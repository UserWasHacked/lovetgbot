from aiogram.fsm.state import State, StatesGroup


class CreateMessageStates(StatesGroup):
    target = State()
    custom_target = State()
    context = State()
    custom_context = State()
    details = State()
    length = State()
