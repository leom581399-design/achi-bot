"""
ACHI BOT - PDF hisobot generatori.

Har bir amal (ban/mute/warn/kick) uchun: nishonning profil rasmi (bo'lsa),
ismi, amal turi, sababi, qaysi admin qilgani va vaqti chiroyli jadval
ko'rinishida PDF'ga chiqariladi.

Eslatma: fpdf2'ning core fontlari (Helvetica) faqat lotin-1 belgilarni
qo'llab-quvvatlaydi, ya'ni kirill (rus/o'zbek kirilcha) matnlarni
ko'rsata olmaydi. Shu sabab loyihaga Unicode shriftni (Google Noto Sans,
Apache-2.0 litsenziyali) `fonts/` papkasiga joylashtirib, PDF'da undan
foydalanamiz - bu orqali admin sababni qaysi tilda/alifboda yozsa ham
(lotin, kirill, rus) PDF'da to'g'ri chiqadi.
"""
from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass

from aiogram import Bot
from aiosqlite import Row
from fpdf import FPDF

from config import settings

_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_FONT_FAMILY = "NotoSans"

_ACTION_LABELS = {
    "ban": ("BAN", (192, 57, 43)),
    "tban": ("VAQTINCHA BAN", (192, 57, 43)),
    "unban": ("UNBAN", (39, 174, 96)),
    "mute": ("MUTE", (211, 84, 0)),
    "tmute": ("VAQTINCHA MUTE", (211, 84, 0)),
    "unmute": ("UNMUTE", (39, 174, 96)),
    "kick": ("KICK", (41, 128, 185)),
    "warn": ("OGOHLANTIRISH", (243, 156, 18)),
    "unwarn": ("OGOHLANTIRISH OLINDI", (127, 140, 141)),
}

_AVATAR_SIZE_MM = 16
_ROW_HEIGHT_MM = 22
_PAGE_MARGIN_MM = 12


@dataclass
class ReportRow:
    action: str
    target_id: int
    target_name: str
    admin_name: str
    reason: str | None
    duration: str | None
    created_at: float
    avatar_path: str | None = None


async def _download_avatar(bot: Bot, user_id: int, cache_dir: str) -> str | None:
    """
    Foydalanuvchining eng so'nggi profil rasmini yuklab, faylga saqlaydi.
    Rasm bo'lmasa None qaytaradi (PDF'da o'rniga bo'sh joy qo'yiladi).
    """
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
    except Exception:
        return None
    if not photos or not photos.photos:
        return None

    try:
        biggest = photos.photos[0][-1]
        os.makedirs(cache_dir, exist_ok=True)
        dest_path = os.path.join(cache_dir, f"avatar_{user_id}.jpg")
        await bot.download(biggest.file_id, destination=dest_path)
        return dest_path
    except Exception:
        return None


async def build_report_rows(
    bot: Bot, actions: list[Row], avatar_cache_dir: str
) -> list[ReportRow]:
    rows: list[ReportRow] = []
    avatar_cache: dict[int, str | None] = {}

    for a in actions:
        target_id = a["target_id"]
        if target_id not in avatar_cache:
            avatar_cache[target_id] = await _download_avatar(
                bot, target_id, avatar_cache_dir
            )

        target_name = a["target_username"] and f"@{a['target_username']}" or a["target_name"] or str(target_id)
        rows.append(
            ReportRow(
                action=a["action"],
                target_id=target_id,
                target_name=target_name,
                admin_name=a["admin_name"] or "-",
                reason=a["reason"],
                duration=a["duration"],
                created_at=a["created_at"],
                avatar_path=avatar_cache[target_id],
            )
        )
    return rows


class _AchiPDF(FPDF):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._unicode_font_loaded = False
        regular_path = os.path.join(_FONTS_DIR, "NotoSans-Regular.ttf")
        bold_path = os.path.join(_FONTS_DIR, "NotoSans-Bold.ttf")
        italic_path = os.path.join(_FONTS_DIR, "NotoSans-Italic.ttf")
        if os.path.exists(regular_path):
            try:
                self.add_font(_FONT_FAMILY, "", regular_path)
                if os.path.exists(bold_path):
                    self.add_font(_FONT_FAMILY, "B", bold_path)
                if os.path.exists(italic_path):
                    self.add_font(_FONT_FAMILY, "I", italic_path)
                self._unicode_font_loaded = True
            except Exception:
                self._unicode_font_loaded = False

    @property
    def font_family_name(self) -> str:
        """Unicode (kirill/lotin) shrift yuklangan bo'lsa uni, aks holda
        zaxira sifatida Helvetica'ni qaytaradi."""
        return _FONT_FAMILY if self._unicode_font_loaded else "Helvetica"

    def use_font(self, style: str = "", size: int = 10) -> None:
        family = self.font_family_name
        if family == _FONT_FAMILY and style == "BI":
            # NotoSans uchun qalin-qiya kombinatsiyasi qo'shilmagan, "B" bilan cheklaymiz
            style = "B"
        self.set_font(family, style, size)

    def header(self) -> None:
        self.use_font("B", 16)
        self.set_text_color(155, 39, 102)  # ACHI BOT rangi - pushti-siyohrang
        self.cell(0, 10, "ACHI BOT - Hisobot", ln=True, align="C")
        self.use_font("", 10)
        self.set_text_color(90, 90, 90)

    def footer(self) -> None:
        self.set_y(-12)
        self.use_font("I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 8, f"Sahifa {self.page_no()}", align="C")


def _safe_text(value: str | None, unicode_ok: bool = True) -> str:
    if not value:
        return "-"
    if unicode_ok:
        return value
    # Zaxira holat: Unicode shrift yuklanmagan bo'lsa, lotin-1'dan tashqari
    # belgilarni (masalan emoji, kirill) olib tashlaymiz - aks holda PDF xato beradi.
    return value.encode("latin-1", errors="ignore").decode("latin-1") or "-"


def build_pdf(
    *,
    chat_title: str,
    period_label: str,
    rows: list[ReportRow],
    summary: dict[str, int],
) -> str:
    pdf = _AchiPDF(orientation="P", unit="mm", format="A4")
    unicode_ok = pdf._unicode_font_loaded
    pdf.set_auto_page_break(auto=True, margin=_PAGE_MARGIN_MM + 10)
    pdf.add_page()

    pdf.use_font("", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, _safe_text(f"Guruh: {chat_title}", unicode_ok), ln=True)
    pdf.cell(0, 8, _safe_text(f"Davr: {period_label}", unicode_ok), ln=True)
    pdf.cell(0, 8, _safe_text(f"Tayyorlangan vaqt: {time.strftime('%d.%m.%Y %H:%M')}", unicode_ok), ln=True)
    pdf.ln(2)

    # Qisqa statistika
    pdf.use_font("B", 12)
    pdf.set_fill_color(245, 235, 240)
    pdf.cell(0, 8, "Qisqa statistika", ln=True, fill=True)
    pdf.use_font("", 10)
    stat_line = (
        f"Jami: {summary.get('total', 0)}   |   "
        f"Ban: {summary.get('ban', 0) + summary.get('tban', 0)}   |   "
        f"Mute: {summary.get('mute', 0) + summary.get('tmute', 0)}   |   "
        f"Warn: {summary.get('warn', 0)}   |   "
        f"Kick: {summary.get('kick', 0)}"
    )
    pdf.cell(0, 8, _safe_text(stat_line, unicode_ok), ln=True)
    pdf.ln(4)

    if not rows:
        pdf.use_font("I", 11)
        pdf.cell(0, 10, "Bu davrda hech qanaqa amal qilinmagan, hammasi tinch.", ln=True)
    else:
        pdf.use_font("B", 12)
        pdf.set_fill_color(245, 235, 240)
        pdf.cell(0, 8, "Amallar ro'yxati", ln=True, fill=True)
        pdf.ln(1)

        for row in rows:
            if pdf.get_y() + _ROW_HEIGHT_MM > pdf.h - (_PAGE_MARGIN_MM + 10):
                pdf.add_page()

            y_start = pdf.get_y()
            x_start = pdf.get_x()

            # Avatar (bo'lsa)
            avatar_x = x_start
            if row.avatar_path and os.path.exists(row.avatar_path):
                try:
                    pdf.image(
                        row.avatar_path,
                        x=avatar_x,
                        y=y_start,
                        w=_AVATAR_SIZE_MM,
                        h=_AVATAR_SIZE_MM,
                    )
                except Exception:
                    pdf.set_fill_color(230, 230, 230)
                    pdf.rect(avatar_x, y_start, _AVATAR_SIZE_MM, _AVATAR_SIZE_MM, style="F")
            else:
                pdf.set_fill_color(230, 230, 230)
                pdf.rect(avatar_x, y_start, _AVATAR_SIZE_MM, _AVATAR_SIZE_MM, style="F")
                pdf.set_xy(avatar_x, y_start + 5)
                pdf.use_font("", 7)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(_AVATAR_SIZE_MM, 5, "rasm yo'q", align="C")

            text_x = x_start + _AVATAR_SIZE_MM + 4
            text_w = pdf.w - text_x - _PAGE_MARGIN_MM

            label, color = _ACTION_LABELS.get(row.action, (row.action.upper(), (100, 100, 100)))
            if row.duration:
                label = f"{label} ({row.duration})"

            pdf.set_xy(text_x, y_start)
            pdf.use_font("B", 11)
            pdf.set_text_color(*color)
            pdf.cell(text_w, 6, _safe_text(f"{label}  -  {row.target_name}", unicode_ok), ln=2)

            pdf.set_x(text_x)
            pdf.use_font("", 9)
            pdf.set_text_color(60, 60, 60)
            date_str = time.strftime("%d.%m.%Y %H:%M", time.localtime(row.created_at))
            reason_text = row.reason or "ko'rsatilmagan"
            pdf.cell(text_w, 5, _safe_text(f"Sabab: {reason_text}", unicode_ok), ln=2)

            pdf.set_x(text_x)
            pdf.cell(text_w, 5, _safe_text(f"Admin: {row.admin_name}   |   {date_str}", unicode_ok), ln=2)

            next_y = y_start + _ROW_HEIGHT_MM
            pdf.set_draw_color(225, 225, 225)
            pdf.line(x_start, next_y - 2, pdf.w - _PAGE_MARGIN_MM, next_y - 2)
            pdf.set_xy(x_start, next_y)

    os.makedirs(settings.reports_dir, exist_ok=True)
    filename = f"achi_report_{uuid.uuid4().hex[:8]}.pdf"
    out_path = os.path.join(settings.reports_dir, filename)
    pdf.output(out_path)
    return out_path


def summarize(actions: list[Row]) -> dict[str, int]:
    summary: dict[str, int] = {"total": len(actions)}
    for a in actions:
        summary[a["action"]] = summary.get(a["action"], 0) + 1
    return summary
