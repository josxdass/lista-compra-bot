from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)
from pymongo import MongoClient
from dotenv import load_dotenv
import cohere
import os
from hashlib import md5

# Cargar variables .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Conexiones
client = MongoClient(MONGO_URI)
db = client["listaCompra"]
productos = db["productos"]
co = cohere.Client(COHERE_API_KEY)

# 🧠 Obtener ingredientes desde Cohere
async def obtener_ingredientes_cohere(plato: str):
    prompt = f"¿Cuáles son los ingredientes necesarios para preparar '{plato}'? Devuelve solo una lista con los nombres de los ingredientes separados por comas."
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=100,
        temperature=0.4
    )
    texto = response.generations[0].text.strip()
    ingredientes = [i.strip().lower() for i in texto.split(",") if i.strip()]
    return ingredientes

# 🧹 Borrar mensajes anteriores
async def limpiar_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for msg_id in context.user_data.get("mensajes", []):
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except:
            pass
    context.user_data["mensajes"] = []

# 📝 Guardar mensaje
async def guardar_mensaje(context: ContextTypes.DEFAULT_TYPE, msg):
    if "mensajes" not in context.user_data:
        context.user_data["mensajes"] = []
    context.user_data["mensajes"].append(msg.message_id)

# 🔘 Teclado principal
def teclado_principal():
    botones = [
        [
            InlineKeyboardButton("➕ Añadir", callback_data="add"),
            InlineKeyboardButton("❌ Borrar", callback_data="delete")
        ],
        [
            InlineKeyboardButton("👀 Ver lista", callback_data="view"),
            InlineKeyboardButton("🗑 Vaciar lista", callback_data="clear")
        ],
        [
            InlineKeyboardButton("🍽 Nombre del plato", callback_data="plato")
        ]
    ]
    return InlineKeyboardMarkup(botones)

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

# /ver_lista
async def ver_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    lista = list(productos.find())
    if not lista:
        texto = "🛒 Tu lista está vacía."
    else:
        texto = "🛒 Tu lista de la compra:\n" + "\n".join(f"{i+1}. {p['nombre']}" for i, p in enumerate(lista))
    msg = await update.effective_chat.send_message(texto, reply_markup=teclado_principal())
    await guardar_mensaje(context, msg)

# 👆 Botones
async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Solo limpiar si no es selección de ingrediente
    if not data.startswith("ingrediente_") and data != "terminar_ingredientes":
        await limpiar_chat(update, context)

    if data == "add":
        context.user_data["modo"] = "add"
        msg = await query.message.chat.send_message("📝 Escribe el producto que quieres *añadir* a la lista:", parse_mode="Markdown")
        await guardar_mensaje(context, msg)

    elif data == "delete":
        context.user_data["modo"] = "delete"
        msg = await query.message.chat.send_message("🗑️ Escribe el producto que quieres *eliminar* de la lista:", parse_mode="Markdown")
        await guardar_mensaje(context, msg)

    elif data == "view":
        lista = list(productos.find())
        if not lista:
            texto = "🛒 Tu lista está vacía."
        else:
            texto = "🛒 Tu lista de la compra:\n" + "\n".join(f"{i+1}. {p['nombre']}" for i, p in enumerate(lista))
        msg = await query.message.chat.send_message(texto, reply_markup=teclado_principal())
        await guardar_mensaje(context, msg)

    elif data == "clear":
        productos.delete_many({})
        msg = await query.message.chat.send_message("🗑 Lista vaciada correctamente.", reply_markup=teclado_principal())
        await guardar_mensaje(context, msg)

    elif data == "plato":
        context.user_data["esperando_plato"] = True
        msg = await query.message.chat.send_message("🍽 Escribe el nombre del plato del que quieres ver los ingredientes.")
        await guardar_mensaje(context, msg)

    elif data.startswith("ingrediente_"):
        id_seguro = data.split("_", 1)[1]
        ingrediente = context.user_data.get(f"ing_{id_seguro}", "ingrediente")
        productos.insert_one({"nombre": ingrediente})
        await query.answer(f"✅ Añadido: {ingrediente.title()}", show_alert=False)
        confirm_msg = await query.message.chat.send_message(f"✅ Añadido a la lista: *{ingrediente.title()}*", parse_mode="Markdown")
        await guardar_mensaje(context, confirm_msg)

    elif data == "terminar_ingredientes":
        await limpiar_chat(update, context)
        msg = await query.message.chat.send_message("✅ Ingredientes seleccionados. ¿Qué más quieres hacer?", reply_markup=teclado_principal())
        await guardar_mensaje(context, msg)

# ✍️ Texto libre
async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await limpiar_chat(update, context)
    texto_usuario = update.message.text.strip().lower()

    # 👉 Añadir producto desde modo botones
    if context.user_data.get("modo") == "add":
        context.user_data["modo"] = None
        productos.insert_one({"nombre": texto_usuario})
        msg = await update.effective_chat.send_message(f"✅ Producto añadido: {texto_usuario}", reply_markup=teclado_principal())
        await guardar_mensaje(context, msg)
        return

    # 👉 Borrar producto desde modo botones
    if context.user_data.get("modo") == "delete":
        context.user_data["modo"] = None
        resultado = productos.delete_one({"nombre": texto_usuario})
        if resultado.deleted_count > 0:
            msg = await update.effective_chat.send_message(f"🗑️ Producto eliminado: {texto_usuario}", reply_markup=teclado_principal())
        else:
            msg = await update.effective_chat.send_message(f"⚠️ No se encontró '{texto_usuario}' en la lista.", reply_markup=teclado_principal())
        await guardar_mensaje(context, msg)
        return

    # 👉 Ingredientes de plato
    if context.user_data.get("esperando_plato"):
        context.user_data["esperando_plato"] = False
        ingredientes = await obtener_ingredientes_cohere(texto_usuario)

        if not ingredientes:
            msg = await update.effective_chat.send_message("❌ No se encontraron ingredientes para ese plato.")
            await guardar_mensaje(context, msg)
            return

        botones = []
        for ing in ingredientes:
            ing_limpio = ing.strip().lower()
            id_seguro = md5(ing_limpio.encode()).hexdigest()[:16]
            context.user_data[f"ing_{id_seguro}"] = ing_limpio
            botones.append([InlineKeyboardButton(f"➕ {ing_limpio.title()}", callback_data=f"ingrediente_{id_seguro}")])

        botones.append([InlineKeyboardButton("✅ Terminar selección", callback_data="terminar_ingredientes")])
        markup = InlineKeyboardMarkup(botones)
        texto = f"🍽 Ingredientes para *{texto_usuario}*:\nSelecciona los que quieres añadir:"
        msg = await update.effective_chat.send_message(texto, reply_markup=markup, parse_mode="Markdown")
        await guardar_mensaje(context, msg)
        return

    # 🧭 Si no encaja en nada
    msg = await update.effective_chat.send_message("❓ No te he entendido. Usa los comandos o botones.")
    await guardar_mensaje(context, msg)

# 🔁 Main
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