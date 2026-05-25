import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import Config
from bot.database import Database
from bot.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router(name="start")

WELCOME_NEW = (
    "Привет! Я помогаю выражать чувства искренне, без банальных открыточных клише.\n\n"
    "🎁 Тебе доступно <b>{balance}</b> бесплатные генерации — попробуй создать первое послание.\n\n"
    "В меню ниже: создать текст, пополнить баланс или посмотреть профиль."
)

WELCOME_BACK = (
    "Снова привет! Помогаю выражать чувства искренне, без банальных открыточных клише.\n\n"
    "На балансе: <b>{balance}</b> генераций. Выбери действие в меню."
)


@router.message(CommandStart())
async def cmd_start(message: Message, config: Config, db: Database) -> None:
    user = message.from_user
    if not user:
        return

    record, is_new = await db.get_or_create_user(
        user_id=user.id,
        username=user.username,
        free_generations=config.free_generations,
    )
    if user.username != record.username:
        await db.update_username(user.id, user.username)

    text = WELCOME_NEW.format(balance=record.generations_balance) if is_new else WELCOME_BACK.format(
        balance=record.generations_balance
    )
    await message.answer(text, reply_markup=main_menu_keyboard())
    logger.info("User %s started bot (new=%s)", user.id, is_new)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/start — главное меню\n"
        "/help — эта справка\n\n"
        "Используй кнопки меню для создания посланий и покупки генераций."
    )
