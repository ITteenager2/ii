from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict

def get_start_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="НАЧАТЬ", callback_data="start_using_bot")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{config.CHANNEL_ID[1:]}")],
        [InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_premium_purchase_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🔥 3 дня за 1 рубль", callback_data="trial_subscription")],
        [InlineKeyboardButton(text="✅ Купить подписку", callback_data="full_subscription")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_payment_method_keyboard(subscription_type: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Yookassa", callback_data=f"pay_yookassa_{subscription_type}")],
        [InlineKeyboardButton(text="TG Stars", callback_data=f"pay_tgstars_{subscription_type}")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_premium")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscription_period_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🔥 3 дня за 1 рубль", callback_data="subscribe_trial")],
        [InlineKeyboardButton(text="👍 Недельная ┃199 руб.", callback_data="subscribe_week")],
        [InlineKeyboardButton(text="👍 Месячная ┃499 руб.", callback_data="subscribe_month")],
        [InlineKeyboardButton(text="🔥 Годовая ┃2990 руб.", callback_data="subscribe_year")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_premium")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_check_payment_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="⭐️Проверить оплату", callback_data="check_payment")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_course_selection_keyboard(available_courses: List[Dict[str, str]]) -> InlineKeyboardMarkup:
    keyboard = []
    for course in available_courses:
        keyboard.append([InlineKeyboardButton(
            text=f"Урок {course['number']}: {course['title']}",
            callback_data=f"select_course_{course['number']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_lesson_complete_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Прочитал", callback_data="lesson_complete")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_support_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Связаться с поддержкой", callback_data="contact_support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Выбор нейросети", callback_data="select_neural_network")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="Premium", callback_data="premium")],
        [InlineKeyboardButton(text="Бонусный курс", callback_data="bonus_course")],
        [InlineKeyboardButton(text="Пригласить друзей", callback_data="invite_friends")],
        [InlineKeyboardButton(text="Тех. Поддержка", callback_data="tech_support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_neural_network_menu(user: dict, selected_nn: str) -> InlineKeyboardMarkup:
    has_free_generations = user['free_generations'] > 0
    is_premium = user['premium']
    
    def get_button_text(nn_name: str, locked: bool, selected: bool) -> str:
        prefix = "🔒 " if locked else ""
        suffix = " ✅" if selected else ""
        return f"{prefix}{nn_name}{suffix}"
    
    keyboard = [
        [InlineKeyboardButton(
            text=get_button_text("ChatGPT-4 Omni Mini", False, selected_nn == "gpt4o_mini"),
            callback_data="select_nn_gpt4o_mini"
        )],
        [InlineKeyboardButton(
            text=get_button_text("ChatGPT-4 Omni", not (has_free_generations or is_premium), selected_nn == "gpt4o"),
            callback_data="select_nn_gpt4o"
        )],
        [InlineKeyboardButton(
            text=get_button_text("OpenAI o1", not is_premium, selected_nn == "openai_o1"),
            callback_data="select_nn_openai_o1"
        )],
        [InlineKeyboardButton(
            text=get_button_text("Генерация картинок Stable Diffusion", not (has_free_generations or is_premium), selected_nn == "stable_diffusion"),
            callback_data="select_nn_stable_diffusion"
        )],
        [InlineKeyboardButton(
            text=get_button_text("Генерация картинок Dall-E 3", not (has_free_generations or is_premium), selected_nn == "dalle3"),
            callback_data="select_nn_dalle3"
        )],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
from config import config

