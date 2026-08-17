import os
import subprocess
import asyncio
import tempfile
import shutil
from pathlib import Path
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from asyncio import Queue 
# === COLA DE PROCESAMIENTO ===
processing_queue = Queue()
is_processing = False


async def process_queue(app):
    """Procesa los videos en cola uno por uno"""
    global is_processing

    while True:
        try:
            # Esperar a que haya un elemento en la cola
            update, context = await processing_queue.get()

            is_processing = True
            print(f"🔄 Procesando solicitud de {update.effective_user.username}")

            # Procesar el video
            await handle_video(update, context)

            # Marcar como completado
            processing_queue.task_done()
            is_processing = False

            # Notificar al siguiente usuario
            if not processing_queue.empty():
                print(f"⏳ {processing_queue.qsize()} solicitudes en espera.")

        except Exception as e:
            print(f"❌ Error en process_queue: {e}")
            is_processing = False
            await asyncio.sleep(1)


# === CONFIGURACIÓN ===
TOKEN = "8885575677:AAHN3u6FRWxtY2sVOe3Rlte1RzNPyz5djyM"  # <--- PON EL TOKEN COMPLETO

# === VERIFICAR FFMPEG ===
# Al inicio del archivo, asigna directamente
FFMPEG_PATH = shutil.which('ffmpeg') or 'ffmpeg'

print("🔍 Verificando FFmpeg...")
if os.path.exists(FFMPEG_PATH):
        print(f"✅ FFmpeg encontrado: {FFMPEG_PATH}")

else:
    print(f"⚠️  FFmpeg NO encontrado en: {FFMPEG_PATH}")
    print("   El bot funcionará pero no podrá comprimir videos")

# === DIRECTORIO TEMPORAL ===
TEMP_DIR = Path(tempfile.gettempdir()) / "video_bot"
TEMP_DIR.mkdir(exist_ok=True)
print(f"📁 Directorio temporal: {TEMP_DIR}")


# === HANDLERS ===
async def start(update: Update, context):
    """Responde al comando /start"""
    await update.message.reply_text(
        "👋 ¡Hola! Soy el compresor de videos.\n\n"
        "📹 Envíame un video y lo comprimiré.\n"
        "⏱️ El proceso puede tomar varios minutos.\n\n"
        "✅ En este momento el bot está funcionando correctamente."
    )
    print(f"✅ /start de @{update.effective_user.username}")


async def handle_video(update: Update, context, status_msg=None):
    """Procesa videos"""
    try:
        user = update.effective_user.username or update.effective_user.id
        print(f"📩 Video recibido de: {user}")
        if status_msg is None:
            status_msg = await update.message.reply_text("📥Procesando tu video...")  # Responder inmediatamente





        # Obtener archivo
        file = await update.message.video.get_file()
        file_id = file.file_id[:8]
        input_path = TEMP_DIR / f"input_{file_id}.mp4"
        output_path = TEMP_DIR / f"output_{file_id}.mp4"

        # Descargar
        msg_descarga = await update.message.reply_text("⏬ Descargando video...")

        try:
            # Intenta descargar el archivo
            await file.download_to_drive(input_path)
            await msg_descarga.delete()
        except Exception as e:
            # Captura CUALQUIER error durante la descarga
            print("Error, intente de nuevo")
            return


        if not input_path.exists():
            await update.message.reply_text("❌ Error: No se pudo descargar el video")
            return

        # Tamaño original
        size_mb = input_path.stat().st_size / (1024 * 1024)
        msg_tamaño = await update.message.reply_text(f"📊 Tamaño original: {size_mb:.2f} MB")

        # EN CASO DE EXCEDER EL TAMAÑO DEL ARCHIVO:
        if size_mb > 20:
            print("El archivo excede el tamaño permitido. Por favor envie un archivo menor de 20 MB.")
            return


        # === AJUSTE AUTOMÁTICO DE CALIDAD Y VELOCIDAD ===
        # Según el tamaño del video, ajustamos los parámetros



       # if size_mb > 80:
            # Videos muy grandes: compresión rápida y agresiva
           # crf = 32
            #preset = "veryfast"
            #mensaje_calidad = "⚡ Modo rápido (prioriza velocidad)"

      #  elif size_mb > 40:
            # Videos medianos: balance entre calidad y velocidad
            #crf = 30
            #preset = "fast"
            #mensaje_calidad = "📊 Modo balanceado"

       # elif size_mb > 20:
            # Videos pequeños: buena calidad
            #crf = 28
            #preset = "fast"
            #mensaje_calidad = "🎯 Modo calidad óptima"

      #  else:
            # Videos muy pequeños: mejor calidad posible
           # crf = 26
            #preset = "medium"
            #mensaje_calidad #= #"✨ Modo alta calidad"



        # Comprimir
        msg_compresion = await update.message.reply_text("🔄 Comprimiendo video (esto puede tomar tiempo)...")

        # Borrar mensajes temporales
        await msg_tamaño.delete()
        await status_msg.delete()




        cmd = [
            FFMPEG_PATH,
            "-i", str(input_path),
            "-vcodec", "libx264",
            "-crf", "28",
            "-preset", "fast",
            "-acodec", "aac",
            "-b:a", "128k",
            "-y",
            str(output_path)
        ]

        # Ejecutar FFmpeg de forma asíncrona
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            returncode = process.returncode
        except asyncio.TimeoutError:
            process.kill()
            await update.message.reply_text("❌ El proceso de compresión ha excedido el tiempo límite (5 minutos)")
            await msg_compresion.delete()
            await msg_tamaño.delete()
            await status_msg.delete()
            input_path.unlink(missing_ok=True)
            return

        if returncode != 0:
            error_msg = stderr.decode()[:200] if stderr else "Error desconocido"
            await update.message.reply_text(f"❌ Error comprimiendo: {error_msg}")
            await msg_compresion.delete()
            await msg_tamaño.delete()
            await status_msg.delete()
            input_path.unlink(missing_ok=True)
            return

        # Verificar resultado
        if not output_path.exists():
            await update.message.reply_text("❌ Error: No se generó el archivo comprimido")
            input_path.unlink(missing_ok=True)
            return

        # Tamaño nuevo
        new_size_mb = output_path.stat().st_size / (1024 * 1024)
        reduccion = (1 - new_size_mb / size_mb) * 100 if size_mb > 0 else 0

        # Enviar
        await update.message.reply_text(
            f"📤 Subiendo video comprimido...\n"
            f"📊 Nuevo tamaño: {new_size_mb:.2f} MB\n"
            f"📉 Reducción: {reduccion:.1f}%"
        )

        with open(output_path, 'rb') as f:
            await update.message.reply_document(
                f,
                filename=f"video_comprimido_{file_id}.mp4",
                caption="✅ ¡Video comprimido exitosamente!"
            )

        # Limpiar
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)

        print(f"✅ Procesamiento completado para {user}")

    except FileNotFoundError as e:
        print(f"❌ Error: FFmpeg no encontrado en {FFMPEG_PATH}")
        await update.message.reply_text(
            f"❌ Error: No se encontró FFmpeg.\n"
            f"Asegúrate de que esté instalado en:\n{FFMPEG_PATH}"
        )
    except Exception as e:
        print(f"❌ Error general: {e}")
        await update.message.reply_text(f"❌ Error procesando el video: {str(e)[:200]}")


# === INICIAR BOT ===
def main():
    print("\n" + "=" * 50)
    print("🚀 INICIANDO BOT COMPRESOR DE VIDEOS")
    print("=" * 50)

    try:
        # Crear aplicación
        app = Application.builder().token(TOKEN).build()

        # Agregar handlers
        app.add_handler(CommandHandler("start", start))

        # Handler que añade a la cola en lugar de procesar directamente
        async def video_handler(update: Update, context):
            """Añade el video a la cola de procesamiento"""
            try:
                user = update.effective_user.username or update.effective_user.id

                # Verificar si ya hay procesamiento
                if is_processing:
                    position = processing_queue.qsize() + 1
                    await update.message.reply_text(
                        f"⏳ ¡El bot está procesando otro video!\n"
                        f"📌 Eres el número {position} en la fila.\n"
                        f"⏱️ El proceso puede tomar varios minutos."
                    )

                # Añadir a la cola
                await processing_queue.put((update, context))
                print(f"📥 {user} añadido a la cola (posición {processing_queue.qsize()})")

            except Exception as e:
                print(f"❌ Error en video_handler: {e}")
                await update.message.reply_text(
                    "❌ Error al añadir el video a la cola. Por favor, intenta de nuevo."
                )

        print("✅ Bot configurado correctamente")
        print(f"📱 Bot: @Jugomundocompressor_bot")
        print("\n📋 INSTRUCCIONES:")
        print("   1. Busca @Jugomundocompressor_bot en Telegram")
        print("   2. Envía /start para verificar")
        print("   3. Envía un video para comprimirlo")
        print("\n⏹️  Presiona Ctrl+C para detener el bot")
        print("=" * 50)
        print()

        # Iniciar polling
        app.run_polling(
            drop_pending_updates=True,
            timeout=300,  # <-- NUEVO: 5 minutos para cada petición
            

        )

    except Exception as e:
        print(f"❌ Error al iniciar el bot: {e}")


if __name__ == "__main__":
    main()