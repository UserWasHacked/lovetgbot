import logging

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bot.config import Config, PackConfig
from bot.database import Database
logger = logging.getLogger(__name__)
router = Router(name="payments")

CURRENCY_STARS = "XTR"


def _pack_by_payload(config: Config, payload: str) -> PackConfig | None:
    if payload == config.pack_5.payload:
        return config.pack_5
    if payload == config.pack_20.payload:
        return config.pack_20
    return None


async def send_pack_invoice(callback: CallbackQuery, config: Config, payload_key: str) -> None:
    pack = _pack_by_payload(config, payload_key.replace("buy:", ""))
    if not pack or not callback.message or not callback.from_user:
        await callback.answer("Пакет не найден", show_alert=True)
        return

    await callback.message.answer_invoice(
        title=f"{pack.generations} генераций посланий",
        description="Персонализированные любовные тексты без банальных клише",
        payload=pack.payload,
        currency=CURRENCY_STARS,
        prices=[LabeledPrice(label=f"{pack.generations} генераций", amount=pack.stars)],
        provider_token="",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def on_buy_pack(callback: CallbackQuery, config: Config) -> None:
    await send_pack_invoice(callback, config, callback.data or "")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery, config: Config) -> None:
    pack = _pack_by_payload(config, query.invoice_payload)
    if pack:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Неизвестный пакет")


@router.message(F.successful_payment)
async def successful_payment(message: Message, config: Config, db: Database) -> None:
    payment = message.successful_payment
    user = message.from_user
    if not payment or not user:
        return

    pack = _pack_by_payload(config, payment.invoice_payload)
    if not pack:
        await message.answer("Оплата получена, но пакет не распознан. Напиши в поддержку бота.")
        return

    charge_id = payment.telegram_payment_charge_id
    if await db.is_payment_processed(charge_id):
        balance = await db.get_balance(user.id)
        await message.answer(f"Эта оплата уже была учтена. Баланс: <b>{balance}</b> генераций.")
        return

    await db.record_payment(
        user_id=user.id,
        charge_id=charge_id,
        pack_payload=pack.payload,
        stars_amount=pack.stars,
        generations_added=pack.generations,
    )
    balance = await db.add_generations(user.id, pack.generations)
    logger.info(
        "Payment success user=%s pack=%s stars=%s balance=%s",
        user.id,
        pack.payload,
        pack.stars,
        balance,
    )
    await message.answer(
        f"✅ Оплата прошла успешно!\n"
        f"На баланс зачислено <b>{pack.generations}</b> генераций.\n"
        f"Текущий остаток: <b>{balance}</b>."
    )
