import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from yookassa import Configuration, Payment
from config import config
from database import db
from keyboards import inline
import uuid

Configuration.account_id = config.YOOKASSA_SHOP_ID
Configuration.secret_key = config.YOOKASSA_SECRET_KEY

router = Router()

def create_payment(user_id: int, amount: float, description: str, payment_method: str) -> dict:
    if payment_method == "yookassa":
        payment = Payment.create({
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/yarneiro_bot"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": user_id
            }
        }, uuid.uuid4())
        
        return {
            "id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url
        }
    elif payment_method == "tgstars":
        # Implement TG Stars payment logic here
        # This is a placeholder and should be replaced with actual TG Stars API calls
        return {
            "id": f"tgstars_{uuid.uuid4()}",
            "confirmation_url": f"https://t.me/tgstars_bot?start=pay_{user_id}"
        }
    else:
        raise ValueError("Invalid payment method")

def check_payment(payment_id: str, payment_method: str) -> bool:
    if payment_method == "yookassa":
        try:
            payment = Payment.find_one(payment_id)
            return payment.status == "succeeded"
        except Exception as e:
            logging.error(f"Ошибка при проверке платежа Yookassa: {e}")
            return False
    elif payment_method == "tgstars":
        # Implement TG Stars payment check logic here
        # This is a placeholder and should be replaced with actual TG Stars API calls
        return True  # Assuming payment is always successful for this example
    else:
        raise ValueError("Invalid payment method")

@router.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    payment_method, subscription_type = callback.data.split("_")[1:]
    
    if subscription_type == "trial":
        amount = config.TRIAL_PRICE
        description = "Пробная Premium подписка на 3 дня"
    else:
        data = await state.get_data()
        period = data.get('subscription_period')
        amount = get_subscription_price(period)
        description = f"Premium подписка на {get_period_name(period)}"
    
    payment = create_payment(callback.from_user.id, amount, description, payment_method)
    
    await state.update_data(payment_id=payment['id'], payment_method=payment_method)
    await callback.message.edit_text(
        f"Для оплаты {description} перейдите по ссылке ниже:\n"
        f"{payment['confirmation_url']}\n\n"
        "После оплаты нажмите кнопку 'Проверить оплату'",
        reply_markup=inline.get_check_payment_keyboard()
    )

@router.callback_query(F.data == "check_payment")
async def check_premium_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get('payment_id')
    payment_method = data.get('payment_method')
    
    if not payment_id or not payment_method:
        await callback.message.edit_text("Ошибка: информация об оплате не найдена.")
        return

    if check_payment(payment_id, payment_method):
        user = db.get_user(callback.from_user.id)
        user['premium'] = True
        user['subscription_until'] = (datetime.now() + config.TRIAL_PERIOD).isoformat()
        db.update_user(callback.from_user.id, user)
        await callback.message.edit_text(
            "🎉 Поздравляем! Вы успешно активировали Premium!\n"
            "Наслаждайтесь расширенными возможностями бота."
        )
    else:
        await callback.message.edit_text(
            "Оплата еще не прошла или произошла ошибка. Попробуйте проверить позже или свяжитесь с поддержкой.",
            reply_markup=inline.get_support_keyboard()
        )

def get_subscription_price(period: str) -> int:
    prices = {
        "week": 199,
        "month": 499,
        "year": 2990
    }
    return prices.get(period, config.PREMIUM_PRICE)

def get_period_name(period: str) -> str:
    names = {
        "week": "неделю",
        "month": "месяц",
        "year": "год"
    }
    return names.get(period, "неопределенный период")

