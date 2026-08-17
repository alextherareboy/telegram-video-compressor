import os
import subprocess
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler

# === CONFIGURACIÓN ===
TOKEN = "8885575677:AAHN3u6FRWxtY2sVOe3Rlte1RzNPyz5djyM"  # <--- PON EL TOKEN COMPLETO
import os
import subprocess
import shutil

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
            status_msg = await update.message.reply_text("📥Procesando tu video")  # Responder inmediatamente





        # Obtener archivo
        file = await update.message.video.get_file()
        file_id = file.file_id[:8]
        input_path = TEMP_DIR / f"input_{file_id}.mp4"
        output_path = TEMP_DIR / f"output_{file_id}.mp4"

        # Descargar
        await update.message.reply_text("⏬ Descargando video...")
        await file.download_to_drive(input_path)

        if not input_path.exists():
            await update.message.reply_text("❌ Error: No se pudo descargar el video")
            return

        # Tamaño original
        size_mb = input_path.stat().st_size / (1024 * 1024)
        await update.message.reply_text(f"📊 Tamaño original: {size_mb:.2f} MB")
        # === AJUSTE AUTOMÁTICO DE CALIDAD Y VELOCIDAD ===
        # Según el tamaño del video, ajustamos los parámetros

        if size_mb > 80:
            # Videos muy grandes: compresión rápida y agresiva
            crf = 32
            preset = "veryfast"
            mensaje_calidad = "⚡ Modo rápido (prioriza velocidad)"

        elif size_mb > 40:
            # Videos medianos: balance entre calidad y velocidad
            crf = 30
            preset = "fast"
            mensaje_calidad = "📊 Modo balanceado"

        elif size_mb > 20:
            # Videos pequeños: buena calidad
            crf = 28
            preset = "fast"
            mensaje_calidad = "🎯 Modo calidad óptima"

        else:
            # Videos muy pequeños: mejor calidad posible
            crf = 26
            preset = "medium"
            mensaje_calidad = "✨ Modo alta calidad"



        # Comprimir
        await update.message.reply_text("🔄 Comprimiendo video (esto puede tomar tiempo)...")

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

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            error_msg = result.stderr[:200] if result.stderr else "Error desconocido"
            await update.message.reply_text(f"❌ Error comprimiendo: {error_msg}")
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
        app.add_handler(MessageHandler(filters.VIDEO, handle_video))

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