from telegram import Update
from telegram.ext import ContextTypes
from services import db
from utils.session import limpiar_chat, guardar_mensaje
from utils.ui import teclado_principal


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    msg = await update.effective_chat.send_message(
        "¡Hola! Usa los botones para manejar tu lista de la compra:",
        reply_markup=teclado_principal()
    )
    await guardar_mensaje(context, msg)


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    if not context.args:
        msg = await update.effective_chat.send_message("✏️ Escribe el producto después de /add. Ej: /add pan")
        await guardar_mensaje(context, msg)
        return
    producto = " ".join(context.args).lower()
    db.insertar_producto(producto)
    msg = await update.effective_chat.send_message(f"✅ Producto añadido: {producto}")
    await guardar_mensaje(context, msg)


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    if not context.args:
        msg = await update.effective_chat.send_message("✏️ Escribe el producto después de /borrar. Ej: /borrar pan")
        await guardar_mensaje(context, msg)
        return
    producto = " ".join(context.args).lower()
    eliminado = db.borrar_producto(producto)
    texto = f"🗑️ Producto eliminado: {producto}" if eliminado else f"⚠️ No se encontró: {producto}"
    msg = await update.effective_chat.send_message(texto)
    await guardar_mensaje(context, msg)


async def ver_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    lista = db.obtener_lista()
    texto = "🛒 Tu lista está vacía." if not lista else "🛒 Tu lista de la compra:\n" + "\n".join(
        f"{i+1}. {p}" for i, p in enumerate(lista)
    )
    msg = await update.effective_chat.send_message(texto, reply_markup=teclado_principal())
    await guardar_mensaje(context, msg)