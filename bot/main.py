import asyncio
import os
from os.path import dirname, join

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, or_f
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from dotenv import load_dotenv
import requests

from model import analyze_profile
from database import (
    create_user,
    get_balance,
    get_balance_by_uniq_code,
    increase_balance,
    link_user_to_balance,
    create_uniq_code,
    get_uniq_code,
    decrerase_balance,
)
from utils import validate_url

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

dp = Dispatcher()


# Command '/start'
async def command_start_handler(message: Message):
    create_user(message.from_user.id)
    await message.answer(
        f"""Привет, {message.from_user.first_name}!
LinkLens - это Помощник для HR по созданию профиля человека на основе его поведения в соцсетях, построенный на базе технологии искусственного интеллекта. Для проверки профиля, просто пришли ссылку на VK""",
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
            ],
            resize_keyboard=True,
        ),
    )


@dp.message(Command("help"))
async def command_help(message: Message):
    await message.answer(
        "Список всех комманд: /start - перезагрузить бота\n/help - вывести все команды\n/analyze - обработать профиль\n/balance - вывести текущий баланс\nget_code - получить секретный код\n\
            /send_code - отправить код"
    )


@dp.message(or_f(Command("send_code"), F.text == "Прислать секретный код 🙈"))
async def command_send_code(message: Message):
    if len(message.text.split()) < 2:
        await message.answer("Введите код")
    else:
        command_parts = message.text.split()
        attribute = command_parts[1]
        balance = get_balance_by_uniq_code(attribute)
        if balance:
            link_user_to_balance(message.from_user.id, balance.id)
            await message.answer("Ты успешно привязан к аккаунту")
        else:
            await message.answer(
                f"Похоже, что код {attribute} неверный. Попробуй еще раз через /send_code или купи токены через /tokens"
            )


# Command '/get_code'
@dp.message(or_f(Command("get_code"), F.text == "Мой секретный код"))
async def command_create_code(message: Message):
    user = message.from_user
    create_uniq_code(user.id)
    uniq_code = get_uniq_code(user.id)
    await message.answer(f"Твой секретный код: {uniq_code}")


# Command '/tokens'
@dp.message(or_f(Command("tokens"), F.text == "Купить токены 💸"))
async def command_tokens_handler(message: Message):
    is_owner = get_balance(message.from_user.id).owner_id == str(message.from_user.id)
    if is_owner:
        await message.answer(
            "Выбери количество токенов, которые хочешь купить",
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
        await message.answer("Только создатель секретного кода может покупать токены")


# Callback for buttons '{}_tokens" in command '/tokens'
async def update_balance_and_notify(callback_query: CallbackQuery, amount: int):
    increase_balance(callback_query.from_user.id, amount)

    await callback_query.message.answer(
        f"Баланс пополнен на {amount} токенов, можешь использовать их через /analyze"
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
    user_balance = get_balance(message.from_user.id)
    await message.answer(f"Ваш баланс: {user_balance.amount}")


# vk profile link handler
@dp.message(F.text.regexp("https://vk\.com/[A-Za-z0-9]+"))
async def vk_profile_link_hanldler(message: Message):
    text = message.text
    user = message.from_user
    if get_balance(user.id).amount > 0:
        try:
            if validate_url(text):
                await message.answer("Обрабатываем профиль, подожди немного")
                print(text)
                response = requests.post(
                    "http://parser:8000/parse", json={"link": text}
                )
                response.raise_for_status()
                analyze = analyze_profile(response.json()["result"])
                if analyze == "Недостаточно данных о пользователе":
                    await message.answer(
                        "Мы не нашли достаточно информации о профиле, за такую попытку токен не был списан. Попробуй отправить другую ссылку"
                    )
                else:
                    await message.answer(analyze)
                    decrerase_balance(user.id)
                    await message.answer("Готово! С баланса списан 1 токен")

            else:
                await message.answer("Пришли ссылку на профиль VK")
        except Exception as e:
            print(e)
            await message.answer(
                "Произошла ошибка при обработке ссылки. Попробуйте еще раз."
            )
    else:
        await message.answer(
            "Упс, кажется не хватает токенов. Пополни баланс через /tokens"
        )


def register_handlers(dp: Dispatcher):
    dp.message.register(command_start_handler, CommandStart())
    dp.callback_query.register(
        tokens_callback_handler,
        lambda c: c.data in ["10_tokens", "50_tokens", "100_tokens", "1000_tokens"],
    )


async def main():
    register_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
