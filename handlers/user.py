from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Voice
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import inline
from services.content_generation import ContentGeneration
from database import db
from config import config
import logging
import io
import os
import uuid
from datetime import datetime, timedelta
from services.payment import create_payment, check_payment
from aiogram.types import FSInputFile
import speech_recognition as sr
from pydub import AudioSegment

router = Router()

class UserStates(StatesGroup):
    main_menu = State()
    chatgpt = State()
    gpt4o = State()
    imagine = State()
    premium_purchase = State()
    course = State()
    waiting_payment = State()
    support = State()
    select_neural_network = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split(' ', maxsplit=1)[1] if len(message.text.split()) > 1 else None
    
    user = db.get_user(user_id)
    
    if args and not user['referred_by']:
        try:
            referrer_id = int(args)
            if user_id != referrer_id:
                referrer = db.get_user(referrer_id)
                if referrer and user_id not in referrer['invited_users']:
                    referrer['invited_users'].append(user_id)
                    referrer['free_generations'] += config.INVITE_BONUS
                    db.update_user(referrer_id, referrer)
                    user['referred_by'] = referrer_id
                    db.update_user(user_id, user)
                    await message.bot.send_message(
                        referrer_id,
                        f"Новый пользователь перешел по вашей реферальной ссылке! Вы получили {config.INVITE_BONUS} бесплатных генераций."
                    )
        except ValueError:
            logging.warning(f"Invalid referral ID: {args}")

    await show_main_menu(message, state)

async def show_main_menu(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    omni_mini_reset_time = datetime.fromisoformat(user['omni_mini_reset_time']) if user['omni_mini_reset_time'] else None
    
    if omni_mini_reset_time and datetime.now() > omni_mini_reset_time:
        db.reset_omni_mini_generations(message.from_user.id)
        user = db.get_user(message.from_user.id)
        omni_mini_reset_time = datetime.fromisoformat(user['omni_mini_reset_time']) if user['omni_mini_reset_time'] else None

    reset_time_str = (omni_mini_reset_time + timedelta(hours=48)).strftime('%d.%m.%Y в %H:%M') if omni_mini_reset_time else "Не установлено"

    await message.answer(
        "Я — твой главный помощник в жизни, который ответит на любой вопрос, "
        "сгенерирует уникальный текст, напишет текст для поста в соцсети, "
        "поддержит тебя, сделает за тебя задание, выполнит работу или нарисует картину.\n\n"
        f"Вам доступно бесплатно {user['free_generations']}/10 запросов на генерацию текста "
        f"(ChatGPT 4 Omni) и картинок (Dall-E 3 и Stable Diffusion)\n\n"
        f"Также вам доступно {user['omni_mini_generations']}/10 запросов на генерацию текста через "
        f"ChatGPT 4 mini каждые 48 часов. Обновление лимитов: "
        f"{reset_time_str} (мск)\n\n"
        "⤷ Отправь мне голосовое сообщение — я тебе отвечу на твой вопрос "
        "⤷ Пришли мне фотографию с заданием — я тебе его решу "
        "⤷ Напишу за тебя пост для блога, соцсетей, сформирую заявление или напишу полноценное сочинение "
        "⤷ Решу любое задание или выполню работу за тебя "
        "⤷ Нарисую для тебя картину с помощью Stable Diffusion или DALL•E 3 "
        "⤷ Побуду твоим личным психологом или лучшим другом\n\n"
        "⭐️ Текущая нейросеть: GPT-4 Omni\n\n"
        "👇🏻 Для старта работы просто напишите вопрос в чат!",
        reply_markup=inline.get_main_menu()
    )
    await state.set_state(UserStates.main_menu)

@router.callback_query(F.data == "select_neural_network")
async def process_select_neural_network(callback: CallbackQuery, state: FSMContext):
    user = db.get_user(callback.from_user.id)
    user_data = await state.get_data()
    selected_nn = user_data.get('selected_neural_network', 'gpt4o_mini')
    await callback.message.edit_text(
        "Выберите нейросеть для генерации текста или изображений.\n"
        f"Вам доступно бесплатно {user['free_generations']}/10 запросов на генерацию текста "
        f"(ChatGPT 4 Omni) и картинок (Dall-E 3 и Stable Diffusion).\n"
        f"Также вам доступно {user['omni_mini_generations']}/10 запросов на генерацию текста через "
        f"ChatGPT 4 mini каждые 48 часов.",
        reply_markup=inline.get_neural_network_menu(user, selected_nn)
    )
    await state.set_state(UserStates.select_neural_network)

@router.callback_query(F.data.startswith("select_nn_"))
async def process_neural_network_selection(callback: CallbackQuery, state: FSMContext):
    selected_nn = callback.data.split("_")[2]
    user = db.get_user(callback.from_user.id)
    
    if selected_nn in ["gpt4o", "openai_o1"] and not user['premium']:
        await show_premium_offer(callback.message)
        return
    
    if selected_nn == "stable_diffusion":
        selected_nn = "dalle3"
        await callback.answer("Выбран Stable Diffusion, но будет использован DALL-E 3")
    else:
        await callback.answer(f"Выбрана нейросеть: {selected_nn}")
    
    await state.update_data(selected_neural_network=selected_nn)
    await process_select_neural_network(callback, state)

@router.message(F.text)
async def handle_message(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    data = await state.get_data()
    selected_nn = data.get('selected_neural_network', 'gpt4o_mini')
    
    if not user['premium']:
        if selected_nn == 'gpt4o_mini':
            if user['omni_mini_generations'] <= 0:
                await message.answer("У вас закончились бесплатные генерации для GPT-4 Omni Mini. Дождитесь обновления лимита или приобретите Premium подписку.")
                return
            user['omni_mini_generations'] -= 1
        else:
            if user['free_generations'] <= 0:
                await message.answer("У вас закончились бесплатные генерации. Приобретите Premium подписку для продолжения использования.")
                return
            user['free_generations'] -= 1
        
        db.update_user(message.from_user.id, user)
    
    response = await ContentGeneration.generate_text(message.text, model=selected_nn)
    await message.answer(response)

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    await cmd_profile(callback.message)

@router.callback_query(F.data == "premium")
async def show_premium(callback: CallbackQuery, state: FSMContext):
    await cmd_premium(callback.message, state)

@router.callback_query(F.data == "bonus_course")
async def show_bonus_course(callback: CallbackQuery, state: FSMContext):
    await cmd_bonus(callback.message, state)

@router.callback_query(F.data == "invite_friends")
async def show_invite_friends(callback: CallbackQuery):
    await cmd_invite(callback.message)

@router.callback_query(F.data == "tech_support")
async def show_tech_support(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Опишите вашу проблему или задайте вопрос. Мы постараемся ответить как можно скорее.")
    await state.set_state(UserStates.support)

@router.message(UserStates.support)
async def handle_support_message(message: Message, state: FSMContext):
    support_message = f"Новое сообщение в поддержку от пользователя {message.from_user.id}:\n\n{message.text}"
    
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, support_message)
        except Exception as e:
            logging.error(f"Failed to send support message to admin {admin_id}: {e}")
    
    await message.answer("Ваше сообщение отправлено в службу поддержки. Мы ответим вам как можно скорее.")
    await show_main_menu(message, state)

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = db.get_user(message.from_user.id)
    profile_text = (
        f"👤 Ваш профиль:\n"
        f"🔢 Оставшиеся бесплатные генерации: {user['free_generations']}\n"
        f"🤖 Оставшиеся генерации GPT-4 Omni Mini: {user['omni_mini_generations']}\n"
        f"🌟 Premium: {'Да' if user['premium'] else 'Нет'}\n"
        f"👥 Приглашено пользователей: {len(user['invited_users'])}\n"
        f"📚 Пройдено уроков: {len(user['completed_lessons'])}"
    )
    await message.answer(profile_text)

@router.message(Command("premium"))
async def cmd_premium(message: Message, state: FSMContext):
    await show_premium_offer(message)

async def show_premium_offer(message: Message):
    await message.answer(
        "Данная нейросеть доступна только пользователям с подпиской.\n\n"
        "В Америке она стоит около 2500 рублей, но вы можете ее попробовать по цене чашечки кофе! "
        "С подпиской я стану эффективнее в 10 (!) раз — малая часть того, что вы получите, если оформите ее:\n"
        "⭐️ Безлимитное количество запросов (такого нет ни у кого)\n"
        "⭐️ Доступ ко всем нейронкам для генерации текстов, поиска ответов на любые запросы, "
        "генерации контента, различных планов и презентаций — OpenAI o1, GPT-4 Omni\n"
        "⭐️ Доступ ко всем нейронкам для генерации картинок - Stable Diffusion и DALL•E 3\n"
        "⭐️ И многое другое…\n\n"
        "Кстати, наша пробная подписка стоит всего 1 рубль.\n\n"
        "P.S. — с подпиской я реально гораздо круче 😎",
        reply_markup=inline.get_premium_purchase_keyboard()
    )

@router.message(Command("bonus"))
async def cmd_bonus(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    completed_lessons = set(user['completed_lessons'])
    
    courses = db.get_all_lessons()
    available_courses = [
        {"number": lesson_num, "title": lesson['title']}
        for lesson_num, lesson in courses.items()
        if int(lesson_num) not in completed_lessons
    ]
    
    if not available_courses:
        await message.answer("Вы уже прошли все доступные уроки. Новые уроки пока не доступны.")
        return
    
    await message.answer(
        "Выберите урок для прохождения:",
        reply_markup=inline.get_course_selection_keyboard(available_courses)
    )

@router.message(Command("invite"))
async def cmd_invite(message: Message):
    user_id = message.from_user.id
    bot_info = await message.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={user_id}"
    await message.answer(
        f"👥 Пригласите друга и получите {config.INVITE_BONUS} генераций!\n\n"
        f"Ваша реферальная ссылка: {invite_link}\n\n"
        "Когда ваш друг активирует бота по этой ссылке, вы получите бонус."
    )

@router.message(F.voice)
async def handle_voice(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user['premium']:
        if user['free_generations'] <= 0:
            await message.answer("У вас недостаточно генераций для обработки голосовых сообщений. Купите Premium или заработайте бонусы.")
            return
        user['free_generations'] -= 1
        db.update_user(message.from_user.id, user)
    
    file = await message.bot.get_file(message.voice.file_id)
    voice_ogg = io.BytesIO()
    await message.bot.download_file(file.file_path, voice_ogg)
    
    voice_wav = io.BytesIO()
    voice_ogg.seek(0)
    audio = AudioSegment.from_ogg(voice_ogg)
    audio.export(voice_wav, format="wav")
    voice_wav.seek(0)
    
    recognizer = sr.Recognizer()
    with sr.AudioFile(voice_wav) as source:
        audio = recognizer.record(source)
    
    try:
        text_from_voice = recognizer.recognize_google(audio, language="ru-RU")
    except sr.UnknownValueError:
        await message.answer("Извините, не удалось распознать речь. Попробуйте еще раз.")
        return
    except sr.RequestError:
        await message.answer("Извините, произошла ошибка при обработке голосового сообщения. Попробуйте позже.")
        return
    
    data = await state.get_data()
    selected_nn = data.get('selected_neural_network', 'gpt4o_mini')
    response = await ContentGeneration.generate_text(text_from_voice, model=selected_nn)
    await message.answer(response)

@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user['premium']:
        if user['free_generations'] <= 0:
            await message.answer("У вас недостаточно генераций для обработки изображений. Купите Premium или заработайте бонусы.")
            return
        user['free_generations'] -= 1
        db.update_user(message.from_user.id, user)
    
    file = await message.bot.get_file(message.photo[-1].file_id)
    photo_bytes = io.BytesIO()
    await message.bot.download_file(file.file_path, photo_bytes)
    
    # Здесь должна быть логика обработки изображения и извлечения текста
    # Например, используя библиотеку pytesseract
    
    text_from_image = "Текст с изображения"  # Заглушка
    
    response = await ContentGeneration.generate_text(f"Решите задачу с изображения: {text_from_image}", model="gpt-4o")
    await message.answer(response)

@router.message(Command("support"))
async def cmd_support(message: Message, state: FSMContext):
    await message.answer("Опишите вашу проблему или задайте вопрос. Мы постараемся ответить как можно скорее.")
    await state.set_state(UserStates.support)

@router.message(UserStates.support)
async def handle_support_message(message: Message, state: FSMContext):
    support_message = f"Новое сообщение в поддержку от пользователя {message.from_user.id}:\n\n{message.text}"
    
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, support_message)
        except Exception as e:
            logging.error(f"Failed to send support message to admin {admin_id}: {e}")
    
    await message.answer("Ваше сообщение отправлено в службу поддержки. Мы ответим вам как можно скорее.")
    await show_main_menu(message, state)

async def check_subscription(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(config.CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        return False

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

