import logging, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from db.database import SessionLocal
from db.models import GenerationLog

API_URL = "http://app:5000/explain"
logging.basicConfig(level=logging.INFO)
WAITING_FOR_INPUT = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне сложный текст, и я объясню его просто.")
    return WAITING_FOR_INPUT

async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = requests.post(API_URL, json={"text": user_text})
        result = response.json()

        if "result" in result:
            await update.message.reply_text(result["result"])
            log_to_db(
                user_id=str(update.effective_user.id),
                user_name=update.effective_user.username or update.effective_user.full_name,
                question=user_text,
                response=result["result"]
            )
        else:
            await update.message.reply_text(f"Ошибка: {result.get('error')}")
    except Exception as e:
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Окей, отмена.")
    return ConversationHandler.END

def log_to_db(user_id, user_name, question, response):
    session = SessionLocal()
    try:
        log = GenerationLog(user_id=user_id, user_name=user_name, question=question, response=response)
        session.add(log)
        session.commit()
    finally:
        session.close()

def main():
    application = ApplicationBuilder().token("***REMOVED***").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={WAITING_FOR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, explain)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
