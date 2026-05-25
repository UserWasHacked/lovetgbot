from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.config import Config
from bot.database import Database
from bot.services.gemini_service import GeminiService


class DependenciesMiddleware(BaseMiddleware):
    def __init__(
        self,
        config: Config,
        db: Database,
        ai_service: GeminiService,
    ) -> None:
        self._config = config
        self._db = db
        self._ai_service = ai_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["config"] = self._config
        data["db"] = self._db
        data["ai_service"] = self._ai_service
        return await handler(event, data)
