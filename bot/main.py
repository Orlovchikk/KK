import asyncio
import os
from os.path import dirname, join

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, KeyboardButton, Message,
                           ReplyKeyboardMarkup)
from dotenv import load_dotenv
from model import analyze_profile

from database.database import Database

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

dp = Dispatcher()

db = Database()


# Command '/start'
async def command_start_handler(message: Message):
    await db.create_user(message.from_user.id, username=message.from_user.username)
    await message.answer(f"Привет, {message.from_user.first_name}! 👋")
    await message.answer(
        "Я — LinkLens, ваш умный помощник HR, который поможет создать профиль человека на основе его активности в социальных сетях. Используя передовые технологии искусственного интеллекта, я анализирую данные, чтобы предоставить вам полезную информацию.\n"
    )
    await message.answer(
        "Чтобы проверить профиль, просто отправьте ссылку на VK. 🚀",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Купить токены 💸"),
                    KeyboardButton(text="Баланс 💰"),
                ],
                [
                    KeyboardButton(text="Прислать секретный код 🙈"),
                    KeyboardButton(text="Мой секретный код"),
                ],
                [
                    KeyboardButton(text="Анализ 🔎"),
                ],
                [
                    KeyboardButton(text="Привязанные пользователи 👤"),
                ],
            ],
            resize_keyboard=True,
        ),
    )


@dp.message(Command("help"))
async def command_help(message: Message):
    await message.answer(
        "Список всех комманд: /start - перезагрузить бота\n/help - вывести все команды\n/analyze - обработать профиль\n/balance - вывести текущий баланс\nget_code - получить секретный код\n/send_code - отправить код"
    )


class Form(StatesGroup):
    code = State()


# Command '/send_code'
@dp.message(or_f(Command("send_code"), F.text == "Прислать секретный код 🙈"))
async def command_send_code(message: Message, state: FSMContext):
    await state.set_state(Form.code)
    await message.answer("Введите код")


@dp.message(Form.code)
async def process_code(message: Message, state: FSMContext):
    balance = await db.get_balance_by_uniq_code(message.text)
    if balance:
        await db.link_user_to_balance(message.from_user.id, balance.id)
        await message.answer("Ты успешно привязан к аккаунту")
    else:
        await message.answer(
            f"К сожалению, код {message.text} оказался неверным. 😕 Попробуйте снова с помощью команды /send_code или приобретите токены через /tokens. 🛒"
        )
    await state.clear()


# Command '/get_code'
@dp.message(or_f(Command("get_code"), F.text == "Мой секретный код"))
async def command_create_code(message: Message):
    user = message.from_user
    await db.create_uniq_code(user.id)
    uniq_code = await db.get_uniq_code(user.id)
    await message.answer(f"Твой секретный код: {uniq_code}")


# Command '/tokens'
@dp.message(or_f(Command("tokens"), F.text == "Купить токены 💸"))
async def command_tokens_handler(message: Message):
    balance = await db.get_balance(user_id=message.from_user.id)
    if balance.owner_id == str(message.from_user.id):
        await message.answer(
            "Выберите количество токенов, которое вы хотите приобрести.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="10 токенов", callback_data="10_tokens"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="50 токенов", callback_data="50_tokens"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="100 токенов", callback_data="100_tokens"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="1000 токенов", callback_data="1000_tokens"
                        )
                    ],
                ]
            ),
        )
    else:
        await message.answer(
            "Только создатель секретного кода имеет право покупать токены. 🔐"
        )


# Callback for buttons '{}_tokens" in command '/tokens'
async def update_balance_and_notify(callback_query: CallbackQuery, amount: int):
    await db.increase_balance(callback_query.from_user.id, amount)

    await callback_query.message.answer(
        f"Баланс успешно пополнен на {amount} токенов! 🎉"
    )
    await callback_query.message.answer(
        f"Теперь вы можете использовать их, воспользовавшись командой /analyze, или просто отправьте ссылку на профиль VK. 🔍"
    )


async def tokens_callback_handler(callback_query: CallbackQuery):
    token_amounts = {
        "10_tokens": 10,
        "50_tokens": 50,
        "100_tokens": 100,
        "1000_tokens": 1000,
    }

    amount = token_amounts.get(callback_query.data)
    if amount:
        await update_balance_and_notify(callback_query, amount)


# Command '/balance'
@dp.message(or_f(Command("balance"), F.text == "Баланс 💰"))
async def command_balance(message: Message):
    user_balance = await db.get_balance(user_id=message.from_user.id)
    await message.answer(f"Ваш текущий баланс: {user_balance.amount} токенов.")


# vk profile link handler
@dp.message(F.text.regexp(r"https://vk\.com/[A-Za-z0-9]+"))
async def vk_profile_link_hanldler(message: Message):
    text = message.text
    user = message.from_user
    balance = await db.get_balance(user_id=user.id)
    if balance.amount > 0:
        try:
            await message.answer(
                "Обрабатываем профиль, пожалуйста, подождите немного... ⏳"
            )
            response = requests.post("http://parser:8000/parse", json={"link": text})
            response.raise_for_status()
            analyze = await analyze_profile(response.json()["result"])
            if analyze == "Недостаточно данных о пользователе":
                await message.answer(
                    "Мы не смогли найти достаточно информации о профиле. 😕 \nНе волнуйтесь, токен за эту попытку не был списан. Попробуйте отправить другую ссылку. 🔗"
                )
            else:
                await message.answer(analyze)
                await db.decrease_balance(user.id)
                await message.answer(
                    "Готово! С вашего баланса успешно списан 1 токен. ✅"
                )

        except Exception as e:
            print(e)
            await message.answer(
                "Произошла ошибка при обработке ссылки. 😟\nПожалуйста, попробуйте ещё раз."
            )
    else:
        await message.answer(
            "Упс! Кажется, у вас не хватает токенов. 😅 Пожалуйста, пополните баланс через команду /tokens."
        )


class Analyze_Form(StatesGroup):
    link = State()


@dp.message(or_f(Command("analyze"), F.text == "Анализ 🔎"))
async def anaylyze_handler(message: Message, state: FSMContext):
    await state.set_state(Analyze_Form.link)
    await message.answer("Пришлите ссылку на профиль VK. 🔗")


async def process_link(message: Message, state: FSMContext):
    if message.text.startswith("https://vk.com/"):
        await state.clear()
        await vk_profile_link_hanldler(message)
    else:
        await state.set_state(Analyze_Form.link)
        message.answer("Не похоже на ссылку на профиль VK. 😟")
        message.answer("Попробуйте еще раз, либо отправьте команду /cancel")


@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        return

    await state.clear()
    await message.answer("Отправление ссылки отменено")


@dp.message(or_f(Command("users"), F.text == "Привязанные пользователи 👤"))
async def users_handler(message: Message):
    user_id = message.from_user.id

    balance = await db.get_balance(user_id=user_id)
    if not balance:
        await message.answer("Баланс не найден.")
        return

    users = await db.get_users_by_balance(balance_id=balance.id)
    users = [user for user in users if user.id != str(user_id)]

    if not users:
        await message.answer("Нет других пользователей, привязанных к вашему балансу.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{user.id}",
                    callback_data=f"delete_{user.id}",
                )
            ]
            for user in users
        ]
    )

    await message.answer(
        "Вот список пользователей, которые подключены к вашему балансу\nНажмите на пользователя, которого хотите удалить со своего аккаунта",
        reply_markup=keyboard,
    )


async def users_callback_handler(callback_query: CallbackQuery):
    user_id_to_delete = callback_query.data[len("delete_") :]
    user_to_delete = await db.get_user(user_id=user_id_to_delete)
    balance = await db.get_balance(user_id=callback_query.from_user.id)

    if balance.owner_id == str(callback_query.from_user.id):
        try:
            await db.unlink_user_from_balance(user_to_delete)
            await callback_query.message.answer(
            f"Пользователь {user_id_to_delete} удален с вашего баланса."
            )
        except Exception as e:
            print(e)
            await callback_query.message.answer('Произошла ошибка при удалении пользователя')

    else:
        await callback_query.message.answer(
            "Вы не можете удалять пользователей, привязанных к чужому балансу."
        )


def register_handlers(dp: Dispatcher):
    dp.message.register(command_start_handler, CommandStart())
    dp.callback_query.register(
        tokens_callback_handler,
        lambda c: c.data in ["10_tokens", "50_tokens", "100_tokens", "1000_tokens"],
    )
    dp.callback_query.register(
        users_callback_handler, lambda c: c.data.startswith("delete_")
    )


async def main():
    await db.create_metadata()
    register_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
