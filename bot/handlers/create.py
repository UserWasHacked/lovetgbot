import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import Config
from bot.database import Database
from bot.keyboards import (
    CONTEXT_LABELS,
    LENGTH_LABELS,
    LENGTH_PROMPT,
    TARGET_LABELS,
    cancel_keyboard,
    context_keyboard,
    insufficient_balance_keyboard,
    length_keyboard,
    main_menu_keyboard,
    target_keyboard,
)
from bot.services.gemini_service import GeminiService
from bot.states import CreateMessageStates

logger = logging.getLogger(__name__)
router = Router(name="create")

CANCEL_TEXT = "❌ Отмена"


async def start_creation_flow(message: Message, state: FSMContext, db: Database) -> None:
    user = message.from_user
    if not user:
        return
    if not await db.get_user(user.id):
        await message.answer("Сначала нажми /start.")
        return

    await state.clear()
    await state.set_state(CreateMessageStates.target)
    await message.answer(
        "Шаг 1 из 4\n<b>Кому адресовано послание?</b>",
        reply_markup=cancel_keyboard(),
    )
    await message.answer("Выбери адресата:", reply_markup=target_keyboard())


@router.message(F.text == CANCEL_TEXT)
async def cancel_creation(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if not current:
        return
    await state.clear()
    await message.answer("Создание отменено.", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "create:cancel")
async def cancel_creation_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text("Создание отменено.")
    await callback.answer()
    if callback.message:
        await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())


@router.callback_query(CreateMessageStates.target, F.data.startswith("target:"))
async def step_target(callback: CallbackQuery, state: FSMContext) -> None:
    key = (callback.data or "").split(":", 1)[-1]
    if key not in TARGET_LABELS:
        await callback.answer("Неверный выбор")
        return

    if key == "other":
        await state.set_state(CreateMessageStates.custom_target)
        if callback.message:
            await callback.message.edit_text(
                "Кому адресовано послание? Напиши своими словами (например: «любимому человеку», «маме»):"
            )
        await callback.answer()
        return

    await state.update_data(target_key=key, target_label=TARGET_LABELS[key])
    await state.set_state(CreateMessageStates.context)
    if callback.message:
        await callback.message.edit_text(
            f"Адресат: <b>{TARGET_LABELS[key]}</b>\n\n"
            "Шаг 2 из 4\n<b>Повод или контекст?</b>",
            reply_markup=context_keyboard(),
        )
    await callback.answer()


@router.message(CreateMessageStates.custom_target, F.text)
async def step_custom_target(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == CANCEL_TEXT:
        return
    if len(text) < 2:
        await message.answer("Уточни, кому адресовано послание.")
        return

    await state.update_data(target_key="other", target_label=text)
    await state.set_state(CreateMessageStates.context)
    await message.answer(
        f"Адресат: <b>{text}</b>\n\nШаг 2 из 4\n<b>Повод или контекст?</b>",
        reply_markup=context_keyboard(),
    )


@router.callback_query(CreateMessageStates.context, F.data.startswith("context:"))
async def step_context(callback: CallbackQuery, state: FSMContext) -> None:
    key = (callback.data or "").split(":", 1)[-1]
    if key not in CONTEXT_LABELS:
        await callback.answer("Неверный выбор")
        return

    if key == "custom":
        await state.set_state(CreateMessageStates.custom_context)
        if callback.message:
            await callback.message.edit_text(
                "Опиши свой повод текстом (например: «хочу поблагодарить за поддержку на работе»):"
            )
        await callback.answer()
        return

    await state.update_data(context_key=key, context_label=CONTEXT_LABELS[key])
    await state.set_state(CreateMessageStates.details)
    if callback.message:
        await callback.message.edit_text(
            f"Повод: <b>{CONTEXT_LABELS[key]}</b>\n\n"
            "Шаг 3 из 4\n<b>Детали для персонализации</b>\n\n"
            "Напиши конкретику: привычки, воспоминания, мелочи "
            '(например: «она вкусно готовит кофе», «вчера были в кино»).'
        )
    await callback.answer()


@router.message(CreateMessageStates.custom_context, F.text)
async def step_custom_context(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 3:
        await message.answer("Напиши повод чуть подробнее (минимум 3 символа).")
        return
    if text == CANCEL_TEXT:
        return

    await state.update_data(context_key="custom", context_label=text)
    await state.set_state(CreateMessageStates.details)
    await message.answer(
        "Шаг 3 из 4\n<b>Детали для персонализации</b>\n\n"
        "Напиши конкретику про человека и ваши моменты:"
    )


@router.message(CreateMessageStates.details, F.text)
async def step_details(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == CANCEL_TEXT:
        return
    if len(text) < 3:
        await message.answer("Добавь хотя бы пару слов — так текст будет живее.")
        return

    await state.update_data(details=text)
    await state.set_state(CreateMessageStates.length)
    await message.answer(
        "Шаг 4 из 4\n<b>Какой длины нужен текст?</b>",
        reply_markup=length_keyboard(),
    )


@router.callback_query(CreateMessageStates.length, F.data.startswith("length:"))
async def step_length_and_generate(
    callback: CallbackQuery,
    state: FSMContext,
    config: Config,
    db: Database,
    ai_service: GeminiService,
) -> None:
    user = callback.from_user
    if not user or not callback.message:
        await callback.answer()
        return

    key = (callback.data or "").split(":", 1)[-1]
    if key not in LENGTH_LABELS:
        await callback.answer("Неверный выбор")
        return

    data = await state.get_data()
    balance = await db.get_balance(user.id)
    if balance < 1:
        await state.clear()
        await callback.message.edit_text(
            "😔 Генерации закончились.\n\n"
            "Пополни баланс, чтобы создать новое послание:",
            reply_markup=insufficient_balance_keyboard(config),
        )
        await callback.answer()
        return

    if not await db.spend_generation(user.id):
        await state.clear()
        await callback.message.edit_text(
            "Не удалось списать генерацию. Попробуй снова или пополни баланс.",
            reply_markup=insufficient_balance_keyboard(config),
        )
        await callback.answer()
        return

    await callback.message.edit_text("✨ Создаю послание… подожди несколько секунд.")
    await callback.answer()

    target_label = data.get("target_label", "близкий человек")
    context_label = data.get("context_label", "без особого повода")
    details = data.get("details", "")
    length_prompt = LENGTH_PROMPT[key]

    try:
        result = await ai_service.generate_love_message(
            user_target=target_label,
            user_context=context_label,
            user_details=details,
            user_length=length_prompt,
        )
        await db.save_generation_history(
            user_id=user.id,
            target=data.get("target_key", ""),
            context=data.get("context_key", ""),
            details=details,
            length_type=key,
            result_text=result,
        )
        new_balance = await db.get_balance(user.id)
        await callback.message.answer(
            f"💌 <b>Твоё послание</b>\n\n{result}\n\n"
            f"<i>Осталось генераций: {new_balance}</i>",
            reply_markup=main_menu_keyboard(),
        )
        logger.info("Generation OK for user %s", user.id)
    except Exception as exc:
        logger.exception("Generation failed for user %s: %s", user.id, exc)
        await db.refund_generation(user.id)
        await callback.message.answer(
            "Произошла ошибка при генерации. Генерация возвращена на баланс. "
            "Попробуй ещё раз чуть позже.",
            reply_markup=main_menu_keyboard(),
        )
    finally:
        await state.clear()
