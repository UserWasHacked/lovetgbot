import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import load_config
from bot.database import Database
from bot.handlers import setup_routers
from bot.middlewares import DependenciesMiddleware
from bot.services.gemini_service import GeminiService


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger("aiogram").setLevel(logging.INFO)


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    config = load_config()
    db = Database(config.database_path)
    await db.connect()

    ai_service = GeminiService(
        api_key=config.gemini_api_key,
        model=config.gemini_model,
    )

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(
        DependenciesMiddleware(config=config, db=db, ai_service=ai_service)
    )
    dp.include_router(setup_routers())

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
