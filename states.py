"""ACHI BOT - FSM holatlari (sabab so'rash, DM panel matn kiritish uchun)."""
from aiogram.fsm.state import State, StatesGroup


class ReasonFSM(StatesGroup):
    """
    Admin ban/mute/kick/warn buyrug'ini sababsiz yozganda, bot sababni
    so'rab shu holatga o'tadi. Keyingi xabar sabab sifatida qabul qilinadi.
    """

    waiting_reason = State()


class PanelFSM(StatesGroup):
    """
    DM boshqarish paneli (handlers/panel.py) uchun: admin biror tugmani
    bosib "matn kiritish" kerak bo'lgan amalni tanlaganda (masalan
    "Xush kelibsiz matnini o'zgartirish"), bot shu holatga o'tadi va
    keyingi xabarni kutilgan matn sifatida qabul qiladi. Qaysi guruh
    (`chat_id`) va qaysi amal (`kind`) ekanligi FSM data'da saqlanadi.
    """

    waiting_text = State()
