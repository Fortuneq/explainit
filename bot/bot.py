import logging
import os
import requests
from tempfile import NamedTemporaryFile
from gtts import gTTS

from telegram import (
    Update,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from db.database import SessionLocal
from db.models import GenerationLog, Feedback

API_URL = "http://app:5000/explain"
logging.basicConfig(level=logging.INFO)


# Храним, кто сейчас пишет фидбек
feedback_waiting = set()


# Reply клавиатура снизу
def get_main_reply_keyboard():
    keyboard = [
        ["🔑 Премиум", "🎙 Подкаст"],
        ["✍ Фидбек", "💸 Донат"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь мне любой сложный текст, и я объясню его просто.",
        reply_markup=get_main_reply_keyboard()
    )


# Обработка объяснения
async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = requests.post(API_URL, json={"text": user_text})
        result = response.json()

        if "result" in result:
            explanation = result["result"]
            await update.message.reply_text(
                explanation,
                reply_markup=get_main_reply_keyboard()
            )

            log_to_db(
                user_id=str(update.effective_user.id),
                user_name=update.effective_user.username or update.effective_user.full_name,
                question=user_text,
                response=explanation
            )
        else:
            await update.message.reply_text(
                f"Ошибка: {result.get('error')}",
                reply_markup=get_main_reply_keyboard()
            )
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_reply_keyboard()
        )


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user

    if text == "✍ Фидбек":
        feedback_waiting.add(user.id)
        await update.message.reply_text(
            "📩 Напиши свой фидбек сюда. Я обязательно прочту!"
        )
    elif text == "💸 Донат":
        await update.message.reply_text(
            "Спасибо за желание поддержать!\n\nВот ссылка для донатов:\nhttps://boosty.to/yourpage\n(можно анонимно через карту или ЮMoney)"
        )
    elif text == "🔑 Премиум":
        await update.message.reply_text(
            "🔐 Премиум пока недоступен, но скоро появится!"
        )
    elif text == "🎙 Подкаст":
        await generate_podcast(update, context)
    else:
        await check_feedback_input(update, context)



# Генерация подкаста из последнего объяснения
async def generate_podcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.message.chat_id
    session = SessionLocal()

    try:
        last_log = (
            session.query(GenerationLog)
            .filter(GenerationLog.user_id == str(user.id))
            .order_by(GenerationLog.id.desc())
            .first()
        )

        if last_log:
            await context.bot.send_message(chat_id=chat_id, text="🎙 Генерирую подкаст...")
            tts = gTTS(text=last_log.response, lang="ru")
            with NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tts.save(tmp.name)
                audio_path = tmp.name

            await context.bot.send_audio(
                chat_id=chat_id,
                audio=open(audio_path, "rb"),
                title="Подкаст: Объяснение текста",
                performer=last_log.user_name or "ExplainIt"
            )
            os.remove(audio_path)

            await context.bot.send_message(chat_id=chat_id, text="🎧 Подкаст сгенерирован!")
        else:
            await context.bot.send_message(chat_id=chat_id, text="❗ Нет недавних объяснений для подкаста.")
    finally:
        session.close()


# Сохранение логов в БД
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


async def check_feedback_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if user.id in feedback_waiting:
        save_feedback(str(user.id), user.username or user.full_name, text)
        feedback_waiting.remove(user.id)

        await update.message.reply_text("Спасибо за фидбек! 💌")
    else:
        await explain(update, context)  # если это обычный текст


def save_feedback(user_id: str, user_name: str, text: str):
    session = SessionLocal()
    try:
        feedback = Feedback(
            user_id=user_id,
            user_name=user_name,
            text=text
        )
        session.add(feedback)
        session.commit()
    finally:
        session.close()


# Основной запуск
def main():
    application = ApplicationBuilder().token("***REMOVED***").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, explain))  # Сначала объяснение
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))  # Потом кнопки

    application.run_polling()


if __name__ == "__main__":
    main()
