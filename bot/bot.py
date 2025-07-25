import logging
import os

import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from tempfile import NamedTemporaryFile
from telegram.constants import ChatAction
from db.database import SessionLocal
from db.models import GenerationLog

API_URL = "http://app:5000/explain"
logging.basicConfig(level=logging.INFO)

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🔑 Премиум", callback_data="premium"),
            InlineKeyboardButton("🎙 Сгенерировать подкаст", callback_data="generate_podcast")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Отправь мне любой сложный текст, и я объясню его просто.",
        reply_markup=reply_markup
    )

# EXPLAIN
async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = requests.post(API_URL, json={"text": user_text})
        result = response.json()

        if "result" in result:
            explanation = result["result"]
            await update.message.reply_text(explanation)

            log_to_db(
                user_id=str(update.effective_user.id),
                user_name=update.effective_user.username or update.effective_user.full_name,
                question=user_text,
                response=explanation
            )
        else:
            await update.message.reply_text(f"Ошибка: {result.get('error')}")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

# CALLBACK (Inline buttons)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "premium":
        await query.edit_message_text("🔐 Подписка на премиум пока недоступна, но скоро появится!")

    elif query.data == "generate_podcast":
        session = SessionLocal()
        try:
            last_log = (
                session.query(GenerationLog)
                .filter(GenerationLog.user_id == str(query.from_user.id))
                .order_by(GenerationLog.id.desc())
                .first()
            )
            if last_log:
                await query.edit_message_text("🎙 Генерирую подкаст...")
                await context.bot.send_chat_action(chat_id=query.message.chat.id, action=ChatAction.UPLOAD_AUDIO)

                # Генерация TTS
                tts = gTTS(text=last_log.response, lang="ru")
                with NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tts.save(tmp.name)
                    audio_path = tmp.name

                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=open(audio_path, "rb"),
                    title="Подкаст: Объяснение текста",
                    performer=last_log.user_name or "ExplainIt"
                )

                os.remove(audio_path)
            else:
                await query.edit_message_text("❗ Нет недавних объяснений для подкаста.")
        finally:
            session.close()

# LOGGING
def log_to_db(user_id, user_name, question, response):
    session = SessionLocal()
    try:
        log = GenerationLog(
            user_id=user_id,
            user_name=user_name,
            question=question,
            response=response
        )
        session.add(log)
        session.commit()
    finally:
        session.close()

# MAIN
def main():
    application = ApplicationBuilder().token("***REMOVED***").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, explain))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()

if __name__ == "__main__":
    main()
