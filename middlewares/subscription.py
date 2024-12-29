from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from handlers.user import check_subscription
from keyboards.inline import get_subscription_keyboard

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        if isinstance(event, CallbackQuery):
            if event.data == "check_subscription":
                return await handler(event, data)
        
        if not await check_subscription(event.bot, user_id):
            if isinstance(event, Message):
                await event.answer(
                    "Для использования бота необходимо подписаться на канал. "
                    "Пожалуйста, подпишитесь и нажмите /start снова.", reply_markup=get_subscription_keyboard()
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "Для использования бота необходимо подписаться на канал. "
                    "Пожалуйста, подпишитесь и попробуйте снова.",
                    show_alert=True
                )
            return
        
        return await handler(event, data)

