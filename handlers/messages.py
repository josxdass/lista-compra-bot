from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.cohere_ai import obtener_ingredientes_cohere
from services import db
from utils.session import limpiar_chat, guardar_mensaje
from hashlib import md5


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    texto = update.message.text.strip()

    if context.user_data.get("esperando_add"):
        context.user_data["esperando_add"] = False
        db.insertar_producto(texto.lower())
        msg = await update.message.reply_text(f"✅ Añadido: {texto.lower()}")
        await guardar_mensaje(context, msg)
        return

    if context.user_data.get("esperando_borrar"):
        context.user_data["esperando_borrar"] = False
        eliminado = db.borrar_producto(texto.lower())
        respuesta = f"🗑️ Borrado: {texto}" if eliminado else f"⚠️ No encontrado: {texto}"
        msg = await update.message.reply_text(respuesta)
        await guardar_mensaje(context, msg)
        return

    if context.user_data.get("esperando_plato"):
        context.user_data["esperando_plato"] = False
        ingredientes = await obtener_ingredientes_cohere(texto)

        if not ingredientes:
            msg = await update.message.reply_text("❌ No se encontraron ingredientes.")
            await guardar_mensaje(context, msg)
            return

        botones = []
        for ing in ingredientes:
            id_seguro = md5(ing.encode()).hexdigest()[:16]
            context.user_data[f"ing_{id_seguro}"] = ing
            botones.append([InlineKeyboardButton(f"➕ {ing.title()}", callback_data=f"ingrediente_{id_seguro}")])

        # Añadir botón de finalizar selección
        botones.append([InlineKeyboardButton("✅ Terminar selección", callback_data="view")])

        markup = InlineKeyboardMarkup(botones)
        msg = await update.effective_chat.send_message(
            f"🍽 Ingredientes para *{texto}*:\nSelecciona los que quieras añadir:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        await guardar_mensaje(context, msg)
        return

    msg = await update.message.reply_text("❓ No te he entendido. Usa los botones del menú.")
    await guardar_mensaje(context, msg)