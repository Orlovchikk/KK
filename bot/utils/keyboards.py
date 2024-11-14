from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

choose_plan = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Персональный")],
        [KeyboardButton(text="Корпоративный")],
    ],
    resize_keyboard=True,
)


person = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Анализ 🔎"),
        ],
        [
            KeyboardButton(text="Купить токены 💸"),
            KeyboardButton(text="Баланс 💰"),
        ],
    ],
    resize_keyboard=True,
)

corporation = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Анализ 🔎"),
        ],
        [
            KeyboardButton(text="Оформить подписку ✅"),
            KeyboardButton(text="Проверить подписку 💰"),
        ],
        [
            KeyboardButton(text="Прислать секретный код 🙈"),
            KeyboardButton(text="Мой секретный код"),
        ],
        [
            KeyboardButton(text="Привязанные пользователи 👤"),
        ],
    ],
    resize_keyboard=True,
)


choose_tokens = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="10 токенов", callback_data="10_tokens"),
        ],
        [InlineKeyboardButton(text="50 токенов", callback_data="50_tokens")],
        [
            InlineKeyboardButton(text="100 токенов", callback_data="100_tokens"),
        ],
        [InlineKeyboardButton(text="1000 токенов", callback_data="1000_tokens")],
    ]
)

subs = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Подписка 1 месяц", callback_data="1_month")],
        [InlineKeyboardButton(text="Подписка 3 месяца", callback_data="3_month")],
        [InlineKeyboardButton(text="Подписка 1 год", callback_data="1_year")],
    ]
)


def users(users):
    return InlineKeyboardMarkup(
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
