
import os
import subprocess
import sys
import requests
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"


def debug_ffmpeg():
    """Diagnóstico detallado del entorno"""
    print("=== DIAGNÓSTICO DEL ENTORNO ===")
    print(f"Directorio actual: {os.getcwd()}")
    print(f"Python PATH: {sys.path}")
    print(f"Variables de entorno PATH: {os.environ.get('PATH', '')[:500]}")

    # Intentar ejecutar de diferentes formas
    try:
        # Forma 1: sin ruta
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ffmpeg funciona en PATH")
    except:
        print("❌ ffmpeg NO está en PATH")
if os.path.exists(FFMPEG_PATH):
    print("✅ FFmpeg encontrado en:", FFMPEG_PATH)
else:
    print("❌ No encontré FFmpeg en:", FFMPEG_PATH)
    print("   Verifica la ruta y actualízala")


load_dotenv()

BOT_TOKEN = "8885575677:AAF15cToobVGMJOTO5aKszOi_NxIkASDtNc"
VIDEO_DIR = os.getenv("VIDEO_DIR", "./videos")
BASE_URL = os.getenv("BASE_URL", "http://localhost")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables.")

os.makedirs(VIDEO_DIR, exist_ok=True)

app = Flask(__name__)

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_DIR, filename)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Envíame el link de un video, lo comprimiré para ti!")

async def handle_url(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    user_id = update.message.chat_id

    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("Enlace inválido, por favor envíe un enlace correcto.")
        return

    try:
        response = requests.head(url, allow_redirects=True)
        if response.status_code != 200:
            await update.message.reply_text(f"Este enlace no es accesible! Status code: {response.status_code}")
            return
        content_length = response.headers.get('content-length', 'unknown')
        await update.message.reply_text(f"Este enlace es válido! Tamaño del archivo: {content_length} bytes")
    except Exception as e:
        await update.message.reply_text(f"Error al validar la URL: {e}")
        return

    await update.message.reply_text("Descargando video... Por favor espere.")
    try:
        file_path = os.path.join(VIDEO_DIR, f"{user_id}_video.mp4")
        download_video(url, file_path)

        compressed_path = os.path.join(VIDEO_DIR, f"{user_id}_compressed.mp4")
        compress_video(file_path, compressed_path)

        await update.message.reply_text("Video comprimido con éxito!")

        if os.path.getsize(compressed_path) > 50 * 1024 * 1024:
            download_url = f"{BASE_URL}/videos/{user_id}_compressed.mp4"
            await update.message.reply_text(
                f"El archivo es demasiado grande para Telegram. Puedes descargarlo en: {download_url}"
            )
        else:
            await update.message.reply_document(document=open(compressed_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"Error al procesar el video: {e}")

def download_video(url: str, file_path: str):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def compress_video(input_file: str, output_file: str):
    command = ["ffmpeg", "-y", "-i", input_file, "-vcodec", "libx264", "-crf", "32", output_file]
    subprocess.run(command, check=True)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    from threading import Thread
    flask_thread = Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5000})
    flask_thread.start()

    application.run_polling()

if __name__ == "__main__":
    main()
