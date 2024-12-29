from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🤖 Генерация текста")],
        [KeyboardButton(text="🎨 Генерация изображений")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="⭐️ Premium")],
        [KeyboardButton(text="📚 Бонусный курс"), KeyboardButton(text="👥 Пригласить друзей")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

