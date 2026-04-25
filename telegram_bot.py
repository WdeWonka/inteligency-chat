import httpx
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters, ConversationHandler

TOKEN = "8641975440:AAF4mZeawkSEhFg-txNsUV9xQTekuUFrn_c"
BACKEND_URL = "http://localhost:8000/api/v1/chat/messages"

ROLES = {
    "1": "profesor",
    "2": "programador", 
    "3": "psicologo",
    "4": "negocios"
}

ELIGIENDO_ROL, CHATEANDO = range(2)

user_sessions = {}

async def start(update: Update, context: CallbackContext):
    keyboard = [["1. Profesor", "2. Programador"], ["3. Psicólogo", "4. Negocios"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Bienvenido al Chat Inteligente con Roles\n\nElige tu rol:",
        reply_markup=reply_markup
    )
    return ELIGIENDO_ROL

async def elegir_rol(update: Update, context: CallbackContext):
    texto = update.message.text
    rol = None
    if "1" in texto: rol = "profesor"
    elif "2" in texto: rol = "programador"
    elif "3" in texto: rol = "psicologo"
    elif "4" in texto: rol = "negocios"
    
    if not rol:
        await update.message.reply_text("Por favor elige una opción del menú.")
        return ELIGIENDO_ROL
    
    user_sessions[update.effective_user.id] = {"rol": rol, "conversation_id": None}
    await update.message.reply_text(f"✅ Rol seleccionado: *{rol}*\n\nAhora escribe tu mensaje:", parse_mode="Markdown")
    return CHATEANDO

async def chatear(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    mensaje = update.message.text

    if mensaje in ["1. Profesor", "2. Programador", "3. Psicólogo", "4. Negocios"]:
        return await elegir_rol(update, context)

    session = user_sessions.get(user_id, {"rol": "profesor", "conversation_id": None})

    await update.message.reply_text("⏳ Pensando...")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(BACKEND_URL, json={
                "role": session["rol"],
                "message": mensaje,
                "conversation_id": session["conversation_id"]
            })
            data = response.json()
            conversation_id = data.get("conversation_id")
            user_sessions[user_id]["conversation_id"] = conversation_id
            respuesta = data["assistant_message"]["content"]
            await update.message.reply_text(f"🤖 {respuesta}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

    return CHATEANDO

async def cambiar_rol(update: Update, context: CallbackContext):
    return await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ELIGIENDO_ROL: [MessageHandler(filters.TEXT & ~filters.COMMAND, elegir_rol)],
            CHATEANDO: [MessageHandler(filters.TEXT & ~filters.COMMAND, chatear)],
        },
        fallbacks=[CommandHandler("rol", cambiar_rol)],
    )
    app.add_handler(conv_handler)
    print("🤖 Bot de Telegram corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
