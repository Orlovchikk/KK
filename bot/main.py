import asyncio
import os
from os.path import dirname, join

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

from ai_model import Model
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
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    create_user(message.from_user.id)
    await message.answer(
        f"""Привет, {message.from_user.full_name}!
LinkLens - это Помощник для HR по созданию профиля человека на основе его поведения в соцсетях, построенный на базе технологии искусственного интеллекта.
Нажми на "Прислать секретный код" или на "Подробнее", чтобы узнать о том, как получить его.""",
    )


@dp.message(Command("help"))
async def command_help(message: Message):
    await message.answer(
        "Список всех комманд: /start - перезагрузить бота\n/help - вывести все команды\n/analyze - обработать профиль"
    )


@dp.message(Command("more_info"))
async def process_start(message: Message):
    await message.answer(
        "Чтобы получить токены, напиши своему руководителю для получения секретного кода, либо купи токены через /tokens. ",
    )


@dp.message(Command("send_code"))
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
@dp.message(Command("get_code"))
async def command_create_code(message: Message):
    user = message.from_user
    create_uniq_code(user.id)
    uniq_code = get_uniq_code(user.id)
    await message.answer(f"Секретный код: {uniq_code}")


# Command '/tokens'
@dp.message(Command("tokens"))
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
@dp.message(Command("balance"))
async def command_balance(message: Message):
    user_balance = get_balance(message.from_user.id)
    await message.answer(f"Ваш баланс: {user_balance.amount}")


# Command '/analyze'
@dp.message(Command("analyze"))
async def command_analyze_handler(message: Message):
    if len(message.text.split()) < 2:
        await message.answer("Пришли ссылку")
    else:
        command_parts = message.text.split()
        attribute = command_parts[1]
        user = message.from_user
        if get_balance(user.id).amount > 0:
            try:
                if validate_url(attribute):
                    await message.answer("Обрабатываем профиль, подожди немного")
                    analyze = Model.analyze_profile(attribute)
                    await message.answer("Готово! С баланса списан 1 токен")
                    await message.answer(analyze)
                    decrerase_balance(user.id)
                else:
                    await message.answer("Пришли ссылку на профиль VK")
            except Exception as e:
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
