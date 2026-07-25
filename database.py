"""
ACHI BOT - ma'lumotlar bazasi qatlami (SQLite, aiosqlite orqali).

Bitta global ulanish (connection) ochib, butun bot davomida shu orqali
ishlaymiz. Barcha jadvallar shu faylda e'lon qilinadi.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import aiosqlite

from config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    chat_title TEXT,
    action TEXT NOT NULL,           -- ban / tban / unban / mute / tmute / unmute / kick / warn / unwarn
    target_id INTEGER NOT NULL,
    target_name TEXT,
    target_username TEXT,
    admin_id INTEGER NOT NULL,
    admin_name TEXT,
    reason TEXT,
    duration TEXT,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_actions_chat_time ON actions(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_actions_target ON actions(chat_id, target_id);

CREATE TABLE IF NOT EXISTS warns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    reason TEXT,
    admin_id INTEGER NOT NULL,
    admin_name TEXT,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_warns_chat_target ON warns(chat_id, target_id);

CREATE TABLE IF NOT EXISTS filters (
    chat_id INTEGER NOT NULL,
    trigger TEXT NOT NULL,
    reply TEXT NOT NULL,
    PRIMARY KEY (chat_id, trigger)
);

CREATE TABLE IF NOT EXISTS notes (
    chat_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    PRIMARY KEY (chat_id, name)
);

CREATE TABLE IF NOT EXISTS locks (
    chat_id INTEGER NOT NULL,
    lock_type TEXT NOT NULL,
    PRIMARY KEY (chat_id, lock_type)
);

-- "Personal" - admin o'zi xohlagan nomda maxsus buyruq yaratadi:
-- /personal <nom> <matn> deb saqlansa, keyinchalik shu guruhda kimdur
-- "/<nom>" deb yozganda bot saqlangan matnni chiqarib beradi (masalan
-- tez-tez so'raladigan javoblar, havolalar va h.k. uchun qulay).
CREATE TABLE IF NOT EXISTS custom_commands (
    chat_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    added_by INTEGER NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (chat_id, name)
);

CREATE TABLE IF NOT EXISTS chat_settings (
    chat_id INTEGER PRIMARY KEY,
    chat_title TEXT,
    welcome_text TEXT,
    goodbye_text TEXT,
    rules_text TEXT,
    clean_service INTEGER NOT NULL DEFAULT 0,
    captcha_enabled INTEGER NOT NULL DEFAULT 0,
    report_enabled INTEGER NOT NULL DEFAULT 1,
    premium_until REAL,              -- 30-kunlik premium tugash vaqti (NULL = premium emas)
    premium_lifetime INTEGER NOT NULL DEFAULT 0,  -- 1 = umrbod premium
    -- Guruhga qo'shilish so'rovlarini (join request) avtomatik qabul
    -- qilish. STANDART HOLATDA O'CHIRILGAN (0) - admin ataylab
    -- /autoapprove on yozmaguncha, so'rovlar qo'lda (admin tomonidan)
    -- ko'rib chiqiladi.
    auto_approve_join INTEGER NOT NULL DEFAULT 0,
    -- AI-yordamchi moderatsiya (premium funksiya): yoqilgan bo'lsa, har
    -- bir matnli xabar spam/haqoratga o'xshab ko'rinsa avtomatik
    -- o'chiriladi. STANDART HOLATDA O'CHIRILGAN - admin DM panel orqali
    -- (yoki /aimod on) o'zi yoqadi.
    ai_moderation_enabled INTEGER NOT NULL DEFAULT 0
);

-- Telegram Stars orqali qilingan barcha to'lovlar tarixi (audit uchun)
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name TEXT,
    plan TEXT NOT NULL,               -- '30d' / 'lifetime'
    amount_stars INTEGER NOT NULL,
    telegram_charge_id TEXT,
    created_at REAL NOT NULL
);

-- Federatsiyalar: bir nechta guruhni bog'lab, umumiy ban ro'yxatini
-- ishlatish (premium funksiya)
CREATE TABLE IF NOT EXISTS federations (
    fed_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fed_admins (
    fed_id TEXT NOT NULL,
    admin_id INTEGER NOT NULL,
    PRIMARY KEY (fed_id, admin_id)
);

CREATE TABLE IF NOT EXISTS fed_chats (
    fed_id TEXT NOT NULL,
    chat_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS fed_bans (
    fed_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    reason TEXT,
    banned_by INTEGER NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (fed_id, user_id)
);

CREATE TABLE IF NOT EXISTS pending_captcha (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    join_message_id INTEGER,
    prompt_message_id INTEGER,
    expires_at REAL NOT NULL,
    PRIMARY KEY (chat_id, user_id)
);

-- Telegram Bot API'da "guruhdagi barcha a'zolarni olish" degan tayyor
-- metod yo'q (faqat kanal/kichik guruhlar uchun cheklangan holatda
-- ishlaydi). Shu sabab @admin/@admins ping va /tag funksiyalari uchun
-- guruhda kim yozganini "ko'rib qolgan sari" shu jadvalga yozib boramiz.
CREATE TABLE IF NOT EXISTS known_members (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    full_name TEXT,
    username TEXT,
    last_seen REAL NOT NULL,
    first_seen REAL,
    PRIMARY KEY (chat_id, user_id)
);

-- Botning o'zi (SUPER_ADMINS yoki guruh egasi) tomonidan /adminber orqali
-- "bot darajasida" admin qilingan foydalanuvchilar. Bu Telegram'ning
-- haqiqiy admin ro'yxatidan ALOHIDA - chunki bot Telegram API orqali
-- promote_chat_member chaqirib, HAQIQIY Telegram adminligini beradi;
-- shu jadval esa faqat "kim ACHI BOT orqali admin qilingan" tarixini
-- yuritish uchun (keyinchalik /adminol bilan olib tashlash, hisobot
-- uchun kerak bo'ladi).
CREATE TABLE IF NOT EXISTS bot_promoted_admins (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    promoted_by INTEGER NOT NULL,
    promoted_at REAL NOT NULL,
    PRIMARY KEY (chat_id, user_id)
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()
        await self._run_migrations()

    async def _run_migrations(self) -> None:
        """
        `CREATE TABLE IF NOT EXISTS` allaqachon mavjud jadvalga yangi
        ustun qo'shmaydi, shu sabab avval yaratilgan bazalarda (bot
        yangilanishidan oldin) ba'zi ustunlar bo'lmasligi mumkin. Shu
        yerda xavfsiz tekshirib, kerak bo'lsa qo'shamiz (yangi bazalarda
        bu ustunlar schema orqali allaqachon bor, shu sabab
        `duplicate column` xatosini e'tiborsiz qoldiramiz).
        """
        migrations = [
            "ALTER TABLE known_members ADD COLUMN first_seen REAL",
            "ALTER TABLE chat_settings ADD COLUMN auto_approve_join INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE chat_settings ADD COLUMN ai_moderation_enabled INTEGER NOT NULL DEFAULT 0",
        ]
        for sql in migrations:
            try:
                await self.conn.execute(sql)
                await self.conn.commit()
            except Exception:
                pass

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        assert self._conn is not None, "Database ulanmagan, avval connect() chaqiring"
        return self._conn

    # ------------------------------------------------------------------
    # Actions (ban/mute/warn/kick tarixi)
    # ------------------------------------------------------------------

    async def log_action(
        self,
        *,
        chat_id: int,
        chat_title: str | None,
        action: str,
        target_id: int,
        target_name: str | None,
        target_username: str | None,
        admin_id: int,
        admin_name: str | None,
        reason: str | None,
        duration: str | None = None,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO actions (
                chat_id, chat_title, action, target_id, target_name,
                target_username, admin_id, admin_name, reason, duration, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                chat_title,
                action,
                target_id,
                target_name,
                target_username,
                admin_id,
                admin_name,
                reason,
                duration,
                time.time(),
            ),
        )
        await self.conn.commit()

    async def get_actions_since(
        self, chat_id: int, since_ts: float, target_id: int | None = None
    ) -> list[aiosqlite.Row]:
        if target_id is not None:
            cursor = await self.conn.execute(
                """
                SELECT * FROM actions
                WHERE chat_id = ? AND created_at >= ? AND target_id = ?
                ORDER BY created_at ASC
                """,
                (chat_id, since_ts, target_id),
            )
        else:
            cursor = await self.conn.execute(
                """
                SELECT * FROM actions
                WHERE chat_id = ? AND created_at >= ?
                ORDER BY created_at ASC
                """,
                (chat_id, since_ts),
            )
        return await cursor.fetchall()

    async def get_all_active_report_chats(self) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(
            "SELECT chat_id, chat_title FROM chat_settings WHERE report_enabled = 1"
        )
        return await cursor.fetchall()

    async def list_all_chats(self) -> list[aiosqlite.Row]:
        """
        Bot hozirgacha ko'rgan (kamida bir marta guruh xabari qabul
        qilingan) barcha guruhlarni qaytaradi - `/achi` buyrug'ida bot
        egasi (super-admin) uchun "qaysi guruhlarda ishlab turaman"
        ro'yxatini chiqarish uchun ishlatiladi.
        """
        cursor = await self.conn.execute(
            "SELECT chat_id, chat_title, premium_until, premium_lifetime "
            "FROM chat_settings ORDER BY chat_id"
        )
        return await cursor.fetchall()

    # ------------------------------------------------------------------
    # Warns
    # ------------------------------------------------------------------

    async def add_warn(
        self,
        chat_id: int,
        target_id: int,
        reason: str | None,
        admin_id: int,
        admin_name: str | None,
    ) -> int:
        await self.conn.execute(
            """
            INSERT INTO warns (chat_id, target_id, reason, admin_id, admin_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chat_id, target_id, reason, admin_id, admin_name, time.time()),
        )
        await self.conn.commit()
        return await self.count_warns(chat_id, target_id)

    async def count_warns(self, chat_id: int, target_id: int) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) as c FROM warns WHERE chat_id = ? AND target_id = ?",
            (chat_id, target_id),
        )
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    async def list_warns(self, chat_id: int, target_id: int) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(
            """
            SELECT * FROM warns WHERE chat_id = ? AND target_id = ?
            ORDER BY created_at ASC
            """,
            (chat_id, target_id),
        )
        return await cursor.fetchall()

    async def remove_last_warn(self, chat_id: int, target_id: int) -> bool:
        cursor = await self.conn.execute(
            """
            SELECT id FROM warns WHERE chat_id = ? AND target_id = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (chat_id, target_id),
        )
        row = await cursor.fetchone()
        if not row:
            return False
        await self.conn.execute("DELETE FROM warns WHERE id = ?", (row["id"],))
        await self.conn.commit()
        return True

    async def clear_warns(self, chat_id: int, target_id: int) -> None:
        await self.conn.execute(
            "DELETE FROM warns WHERE chat_id = ? AND target_id = ?",
            (chat_id, target_id),
        )
        await self.conn.commit()

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    async def set_filter(self, chat_id: int, trigger: str, reply: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO filters (chat_id, trigger, reply) VALUES (?, ?, ?)
            ON CONFLICT(chat_id, trigger) DO UPDATE SET reply = excluded.reply
            """,
            (chat_id, trigger.lower(), reply),
        )
        await self.conn.commit()

    async def get_filter(self, chat_id: int, trigger: str) -> str | None:
        cursor = await self.conn.execute(
            "SELECT reply FROM filters WHERE chat_id = ? AND trigger = ?",
            (chat_id, trigger.lower()),
        )
        row = await cursor.fetchone()
        return row["reply"] if row else None

    async def list_filters(self, chat_id: int) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(
            "SELECT trigger FROM filters WHERE chat_id = ? ORDER BY trigger",
            (chat_id,),
        )
        return await cursor.fetchall()

    async def all_filters(self, chat_id: int) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(
            "SELECT trigger, reply FROM filters WHERE chat_id = ?",
            (chat_id,),
        )
        return await cursor.fetchall()

    async def remove_filter(self, chat_id: int, trigger: str) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM filters WHERE chat_id = ? AND trigger = ?",
            (chat_id, trigger.lower()),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    async def save_note(self, chat_id: int, name: str, content: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO notes (chat_id, name, content) VALUES (?, ?, ?)
            ON CONFLICT(chat_id, name) DO UPDATE SET content = excluded.content
            """,
            (chat_id, name.lower(), content),
        )
        await self.conn.commit()

    async def get_note(self, chat_id: int, name: str) -> str | None:
        cursor = await self.conn.execute(
            "SELECT content FROM notes WHERE chat_id = ? AND name = ?",
            (chat_id, name.lower()),
        )
        row = await cursor.fetchone()
        return row["content"] if row else None

    async def list_notes(self, chat_id: int) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(
            "SELECT name FROM notes WHERE chat_id = ? ORDER BY name", (chat_id,)
        )
        return await cursor.fetchall()

    async def remove_note(self, chat_id: int, name: str) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM notes WHERE chat_id = ? AND name = ?",
            (chat_id, name.lower()),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Locks
    # ------------------------------------------------------------------

    async def set_lock(self, chat_id: int, lock_type: str) -> None:
        await self.conn.execute(
            "INSERT OR IGNORE INTO locks (chat_id, lock_type) VALUES (?, ?)",
            (chat_id, lock_type),
        )
        await self.conn.commit()

    async def unset_lock(self, chat_id: int, lock_type: str) -> None:
        await self.conn.execute(
            "DELETE FROM locks WHERE chat_id = ? AND lock_type = ?",
            (chat_id, lock_type),
        )
        await self.conn.commit()

    async def is_locked(self, chat_id: int, lock_type: str) -> bool:
        cursor = await self.conn.execute(
            "SELECT 1 FROM locks WHERE chat_id = ? AND lock_type = ?",
            (chat_id, lock_type),
        )
        return await cursor.fetchone() is not None

    async def list_locks(self, chat_id: int) -> list[str]:
        cursor = await self.conn.execute(
            "SELECT lock_type FROM locks WHERE chat_id = ?", (chat_id,)
        )
        rows = await cursor.fetchall()
        return [r["lock_type"] for r in rows]

    # ------------------------------------------------------------------
    # Custom commands (/personal - o'zingizning buyrug'ingizni yaratish)
    # ------------------------------------------------------------------

    async def add_custom_command(
        self, chat_id: int, name: str, content: str, added_by: int
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO custom_commands (chat_id, name, content, added_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, name) DO UPDATE SET
                content = excluded.content,
                added_by = excluded.added_by,
                created_at = excluded.created_at
            """,
            (chat_id, name.lower(), content, added_by, time.time()),
        )
        await self.conn.commit()

    async def remove_custom_command(self, chat_id: int, name: str) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM custom_commands WHERE chat_id = ? AND name = ?",
            (chat_id, name.lower()),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def get_custom_command(self, chat_id: int, name: str) -> str | None:
        cursor = await self.conn.execute(
            "SELECT content FROM custom_commands WHERE chat_id = ? AND name = ?",
            (chat_id, name.lower()),
        )
        row = await cursor.fetchone()
        return row["content"] if row else None

    async def list_custom_commands(self, chat_id: int) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(
            "SELECT name FROM custom_commands WHERE chat_id = ? ORDER BY name",
            (chat_id,),
        )
        return await cursor.fetchall()

    # ------------------------------------------------------------------
    # Chat settings (welcome/goodbye/rules/clean-service/captcha)
    # ------------------------------------------------------------------

    async def ensure_chat(self, chat_id: int, chat_title: str | None) -> None:
        await self.conn.execute(
            """
            INSERT INTO chat_settings (chat_id, chat_title) VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET chat_title = excluded.chat_title
            """,
            (chat_id, chat_title),
        )
        await self.conn.commit()

    async def get_chat_settings(self, chat_id: int) -> aiosqlite.Row | None:
        cursor = await self.conn.execute(
            "SELECT * FROM chat_settings WHERE chat_id = ?", (chat_id,)
        )
        return await cursor.fetchone()

    async def update_chat_setting(self, chat_id: int, **fields: Any) -> None:
        if not fields:
            return
        columns = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values())
        await self.conn.execute(
            f"UPDATE chat_settings SET {columns} WHERE chat_id = ?",
            (*values, chat_id),
        )
        await self.conn.commit()

    # ------------------------------------------------------------------
    # Captcha pending
    # ------------------------------------------------------------------

    async def add_pending_captcha(
        self,
        chat_id: int,
        user_id: int,
        join_message_id: int | None,
        prompt_message_id: int | None,
        expires_at: float,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO pending_captcha (chat_id, user_id, join_message_id, prompt_message_id, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                join_message_id = excluded.join_message_id,
                prompt_message_id = excluded.prompt_message_id,
                expires_at = excluded.expires_at
            """,
            (chat_id, user_id, join_message_id, prompt_message_id, expires_at),
        )
        await self.conn.commit()

    async def pop_pending_captcha(
        self, chat_id: int, user_id: int
    ) -> aiosqlite.Row | None:
        cursor = await self.conn.execute(
            "SELECT * FROM pending_captcha WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        row = await cursor.fetchone()
        if row:
            await self.conn.execute(
                "DELETE FROM pending_captcha WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            )
            await self.conn.commit()
        return row

    async def get_expired_captchas(self, now: float) -> list[aiosqlite.Row]:
        cursor = await self.conn.execute(
            "SELECT * FROM pending_captcha WHERE expires_at <= ?", (now,)
        )
        return await cursor.fetchall()

    # ------------------------------------------------------------------
    # Premium (Telegram Stars)
    # ------------------------------------------------------------------

    async def is_chat_premium(self, chat_id: int) -> bool:
        row = await self.get_chat_settings(chat_id)
        if not row:
            return False
        if row["premium_lifetime"]:
            return True
        if row["premium_until"] and row["premium_until"] > time.time():
            return True
        return False

    async def grant_premium(
        self, chat_id: int, *, lifetime: bool = False, days: int = 30
    ) -> None:
        await self.ensure_chat(chat_id, None)
        if lifetime:
            await self.update_chat_setting(chat_id, premium_lifetime=1)
            return

        current = await self.get_chat_settings(chat_id)
        now = time.time()
        base = now
        if current and current["premium_until"] and current["premium_until"] > now:
            # Muddati tugamagan premium ustiga qo'shib boramiz (kumulyativ)
            base = current["premium_until"]
        new_until = base + days * 86400
        await self.update_chat_setting(chat_id, premium_until=new_until)

    async def revoke_premium(self, chat_id: int) -> None:
        """Guruhning premium holatini butunlay bekor qiladi (bot egasi
        DM orqali qo'lda bergan yoki Stars orqali sotib olingan bo'lishidan
        qat'iy nazar)."""
        await self.ensure_chat(chat_id, None)
        await self.update_chat_setting(chat_id, premium_lifetime=0, premium_until=0)

    async def record_payment(
        self,
        *,
        chat_id: int,
        user_id: int,
        user_name: str | None,
        plan: str,
        amount_stars: int,
        telegram_charge_id: str | None,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO payments (
                chat_id, user_id, user_name, plan, amount_stars,
                telegram_charge_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                user_id,
                user_name,
                plan,
                amount_stars,
                telegram_charge_id,
                time.time(),
            ),
        )
        await self.conn.commit()

    async def count_filters(self, chat_id: int) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) as c FROM filters WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    async def count_notes(self, chat_id: int) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) as c FROM notes WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    # ------------------------------------------------------------------
    # Federatsiya (premium funksiya)
    # ------------------------------------------------------------------

    async def create_federation(self, fed_id: str, name: str, owner_id: int) -> None:
        await self.conn.execute(
            "INSERT INTO federations (fed_id, name, owner_id, created_at) VALUES (?, ?, ?, ?)",
            (fed_id, name, owner_id, time.time()),
        )
        await self.conn.execute(
            "INSERT INTO fed_admins (fed_id, admin_id) VALUES (?, ?)",
            (fed_id, owner_id),
        )
        await self.conn.commit()

    async def get_federation(self, fed_id: str) -> aiosqlite.Row | None:
        cursor = await self.conn.execute(
            "SELECT * FROM federations WHERE fed_id = ?", (fed_id,)
        )
        return await cursor.fetchone()

    async def get_federation_by_owner(self, owner_id: int) -> aiosqlite.Row | None:
        cursor = await self.conn.execute(
            "SELECT * FROM federations WHERE owner_id = ?", (owner_id,)
        )
        return await cursor.fetchone()

    async def link_chat_to_federation(self, fed_id: str, chat_id: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO fed_chats (fed_id, chat_id) VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET fed_id = excluded.fed_id
            """,
            (fed_id, chat_id),
        )
        await self.conn.commit()

    async def unlink_chat_from_federation(self, chat_id: int) -> None:
        await self.conn.execute("DELETE FROM fed_chats WHERE chat_id = ?", (chat_id,))
        await self.conn.commit()

    async def get_chat_federation(self, chat_id: int) -> str | None:
        cursor = await self.conn.execute(
            "SELECT fed_id FROM fed_chats WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        return row["fed_id"] if row else None

    async def get_federation_chats(self, fed_id: str) -> list[int]:
        cursor = await self.conn.execute(
            "SELECT chat_id FROM fed_chats WHERE fed_id = ?", (fed_id,)
        )
        rows = await cursor.fetchall()
        return [r["chat_id"] for r in rows]

    async def is_fed_admin(self, fed_id: str, user_id: int) -> bool:
        cursor = await self.conn.execute(
            "SELECT 1 FROM fed_admins WHERE fed_id = ? AND admin_id = ?",
            (fed_id, user_id),
        )
        return await cursor.fetchone() is not None

    async def fed_ban(
        self, fed_id: str, user_id: int, reason: str | None, banned_by: int
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO fed_bans (fed_id, user_id, reason, banned_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(fed_id, user_id) DO UPDATE SET
                reason = excluded.reason, banned_by = excluded.banned_by,
                created_at = excluded.created_at
            """,
            (fed_id, user_id, reason, banned_by, time.time()),
        )
        await self.conn.commit()

    async def fed_unban(self, fed_id: str, user_id: int) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM fed_bans WHERE fed_id = ? AND user_id = ?", (fed_id, user_id)
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def is_fed_banned(self, fed_id: str, user_id: int) -> aiosqlite.Row | None:
        cursor = await self.conn.execute(
            "SELECT * FROM fed_bans WHERE fed_id = ? AND user_id = ?",
            (fed_id, user_id),
        )
        return await cursor.fetchone()

    async def count_fed_bans(self, fed_id: str) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) as c FROM fed_bans WHERE fed_id = ?", (fed_id,)
        )
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    # ------------------------------------------------------------------
    # known_members (@admin ping va /tag uchun a'zolar ro'yxati)
    # ------------------------------------------------------------------

    async def upsert_known_member(
        self, chat_id: int, user_id: int, full_name: str | None, username: str | None
    ) -> None:
        now = time.time()
        await self.conn.execute(
            """
            INSERT INTO known_members (chat_id, user_id, full_name, username, last_seen, first_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                full_name = excluded.full_name,
                username = excluded.username,
                last_seen = excluded.last_seen
            """,
            (chat_id, user_id, full_name, username, now, now),
        )
        await self.conn.commit()

    async def get_known_member(
        self, chat_id: int, user_id: int
    ) -> aiosqlite.Row | None:
        cursor = await self.conn.execute(
            "SELECT * FROM known_members WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        return await cursor.fetchone()

    async def get_known_member_by_username(
        self, chat_id: int, username: str
    ) -> aiosqlite.Row | None:
        """
        @username orqali odamni qidiradi (bot ko'rgan a'zolar ro'yxatidan).
        Telegram Bot API'da @username -> user_id ni to'g'ridan-to'g'ri
        olishning tayyor metodi yo'q, shu sabab bot o'zi ko'rgan a'zolar
        (`known_members`) ichidan qidiramiz.
        """
        cursor = await self.conn.execute(
            "SELECT * FROM known_members WHERE chat_id = ? AND LOWER(username) = ?",
            (chat_id, username.lower()),
        )
        return await cursor.fetchone()

    async def remove_known_member(self, chat_id: int, user_id: int) -> None:
        await self.conn.execute(
            "DELETE FROM known_members WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        await self.conn.commit()

    async def list_known_members(
        self, chat_id: int, exclude_user_id: int | None = None
    ) -> list[aiosqlite.Row]:
        if exclude_user_id is not None:
            cursor = await self.conn.execute(
                "SELECT * FROM known_members WHERE chat_id = ? AND user_id != ?",
                (chat_id, exclude_user_id),
            )
        else:
            cursor = await self.conn.execute(
                "SELECT * FROM known_members WHERE chat_id = ?", (chat_id,)
            )
        return await cursor.fetchall()

    # ------------------------------------------------------------------
    # bot_promoted_admins (/adminber, /adminol tarixi)
    # ------------------------------------------------------------------

    async def add_bot_promoted_admin(
        self, chat_id: int, user_id: int, promoted_by: int
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO bot_promoted_admins (chat_id, user_id, promoted_by, promoted_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                promoted_by = excluded.promoted_by, promoted_at = excluded.promoted_at
            """,
            (chat_id, user_id, promoted_by, time.time()),
        )
        await self.conn.commit()

    async def remove_bot_promoted_admin(self, chat_id: int, user_id: int) -> bool:
        cursor = await self.conn.execute(
            "DELETE FROM bot_promoted_admins WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        await self.conn.commit()
        return cursor.rowcount > 0

    async def is_bot_promoted_admin(self, chat_id: int, user_id: int) -> bool:
        cursor = await self.conn.execute(
            "SELECT 1 FROM bot_promoted_admins WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        return await cursor.fetchone() is not None


db = Database(settings.db_path)
