from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from dotenv import load_dotenv
import os

from handlers.commands import start, add, delete, ver_lista
from handlers.buttons import manejar_botones
from handlers.messages import manejar_mensaje

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("borrar", delete))
    app.add_handler(CommandHandler("ver_lista", ver_lista))
    app.add_handler(CallbackQueryHandler(manejar_botones))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("✅ Bot en marcha...")
    app.run_polling()