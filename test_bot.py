from telegram import Update
from telegram.ext import Application, CommandHandler

# === CAMBIA SOLO ESTO ===
TOKEN = "8885575677:AAF15cToobVGMJOTO5aKszOi_NxIkASDtNc"  # Pega tu token aquí


async def start(update: Update, context):
    await update.message.reply_text("✅ ¡El bot funciona!")


def main():
    print("🔄 Iniciando bot de prueba...")
    print(f"📱 Token: {TOKEN[:10]}...{TOKEN[-5:]}")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("✅ Bot listo. Envía /start en Telegram")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()