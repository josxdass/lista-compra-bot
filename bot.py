from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
uri = os.getenv("MONGO_URI")

client = MongoClient(uri)
db = client["listaCompra"]
productos = db["productos"]

# Teclado inline
def teclado_principal():
    botones = [
        [
            InlineKeyboardButton("➕ Añadir", callback_data="add"),
            InlineKeyboardButton("❌ Borrar", callback_data="delete"),
        ],
        [
            InlineKeyboardButton("👀 Ver lista", callback_data="view"),
            InlineKeyboardButton("🗑 Vaciar lista", callback_data="clear"),
        ],
    ]
    return InlineKeyboardMarkup(botones)

# 🧹 Borrar mensajes anteriores
async def limpiar_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensajes = context.user_data.get("mensajes", [])

    for msg_id in mensajes:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except:
            pass  # Puede fallar si ya fue borrado

    # Limpiamos el registro
    context.user_data["mensajes"] = []

# 📥 Guardar nuevo mensaje para futura limpieza
async def guardar_mensaje(context: ContextTypes.DEFAULT_TYPE, msg):
    if "mensajes" not in context.user_data:
        context.user_data["mensajes"] = []
    context.user_data["mensajes"].append(msg.message_id)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    msg = await update.effective_chat.send_message(
        "¡Hola! Usa los botones para manejar tu lista de la compra:",
        reply_markup=teclado_principal()
    )
    await guardar_mensaje(context, msg)

# /add
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)

    if not context.args:
        msg = await update.effective_chat.send_message("❌ Tienes que escribir qué producto añadir. Ej: /add pan")
        await guardar_mensaje(context, msg)
        return

    producto = " ".join(context.args).lower()
    productos.insert_one({"nombre": producto})
    msg = await update.effective_chat.send_message(f"✅ Producto añadido: {producto}")
    await guardar_mensaje(context, msg)

# /borrar
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)

    if not context.args:
        msg = await update.effective_chat.send_message("❌ Tienes que indicar el producto a borrar. Ej: /borrar pan")
        await guardar_mensaje(context, msg)
        return

    producto = " ".join(context.args).lower()
    resultado = productos.delete_one({"nombre": producto})
    if resultado.deleted_count > 0:
        msg = await update.effective_chat.send_message(f"🗑️ Producto eliminado: {producto}")
    else:
        msg = await update.effective_chat.send_message(f"⚠️ No se encontró '{producto}' en la lista.")
    await guardar_mensaje(context, msg)

# /ver
async def ver_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)

    lista = list(productos.find())
    if not lista:
        texto = "🛒 Tu lista está vacía."
    else:
        texto = "🛒 Tu lista de la compra:\n"
        for i, item in enumerate(lista, start=1):
            texto += f"{i}. {item['nombre']}\n"

    msg = await update.effective_chat.send_message(texto, reply_markup=teclado_principal())
    await guardar_mensaje(context, msg)

# Botones inline
async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await limpiar_chat(update, context)

    data = query.data

    if data == "add":
        msg = await query.message.chat.send_message("✏️ Usa /add seguido del producto. Ej: /add pan")
    elif data == "delete":
        msg = await query.message.chat.send_message("🧽 Usa /borrar seguido del producto. Ej: /borrar pan")
    elif data == "view":
        lista = list(productos.find())
        if not lista:
            texto = "🛒 Tu lista está vacía."
        else:
            texto = "🛒 Tu lista de la compra:\n"
            for i, item in enumerate(lista, start=1):
                texto += f"{i}. {item['nombre']}\n"
        msg = await query.message.chat.send_message(texto, reply_markup=teclado_principal())
    elif data == "clear":
        productos.delete_many({})
        msg = await query.message.chat.send_message("🗑 Lista vaciada correctamente.", reply_markup=teclado_principal())

    await guardar_mensaje(context, msg)

# Mensajes no reconocidos
async def mensaje_no_reconocido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    msg = await update.effective_chat.send_message("❓ No te he entendido. Usa los comandos o botones.")
    await guardar_mensaje(context, msg)

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("borrar", delete))
    app.add_handler(CommandHandler("ver_lista", ver_lista))
    app.add_handler(CallbackQueryHandler(manejar_botones))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_no_reconocido))

    print("✅ Bot en marcha...")
    app.run_polling()