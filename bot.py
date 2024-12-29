from aiogram import Bot
import config
from main import *

bot = Bot(token=config.TELEGRAM_TOKEN)

if __name__ == "__main__":
    dp.start_polling(bot)
