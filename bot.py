import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from model_server import ModelServer

load_dotenv()

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]

# Model settings
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt2')
MAX_NEW_TOKENS = int(os.getenv('MAX_NEW_TOKENS', '128'))
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
TOP_P = float(os.getenv('TOP_P', '0.95'))
DO_SAMPLE = os.getenv('DO_SAMPLE', 'true').lower() in ('1', 'true', 'yes')
DEVICE = os.getenv('DEVICE', 'cpu')

# Initialize model server globally so it loads once
model_server = ModelServer(model_name=MODEL_NAME, device=DEVICE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я локальный AI-бот. Отправь мне сообщение — я сгенерирую ответ.')

async def gen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    prompt = update.message.text
    chat_id = update.effective_chat.id

    logger.info('Received prompt from %s: %s', user.id if user else 'unknown', prompt)

    # Simple typing action
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    try:
        # Call model_server (which internally may be sync or async)
        text = await model_server.generate(
            prompt,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            do_sample=DO_SAMPLE,
        )
    except Exception as e:
        logger.exception('Generation failed')
        await update.message.reply_text('Ошибка при генерации: ' + str(e))
        return

    # Send result — trim if too long
    if len(text) > 4096:
        text = text[:4000] + '\n\n...[truncated]'

    await update.message.reply_text(text)


def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError('TELEGRAM_TOKEN is not set')

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gen_handler))

    logger.info('Starting bot...')
    app.run_polling(stop_signals=None)


if __name__ == '__main__':
    main()
