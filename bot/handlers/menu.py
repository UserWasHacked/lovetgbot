import logging

from aiogram import F, Router
from aiogram.types import Message

from bot.config import Config
from bot.database import Database
from bot.handlers.create import start_creation_flow
from bot.keyboards import (
    MENU_CREATE,
    MENU_PROFILE,
    MENU_TOPUP,
    topup_keyboard,
)

logger = logging.getLogger(__name__)
router = Router(name="menu")


@router.message(F.text == MENU_CREATE)
async def menu_create(message: Message, state, db: Database) -> None:
    await start_creation_flow(message, state, db)


@router.message(F.text == MENU_TOPUP)
async def menu_topup(message: Message, config: Config) -> None:
    await message.answer(
        "Выбери пакет генераций. Оплата через Telegram Stars ⭐",
        reply_markup=topup_keyboard(config),
    )


@router.message(F.text == MENU_PROFILE)
async def menu_profile(message: Message, db: Database) -> None:
    user = message.from_user
    if not user:
        return
    record = await db.get_user(user.id)
    if not record:
        await message.answer("Сначала нажми /start для регистрации.")
        return
    await message.answer(
        f"👤 <b>Твой профиль</b>\n\n"
        f"ID: <code>{record.user_id}</code>\n"
        f"Остаток генераций: <b>{record.generations_balance}</b>\n"
        f"Регистрация: {record.created_at[:10]}"
    )
