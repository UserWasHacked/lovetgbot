from aiogram import Router

from bot.handlers.create import router as create_router
from bot.handlers.menu import router as menu_router
from bot.handlers.payments import router as payments_router
from bot.handlers.start import router as start_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(start_router)
    root.include_router(menu_router)
    root.include_router(create_router)
    root.include_router(payments_router)
    return root
