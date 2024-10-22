import asyncio
from dotenv import load_dotenv
import os
from os.path import dirname, join
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from database import Database
from utils import validate_url
from model import Model
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()
database = Database()


@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    await message.answer(
        f"""Привет, {message.from_user.full_name}!
LinkLens - это Помощник для HR по созданию профиля человека на основе его поведения в соцсетях, построенный на базе технологии искусственного интеллекта.
Пришли токен или нажми на "Подробнее", чтобы узнать о том, как получить его.""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Подробнее", callback_data="more_info")]
            ]
        ),
    )


async def more_info_callback_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer(
        "Чтобы получить токен, напиши своему руководителю, либо @кто-то, чтобы узнать о нашем продукте."
    )
    await callback_query.answer()


@dp.message()
async def messages_handler(message):
    user = message.from_user.username
    if database.check_access(user):
        try:
            if validate_url(message.text):
                await message.answer("Обрабатываем профиль, подожди немного")
                analyze = Model.analyze_profile(message.text)
                await message.answer("Готово!")
                await message.answer(analyze)
            else:
                await message.answer("Пришли ссылку на профиль VK")
        except Exception as e:
            await message.answer(
                "Произошла ошибка при обработке ссылки. Попробуйте еще раз."
            )
    else:
        database.add_user(user, message.text)
        if database.check_access(user):
            await message.answer(
                "Прекрасно, теперь можешь присылать ссылку на профиль VK"
            )
        else:
            await message.answer("Похоже у нас ошибочка")


def register_handlers(dp: Dispatcher):
    dp.message.register(command_start_handler, CommandStart())
    dp.callback_query.register(
        more_info_callback_handler, lambda c: c.data == "more_info"
    )
    dp.message.register(messages_handler)


async def main():
    register_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
