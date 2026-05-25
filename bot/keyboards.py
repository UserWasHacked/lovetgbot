from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.config import Config

MENU_CREATE = "💌 Создать послание"
MENU_TOPUP = "💰 Пополнить баланс"
MENU_PROFILE = "👤 Мой профиль"

TARGET_LABELS = {
    "boyfriend": "Парень",
    "girlfriend": "Девушка",
    "husband": "Муж",
    "wife": "Жена",
    "other": "Другое",
}

CONTEXT_LABELS = {
    "support_day": "Поддержать днём",
    "make_up": "Помириться",
    "before_sleep": "Перед сном",
    "anniversary": "С годовщиной",
    "custom": "Свой вариант",
}

LENGTH_LABELS = {
    "sms": "Короткое СМС",
    "medium": "Среднее сообщение",
    "letter": "Письмо",
}

LENGTH_PROMPT = {
    "sms": "короткое СМС в пару предложений",
    "medium": "среднее сообщение для мессенджера",
    "letter": "небольшое письмо",
}


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_CREATE)],
            [KeyboardButton(text=MENU_TOPUP), KeyboardButton(text=MENU_PROFILE)],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def target_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"target:{key}")]
        for key, label in TARGET_LABELS.items()
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="create:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def context_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"context:{key}")]
        for key, label in CONTEXT_LABELS.items()
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="create:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def length_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"length:{key}")]
        for key, label in LENGTH_LABELS.items()
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="create:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def topup_keyboard(config: Config) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Купить 5 генераций — {config.pack_5.stars} ⭐",
                    callback_data="buy:pack_5",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Купить 20 генераций — {config.pack_20.stars} ⭐",
                    callback_data="buy:pack_20",
                )
            ],
        ]
    )


def insufficient_balance_keyboard(config: Config) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⭐ Купить 5 ({config.pack_5.stars} звёзд)",
                    callback_data="buy:pack_5",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⭐ Купить 20 ({config.pack_20.stars} звёзд)",
                    callback_data="buy:pack_20",
                )
            ],
        ]
    )
