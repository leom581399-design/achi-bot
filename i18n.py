"""
ACHI BOT - til tizimi (i18n).

Bot ikki tilda ishlaydi: o'zbek (Toshkent shevasi, standart) va rus.
Har bir guruh o'z tilini tanlaydi (DM panel yoki /language orqali).

Ishlash tartibi:
- `texts.py` dagi barcha KONSTANTALAR o'zbek tilidagi ASOSIY (default)
  matn hisoblanadi - hech narsa o'zgarmaydi, orqaga moslik saqlanadi.
- Shu fayldagi `RU` lug'ati esa faqat RUS TILIGA TARJIMA QILINGAN
  qismlarni o'z ichiga oladi (asosan DM boshqarish paneli - foydalanuvchi
  aynan shu joyni "tushunarsiz" deb bergan edi, shu sabab to'liq
  tarjima qilingan - va guruhda eng ko'p ko'rinadigan xabarlar).
- `tr(chat_id, "KEY", **kwargs)` chaqirilganda: avval guruh tilini
  (keshlangan holda) so'raymiz, agar "ru" bo'lsa va shu KEY uchun
  tarjima mavjud bo'lsa - o'shani qaytaramiz; aks holda (til "uz"
  bo'lsa, YOKI "ru" tarjimasi hali yozilmagan bo'lsa) `texts.py`dagi
  asosiy (o'zbek) matnni qaytaramiz. Shu sabab tarjima qilinmagan
  matnlar uchun bot XATOGA uchramaydi - shunchaki o'zbekcha ko'rsatadi.
"""
from __future__ import annotations

import texts
from database import db

SUPPORTED_LANGUAGES = ("uz", "ru")
LANGUAGE_NAMES = {"uz": "O'zbekcha", "ru": "Русский"}


async def get_lang(chat_id: int) -> str:
    lang = await db.get_chat_language(chat_id)
    return lang if lang in SUPPORTED_LANGUAGES else "uz"


def tr_sync(lang: str, key: str, **kwargs: object) -> str:
    """Til allaqachon ma'lum bo'lganda (masalan bir nechta matnni bitta
    chaqiruvda formatlash uchun) - DB so'rovisiz ishlaydi."""
    template = None
    if lang == "ru":
        template = RU.get(key)
    if template is None:
        template = getattr(texts, key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


async def tr(chat_id: int, key: str, **kwargs: object) -> str:
    lang = await get_lang(chat_id)
    return tr_sync(lang, key, **kwargs)


def get_lock_names(lang: str) -> dict[str, str]:
    """
    `LOCK_NAMES` lug'at (dict) bo'lgani uchun `tr_sync()`ning matn-
    formatlash mantiqiga to'g'ri kelmaydi - shu sabab alohida funksiya.
    """
    if lang == "ru":
        return RU.get("LOCK_NAMES", texts.LOCK_NAMES)
    return texts.LOCK_NAMES


# ------------------------------------------------------------------
# Rus tiliga tarjimalar
# ------------------------------------------------------------------
# MUHIM: bu yerda faqat "KEY": "tarjima" formatida yoziladi - format()
# placeholder'lari ({title}, {status} va h.k.) ASL matndagi bilan
# AYNAN BIR XIL nomda bo'lishi SHART (aks holda .format() KeyError
# beradi - lekin tr_sync buni ushlab, asl matnga qaytadi, shu sabab
# xato sezilmasdan "uz" ko'rsatilib qoladi - shunga ehtiyot bo'ling).

RU: dict[str, str] = {
    # --- Umumiy ---
    "START": (
        "Здравствуйте! Я ACHI BOT, помогу содержать вашу группу в порядке. "
        "Добавьте меня администратором в группу, и я начну работать.\n\n"
        "Чтобы настроить группу, напишите мне сюда /panel - всё управляется "
        "кнопками, писать команды в группе не обязательно.\n\n"
        "Список команд: /help."
    ),
    # --- DM panel: umumiy ---
    "PANEL_ONLY_DM": (
        "Эта команда работает только в личном чате со мной. "
        "Напишите мне сюда: {bot_username}"
    ),
    "PANEL_NOT_ADMIN_OF_THAT_GROUP": "Вы больше не администратор этой группы, доступ закрыт.",
    "PANEL_NO_GROUPS": (
        "Не найдено ни одной группы, где вы администратор. Добавьте меня "
        "администратором в свою группу - она появится здесь."
    ),
    "PANEL_PICK_GROUP": "Выберите группу для настройки:",
    "PANEL_GROUP_MENU_HEADER": "<b>{title}</b>\nЧто настроим?",
    "PANEL_MAIN_MENU_HEADER": "<b>{title}</b>\n{premium_line}\nЯзык: {language}\n\nЧто настроим?",
    "PANEL_PREMIUM_LINE_ACTIVE": "Статус: премиум активен",
    "PANEL_PREMIUM_LINE_NONE": "Статус: премиума нет",
    "PANEL_MODERATION_MENU_HEADER": "Настройки модерации:",
    "PANEL_SETTINGS_MENU_HEADER": "Настройки группы:",
    "PANEL_CONTENT_MENU_HEADER": "Фильтры, заметки и свои команды:",
    "PANEL_PREMIUM_CENTER_HEADER": "Премиум-центр - все мощные функции здесь:\n{status}",
    "PANEL_OTHER_MENU_HEADER": "Другие инструменты:",
    "PANEL_BTN_BACK": "Назад",
    "PANEL_BTN_TO_LIST": "К списку групп",
    "PANEL_BTN_LOCKS": "Блокировки",
    "PANEL_BTN_GREETINGS": "Приветствие",
    "PANEL_BTN_FILTERS": "Фильтры",
    "PANEL_BTN_NOTES": "Заметки",
    "PANEL_BTN_PERSONAL": "Свои команды",
    "PANEL_BTN_RULES": "Правила",
    "PANEL_BTN_PREMIUM": "Премиум",
    "PANEL_BTN_AI_MOD": "Умная модерация",
    "PANEL_BTN_REPORTS": "Отчёт",
    "PANEL_BTN_FEDERATION": "Федерация",
    "PANEL_BTN_ADMIN_TOOLS": "Администраторы",
    "PANEL_BTN_LANGUAGE": "Язык",
    "PANEL_BTN_STATS": "Статистика",
    "PANEL_BTN_ADD_NEW": "+ Добавить новое",
    "PANEL_BTN_MODERATION_MENU": "Модерация",
    "PANEL_BTN_SETTINGS_MENU": "Настройки",
    "PANEL_BTN_CONTENT_MENU": "Фильтры и заметки",
    "PANEL_BTN_PREMIUM_CENTER_MENU": "Премиум-центр",
    "PANEL_BTN_OTHER_MENU": "Другое",
    "PANEL_BTN_BADWORDS": "Запрещённые слова",
    "PANEL_BTN_SLOWMODE": "Ограничение скорости",
    "PANEL_BTN_WARNACTION": "Лимит предупреждений",
    "PANEL_BTN_FLOODLIMIT": "Лимит флуда",
    "PANEL_BTN_ANTIRAID": "Анти-рейд",
    "PANEL_BTN_NIGHTMODE": "Ночной режим",
    "PANEL_BTN_LINKWHITELIST": "Белый список ссылок",
    "PANEL_BTN_WARNEXPIRY": "Срок предупреждений",
    "PANEL_BTN_TEXTCAPTCHA": "Текстовая капча",
    "PANEL_BTN_AUTODELETE": "Авто-удаление ответов",
    "PANEL_BTN_SILENTMODE": "Тихий режим",
    "PANEL_BTN_VIP": "VIP участники",
    "PANEL_BTN_MODERATORS": "Модераторы",
    "PANEL_BTN_SCHEDULE": "Запланированное сообщение",
    "PANEL_BTN_DAILYREPORT": "Ежедневный отчёт",
    "PANEL_BTN_BACKUP": "Резервная копия",
    "PANEL_BTN_SET_WELCOME": "Изменить текст приветствия",
    "PANEL_BTN_SET_GOODBYE": "Изменить текст прощания",
    "PANEL_BTN_CAPTCHA": "Капча",
    "PANEL_BTN_AUTOAPPROVE": "Авто-приём заявок",
    "PANEL_BTN_CLEANSERVICE": "Чистка системных сообщений",
    "PANEL_BTN_EDIT_RULES": "Изменить правила",
    "PANEL_BTN_REPORT_TEXT": "Текстом",
    "PANEL_BTN_REPORT_PDF": "PDF",
    "PANEL_BTN_REPORT_CSV": "CSV (Excel)",
    "PANEL_LOCKS_HEADER": "Что заблокировать? (нажмите, чтобы включить/выключить)",
    "PANEL_GREETINGS_HEADER": "Настройки приветствия и новых участников:",
    "PANEL_ASK_WELCOME_TEXT": (
        "Напишите текст приветствия. {mention} будет заменено на имя "
        "пользователя.\nНапример: Привет, {mention}, добро пожаловать!"
    ),
    "PANEL_ASK_GOODBYE_TEXT": "Напишите текст прощания. Например: Прощай, {mention}!",
    "PANEL_ASK_FILTER": "Напишите слово и ответ так: слово | текст ответа",
    "PANEL_ASK_NOTE": "Напишите название и текст: название текст",
    "PANEL_ASK_PERSONAL": (
        "Напишите название команды и текст: название текст\n"
        "Например: hello Добро пожаловать! Как дела?"
    ),
    "PANEL_ASK_RULES": "Напишите правила группы:",
    "PANEL_TEXT_EMPTY": "Пустой текст не принимается, попробуйте снова.",
    "PANEL_REMOVED_OK": "Удалено.",
    "PANEL_FILTERS_HEADER": "Фильтры группы (нажмите, чтобы удалить):",
    "PANEL_FILTERS_EMPTY": "Пока нет ни одного фильтра.",
    "PANEL_NOTES_HEADER": "Сохранённые заметки (нажмите, чтобы удалить):",
    "PANEL_NOTES_EMPTY": "Пока нет заметок.",
    "PANEL_PERSONAL_HEADER": "Созданные свои команды (нажмите, чтобы удалить):",
    "PANEL_PERSONAL_EMPTY": "Пока нет своих команд.",
    "PANEL_PREMIUM_HEADER": "Статус премиума:\n{status}",
    "PANEL_AI_MOD_HEADER": "Умная модерация - если включена, автоматически удаляю спам/оскорбления.",
    "PANEL_REPORTS_HEADER": "Какой отчёт и за какой период?",
    "PANEL_REPORT_PREPARING": "Готовлю, сейчас отправлю...",
    "PANEL_FEDERATION_NONE": "Эта группа не подключена ни к одной федерации.",
    "PANEL_ADMIN_TOOLS_HEADER": "Администраторы группы:",
    "PANEL_OPEN_BUTTON": "Открыть панель настроек",
    "PANEL_ONBOARDING_DM": (
        "Спасибо, что добавили меня в группу \"{chat_title}\". Теперь вы "
        "можете настроить группу отсюда (в личных сообщениях) кнопками - "
        "писать команды в группе не нужно. Нажмите кнопку ниже."
    ),
    "PANEL_ONBOARDING_GROUP_FALLBACK": (
        "Спасибо, что добавили в группу. Панель настроек теперь работает "
        "только в личных сообщениях, но я не смог вам написать - сначала "
        "напишите мне лично и нажмите \"Старт\": @{bot_username}. После "
        "этого кнопка ниже сразу откроет панель этой группы."
    ),
    "PANEL_LANGUAGE_HEADER": "Выберите язык бота для этой группы:",
    "PANEL_LANGUAGE_SET": "Язык изменён.",
    "PANEL_STATS_HEADER": "<b>Статистика группы</b>",
    "PANEL_BADWORDS_HEADER": "Запрещённые слова (нажмите, чтобы удалить):",
    "PANEL_BADWORDS_EMPTY": "Пока нет запрещённых слов.",
    "PANEL_ASK_BADWORD": "Напишите слово, которое нужно запретить:",
    "PANEL_ASK_SLOWMODE": "Напишите, через сколько секунд можно писать снова (например: 10). Отключить: 0",
    "PANEL_SLOWMODE_HEADER": "Ограничение скорости: {status}",
    "PANEL_WARNACTION_HEADER": "Что делать при достижении лимита предупреждений?",
    "PANEL_BTN_WARNACTION_BAN": "Банить",
    "PANEL_BTN_WARNACTION_MUTE": "Только мьютить",
    "PANEL_ASK_FLOODLIMIT": "Напишите лимит: число_сообщений секунды (например: 6 8). Отключить: off",
    "PANEL_FLOODLIMIT_HEADER": "Лимит флуда: {status}",
    "PANEL_ASK_ANTIRAID": "Напишите лимит: число_людей секунды (например: 5 60). Отключить: off",
    "PANEL_ANTIRAID_HEADER": "Анти-рейд: {status}",
    "PANEL_ASK_NIGHTMODE": "Напишите время: начало-конец (например: 23-7). Отключить: off",
    "PANEL_NIGHTMODE_HEADER": "Ночной режим: {status}",
    "PANEL_LINKWHITELIST_HEADER": "Разрешённые домены (нажмите, чтобы удалить):",
    "PANEL_LINKWHITELIST_EMPTY": "Пока нет доменов.",
    "PANEL_ASK_LINKWHITELIST": "Напишите домен (например: youtube.com):",
    "PANEL_ASK_WARNEXPIRY": "Напишите, через сколько дней предупреждения истекают. Отключить: 0",
    "PANEL_WARNEXPIRY_HEADER": "Срок предупреждений: {status}",
    "PANEL_ASK_TEXTCAPTCHA": "Напишите вопрос и ответ: вопрос | ответ. Отключить: off",
    "PANEL_TEXTCAPTCHA_HEADER": "Текстовая капча: {status}",
    "PANEL_ASK_AUTODELETE": "Напишите, через сколько секунд удалять ответы. Отключить: 0",
    "PANEL_AUTODELETE_HEADER": "Авто-удаление: {status}",
    "PANEL_SILENTMODE_HEADER": "Тихий режим: {status}",
    "PANEL_VIP_HEADER": "VIP участники (нажмите, чтобы убрать):",
    "PANEL_VIP_EMPTY": "Пока нет VIP.",
    "PANEL_ASK_VIP": "Напишите username или ID добавляемого пользователя:",
    "PANEL_MODERATORS_HEADER": "Модераторы (нажмите, чтобы убрать):",
    "PANEL_MODERATORS_EMPTY": "Пока нет модераторов.",
    "PANEL_ASK_MODERATOR": "Напишите username или ID добавляемого пользователя:",
    "PANEL_SCHEDULE_HEADER": "Запланированные сообщения (нажмите, чтобы удалить):",
    "PANEL_SCHEDULE_EMPTY": "Пока нет запланированных сообщений.",
    "PANEL_ASK_SCHEDULE": "Напишите время и текст: час:минута текст (например: 09:00 Доброе утро!)",
    "PANEL_ASK_DAILYREPORT": "Напишите час (0-23) для ежедневного отчёта. Отключить: off",
    "PANEL_DAILYREPORT_HEADER": "Ежедневный отчёт: {status}",
    "PANEL_STATUS_ON": "включено",
    "PANEL_STATUS_OFF": "отключено",
    "WARNACTION_REQUIRES_PREMIUM": "Эта настройка - премиум функция.",
    "WARNACTION_SET": "При лимите теперь будет: \"{action}\".",
    "NIGHTMODE_REQUIRES_PREMIUM": "Ночной режим - премиум функция.",
    "NIGHTMODE_ON": "Ночной режим включён: {start}:00 - {end}:00 группа закрывается автоматически.",
    "NIGHTMODE_OFF": "Ночной режим отключён.",
    "FLOODLIMIT_REQUIRES_PREMIUM": "Настройка лимита флуда - премиум функция.",
    "FLOODLIMIT_SET": "Лимит флуда установлен: {limit} сообщений / {window} секунд.",
    "FLOODLIMIT_OFF": "Лимит флуда для группы отключён, используется стандартный.",
    "WARNEXPIRY_REQUIRES_PREMIUM": "Срок предупреждений - премиум функция.",
    "WARNEXPIRY_SET": "Предупреждения теперь истекают через {days} дней.",
    "WARNEXPIRY_OFF": "Срок предупреждений сделан бесконечным.",
    "TEXTCAPTCHA_REQUIRES_PREMIUM": "Текстовая капча - премиум функция.",
    "TEXTCAPTCHA_SET": "Текстовая капча установлена.",
    "TEXTCAPTCHA_OFF": "Текстовая капча отключена.",
    "AUTODELETE_REQUIRES_PREMIUM": "Авто-удаление ответов - премиум функция.",
    "AUTODELETE_SET": "Ответы теперь удаляются через {seconds} секунд.",
    "AUTODELETE_OFF": "Режим авто-удаления отключён.",
    "SILENTMODE_REQUIRES_PREMIUM": "Тихий режим - премиум функция.",
    "SILENTMODE_ON": "Тихий режим включён: команды администратора тоже удаляются.",
    "SILENTMODE_OFF": "Тихий режим отключён.",
    "AUTOPIN_REQUIRES_PREMIUM": "Авто-закреп - премиум функция.",
    "AUTOPIN_ON": "Приветственные сообщения теперь закрепляются автоматически.",
    "AUTOPIN_OFF": "Авто-закреп отключён.",
    "ANTIRAID_REQUIRES_PREMIUM": "Защита от рейдов - премиум функция.",
    "ANTIRAID_ON": "Анти-рейд включён: если {threshold} человек за {window} секунд - группа закроется автоматически.",
    "ANTIRAID_OFF": "Анти-рейд отключён.",
    "VIP_REQUIRES_PREMIUM": "VIP функция - премиум.",
    "VIP_ADDED": "{target} теперь VIP - освобождён от лимитов warn/flood.",
    "MODERATOR_REQUIRES_PREMIUM": "Добавление модератора - премиум функция.",
    "MODERATOR_ADDED": "{target} теперь модератор: может warn/mute, но не может ban/kick.",
    "SCHEDULE_REQUIRES_PREMIUM": "Запланированные сообщения - премиум функция.",
    "SCHEDULE_ADDED": "Хорошо, буду отправлять это сообщение каждый день в {time}.",
    "LINKWHITELIST_REQUIRES_PREMIUM": "Белый список ссылок - премиум функция.",
    "LINKWHITELIST_ADDED": "\"{domain}\" больше не блокируется (даже если ссылки заблокированы).",
    "DAILYREPORT_REQUIRES_PREMIUM": "Ежедневный отчёт - премиум функция.",
    "DAILYREPORT_ON": "Каждый день в {hour}:00 буду отправлять отчёт сюда, в личные сообщения.",
    "DAILYREPORT_OFF": "Ежедневный автоотчёт отключён.",
    "BACKUP_REQUIRES_PREMIUM": "Резервная копия - премиум функция.",
    "BACKUP_GENERATING": "Готовлю резервную копию...",
    "BACKUP_CAPTION": "Резервная копия настроек группы (JSON).",
    # --- Personal / Filters / Notes / Rules (umumiy matnlar) ---
    "FILTER_SAVED": "Хорошо, теперь на слово \"{trigger}\" я буду отвечать так.",
    "FILTER_USAGE": "Напишите так: /filter слово | текст ответа",
    "NOTE_SAVED": "Заметка \"{name}\" сохранена. Вызов: #{name} или /get {name}.",
    "NOTE_USAGE": "Напишите так: /save название текст",
    "RULES_SET": "Правила группы сохранены.",
    "RULES_EMPTY": "Правила пока не заданы, администратор может задать через /setrules.",
    "RULES_HEADER": "<b>Правила группы:</b>\n\n",
    "WELCOME_SET": "Текст приветствия установлен. Вот как он будет выглядеть:",
    "GOODBYE_SET": "Текст прощания установлен.",
    "PERSONAL_USAGE": (
        "Напишите так: /personal название текст - например:\n"
        "/personal hello Добро пожаловать! Как дела?\n\n"
        "После этого если кто-то в группе напишет \"/hello\", я отвечу "
        "\"Добро пожаловать! Как дела?\".\n\n"
        "Удалить: /stoppersonal название\n"
        "Список: /personallist"
    ),
    "PERSONAL_BAD_NAME": (
        "Название команды должно состоять только из латинских букв, цифр "
        "и \"_\" (без пробелов, одно слово)."
    ),
    "PERSONAL_NAME_RESERVED": (
        "\"/{name}\" - это встроенная команда бота, её нельзя занять. "
        "Выберите другое название."
    ),
    "PERSONAL_ADDED": "Готово, теперь на \"/{name}\" я отправлю сохранённый текст.",
    # --- Premium ---
    "PREMIUM_STATUS_ACTIVE_UNTIL": "Премиум активен до {date}",
    "PREMIUM_STATUS_LIFETIME": "Премиум активен навсегда",
    "PREMIUM_STATUS_NONE": "Премиум не активирован",
    "PREMIUM_STATUS_SUPERADMIN": "Вы владелец бота, премиум-функции для вас всегда бесплатны.",
    "PREMIUM_BUTTON_30D": "30 дней — {price} Stars",
    "PREMIUM_BUTTON_LIFETIME": "Навсегда — {price} Stars",
    "PREMIUM_REQUIRED_EXPORT": "Экспорт CSV - премиум функция. Купите премиум через /premium.",
    "PREMIUM_REQUIRED_FILTER_LIMIT": (
        "В бесплатной группе можно добавить не более {limit} фильтров. "
        "Для безлимита купите /premium."
    ),
    "PREMIUM_REQUIRED_NOTE_LIMIT": (
        "В бесплатной группе можно сохранить не более {limit} заметок. "
        "Для безлимита купите /premium."
    ),
    # --- AI moderatsiya ---
    "AI_MODERATION_ON": (
        "Умная модерация включена. Теперь автоматически определяю и удаляю "
        "сообщения похожие на спам/оскорбления (администраторов не трогаю)."
    ),
    "AI_MODERATION_OFF": "Умная модерация отключена.",
    "AI_MODERATION_REQUIRES_PREMIUM": (
        "Умная модерация - премиум функция. Сначала купите премиум через /premium."
    ),
    # --- Lock nomlari ---
    "LOCK_NAMES": {
        "link": "ссылки",
        "photo": "фото",
        "video": "видео",
        "sticker": "стикеры",
        "forward": "переслан. сообщения",
        "gif": "GIF/анимации",
        "all": "всё",
    },
    # --- Staff / Federation / Report ---
    "STAFF_OWNER_LINE": "{mention} — владелец",
    "STAFF_ADMIN_LINE": "{mention} — администратор",
    "STAFF_EMPTY": "В этой группе не найдено администраторов, странно.",
    "FED_INFO": (
        "<b>Федерация: {name}</b>\n"
        "ID: <code>{fed_id}</code>\n"
        "Групп: {chats_count}\n"
        "Забанено: {bans_count}"
    ),
    "REPORT_EMPTY_PERIOD": "За этот период никаких действий не было, всё спокойно.",
}
