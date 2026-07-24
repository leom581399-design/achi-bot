"""ACHI BOT - FSM holatlari (sabab so'rash uchun)."""
from aiogram.fsm.state import State, StatesGroup


class ReasonFSM(StatesGroup):
    """
    Admin ban/mute/kick/warn buyrug'ini sababsiz yozganda, bot sababni
    so'rab shu holatga o'tadi. Keyingi xabar sabab sifatida qabul qilinadi.
    """

    waiting_reason = State()
