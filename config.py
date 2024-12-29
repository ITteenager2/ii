import os
from datetime import timedelta

class Config:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7705152431:AAH5DSQ8p32VYQoCCMpw3q6PF9rUKBrApFc')
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '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')
        self.CHANNEL_ID = "@yarseoneiro"
        self.ADMIN_IDS = [6306428168, 297933075]
        self.PREMIUM_GENERATIONS = 100000
        self.INVITE_BONUS = 6
        self.COURSE_BONUS = 2
        self.MAX_COURSE_BONUS = 60
        self.YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', 'your_shop_id')
        self.YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', 'your_secret_key')
        self.PREMIUM_PRICE = 300  # Цена в рублях
        self.TRIAL_PERIOD = timedelta(days=3)
        self.TRIAL_PRICE = 1  # Цена за пробный период в рублях
        self.SUPPORT_USERNAME = "evgesha_aga"
        self.FREE_GENERATIONS = 10
        self.OMNI_MINI_GENERATIONS = 10
        self.OMNI_MINI_RESET_PERIOD = timedelta(hours=48)

config = Config()

