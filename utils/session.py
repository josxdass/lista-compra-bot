async def limpiar_chat(update, context):
    for msg_id in context.user_data.get("mensajes", []):
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except:
            pass
    context.user_data["mensajes"] = []

async def guardar_mensaje(context, msg):
    if "mensajes" not in context.user_data:
        context.user_data["mensajes"] = []
    context.user_data["mensajes"].append(msg.message_id)