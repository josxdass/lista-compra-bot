from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services import db
from utils.session import limpiar_chat, guardar_mensaje
from utils.ui import teclado_principal
from hashlib import md5


async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "add":
        context.user_data["esperando_add"] = True
        msg = await query.message.chat.send_message("✏️ Escribe el producto que quieres añadir.")
    elif data == "delete":
        context.user_data["esperando_borrar"] = True
        msg = await query.message.chat.send_message("🧽 Escribe el producto que quieres borrar.")
    elif data == "view":
        lista = db.obtener_lista()
        texto = "🛒 Tu lista está vacía." if not lista else "🛒 Tu lista:\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(lista))
        msg = await query.message.chat.send_message(texto, reply_markup=teclado_principal())
    elif data == "clear":
        db.vaciar_lista()
        msg = await query.message.chat.send_message("🗑 Lista vaciada correctamente.", reply_markup=teclado_principal())
    elif data == "plato":
        context.user_data["esperando_plato"] = True
        msg = await query.message.chat.send_message("🍽 Escribe el nombre del plato:")
    elif data.startswith("ingrediente_"):
        id_seguro = data.split("_", 1)[1]
        ingrediente = context.user_data.get(f"ing_{id_seguro}", "ingrediente")
        db.insertar_producto(ingrediente)
        await query.answer(f"✅ Añadido: {ingrediente.title()}")
        confirm_msg = await query.message.chat.send_message(f"✅ Añadido a la lista: *{ingrediente.title()}*", parse_mode="Markdown")
        await guardar_mensaje(context, confirm_msg)
        return

    await guardar_mensaje(context, msg)