from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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