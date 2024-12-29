from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import config
from database import db

router = Router()

class AdminStates(StatesGroup):
    assign_premium = State()
    create_course_title = State()
    create_course_content = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к панели администратора.")
        return
    await message.answer(
        "Панель администратора:\n"
        "/assign_premium - Выдать Premium статус пользователю\n"
        "/create_course - Создать новый курс"
    )

@router.message(Command("assign_premium"))
async def cmd_assign_premium(message: Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    await message.answer("Введите ID пользователя, которому нужно выдать Premium статус:")
    await state.set_state(AdminStates.assign_premium)

@router.message(AdminStates.assign_premium)
async def process_assign_premium(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user = db.get_user(user_id)
        user['premium'] = True
        user['free_generations'] += config.PREMIUM_GENERATIONS
        db.update_user(user_id, user)
        await message.answer(f"Premium статус успешно выдан пользователю с ID {user_id}")
    except ValueError:
        await message.answer("Некорректный ID пользователя. Попробуйте еще раз.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
    finally:
        await state.clear()

@router.message(Command("create_course"))
async def cmd_create_course(message: Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    await message.answer("Введите название нового курса:")
    await state.set_state(AdminStates.create_course_title)

@router.message(AdminStates.create_course_title)
async def process_course_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Теперь введите содержание курса:")
    await state.set_state(AdminStates.create_course_content)

@router.message(AdminStates.create_course_content)
async def process_course_content(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get('title')
    content = message.text

    new_lesson = {
        'title': title,
        'content': content
    }

    lesson_number = db.add_lesson(new_lesson)
    await message.answer(f"Курс '{title}' успешно создан и добавлен как урок номер {lesson_number}.")
    await state.clear()

