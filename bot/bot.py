import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from db.database import SessionLocal
from db.models import GenerationLog, Feedback
import requests

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Хранилище для ожидания фидбека от конкретных пользователей
feedback_waiting = set()

API_URL = "http://app:5000/explain"


# Клавиатура
keyboard = ReplyKeyboardMarkup(
    [
        ["🔑 Премиум", "🎙 Подкаст"],
        ["✍ Фидбек", "💸 Донат"]
    ],
    resize_keyboard=True
)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь мне любой сложный текст, и я объясню его просто.",
        reply_markup=keyboard
    )

# Обработка всех текстов
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user

    # 1. Если пользователь в режиме фидбека
    if user.id in feedback_waiting:
        save_feedback(str(user.id), user.username or user.full_name, text)
        feedback_waiting.remove(user.id)
        await update.message.reply_text("Спасибо за фидбек! 💌")
        return

    # 2. Обработка кнопок
    if text == "✍ Фидбек":
        feedback_waiting.add(user.id)
        await update.message.reply_text("📩 Напиши свой фидбек сюда. Я обязательно прочту!")
        return

    elif text == "💸 Донат":
        await update.message.reply_text(
            "Спасибо за желание поддержать!\n\n"
            "💖 Вот ссылка для донатов:\n"
            "https://boosty.to/vlad_vlkv\n\n"
            "Там можно задонатить анонимно с карты или ЮMoney 🙏"
        )
        return

    elif text == "🔑 Премиум":
        await update.message.reply_text("🔐 Премиум пока недоступен, но скоро появится!")
        return

    elif text == "🎙 Подкаст":
        await generate_podcast(update, context)
        return

    # 3. Обычный текст — отправляем на объяснение
    await explain(update, context)

# Отправка текста на explain-сервер
async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = requests.post(API_URL, json={"text": user_text})
        result = response.json()

        if "result" in result:
            explanation = result["result"]

        # Логгируем запрос
        db = SessionLocal()
        log = GenerationLog(
            user_id=str(update.effective_user.id),
            user_name=update.effective_user.username or update.effective_user.full_name,
            question=user_text,
            response=explanation
        )
        db.add(log)
        db.commit()
        db.close()

        await update.message.reply_text(explanation)

    except Exception as e:
        logging.exception("Ошибка при объяснении текста:")
        await update.message.reply_text("Произошла ошибка при попытке объяснить. Попробуй позже.")

# Сохраняем фидбек
def save_feedback(user_id, user_name, text):
    db = SessionLocal()
    feedback = Feedback(
        user_id=user_id,
        user_name=user_name,
        text=text
    )
    db.add(feedback)
    db.commit()
    db.close()

# Заглушка для подкаста
async def generate_podcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 Подкасты пока в разработке. Спасибо за интерес!")

# Запуск приложения
def main():
    application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all))

    application.run_polling()

if __name__ == "__main__":
    main()
