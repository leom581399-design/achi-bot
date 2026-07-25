"""
ACHI BOT - barcha foydalanuvchiga ko'rinadigan matnlar.

Botning "ohangi" sof Toshkent shevasida bo'lishi uchun barcha xabarlar
shu yerda to'plangan. Agar ohangni o'zgartirmoqchi bo'lsangiz, faqat
shu faylni tahrirlashingiz kifoya - qolgan kod ishlashda davom etadi.
"""

# ------------------------------------------------------------------
# Umumiy / start / help
# ------------------------------------------------------------------

START = (
    "Assalomu alaykum, aka/opa! ACHI BOT'man, guruhingizni tozalab-yig'ishtirib "
    "turaman-a. Meni guruhga admin qilib qo'shsangiz, ishga tushib ketaman.\n\n"
    "Guruhni sozlash uchun shu yerdan /panel deb yozing - tugmalar orqali "
    "hammasini boshqarasiz, guruh ichida buyruq yozish shart emas.\n\n"
    "Buyruqlarni bilish uchun /help yozing."
)

HELP = (
    "<b>ACHI BOT — buyruqlar ro'yxati</b>\n\n"
    "Guruhni endi shaxsiy xabarda (DM), tugmalar orqali sozlash mumkin: "
    "botga yozib /panel deb yuboring. Pastda esa guruh ichida yozadigan "
    "buyruqlar ro'yxati (ba'zilari orqaga moslik uchun qolgan, DM panel "
    "afzalroq).\n\n"
    "<b>Moderatsiya:</b>\n"
    "/ban - odamni banlash (reply qilib)\n"
    "/tban 1d - vaqtincha banlash\n"
    "/unban - bandan chiqarish\n"
    "/mute - ovozini o'chirish\n"
    "/tmute 2h - vaqtincha mute\n"
    "/unmute - mute'dan chiqarish\n"
    "/kick - guruhdan chiqarib yuborish (ban emas)\n"
    "/warn [sabab] - ogohlantirish berish\n"
    "/unwarn - oxirgi ogohlantirishni bekor qilish\n"
    "/warns - odamning nechta ogohlantirishi borligini ko'rish\n\n"
    "<b>Qulflar:</b>\n"
    "/lock link|photo|video|sticker|forward|all\n"
    "/unlock link|photo|video|sticker|forward|all\n"
    "/locks - joriy qulflar holati\n\n"
    "<b>Aqlli moderatsiya (premium):</b>\n"
    "/aimod on/off - spam/haqoratli xabarlarni avtomatik aniqlab o'chirish\n\n"
    "<b>Salomlashish:</b>\n"
    "/setwelcome [matn] - xush kelibsiz xabarini o'rnatish\n"
    "/setgoodbye [matn] - xayrlashuv xabarini o'rnatish\n"
    "/cleanservice on/off - \"...guruhga qo'shildi\" xabarlarini o'chirish\n"
    "/captcha on/off - yangi a'zolarga captcha talab qilish\n"
    "/autoapprove on/off - qo'shilish so'rovlarini avtomatik qabul qilish "
    "(standart: o'chirilgan, qo'lda tasdiqlanadi)\n\n"
    "<b>Filtr va eslatmalar:</b>\n"
    "/filter so'z | javob - avtomatik javob o'rnatish\n"
    "/filters - barcha filtrlar ro'yxati\n"
    "/stopfilter so'z - filtrni o'chirish\n"
    "/save nom matn - eslatma saqlash\n"
    "#nom yoki /get nom - eslatmani chaqirish\n"
    "/notes - eslatmalar ro'yxati\n"
    "/setrules [matn] - guruh qoidalarini yozish\n"
    "/rules - qoidalarni ko'rish\n\n"
    "<b>Personal (o'zingizning maxsus buyrug'ingiz):</b>\n"
    "/personal nom matn - shu nomda buyruq yaratish (masalan: "
    "/personal salom Xush kelibsiz, aka!), keyin guruhda kimdur /salom "
    "deb yozsa, o'sha matnni chiqarib beraman\n"
    "/stoppersonal nom - buyruqni o'chirish\n"
    "/personallist - yaratilgan buyruqlar ro'yxati\n\n"
    "<b>Hisobot:</b>\n"
    "/r - shu kunlik/soatlik hisobotni chatga chiqarish\n"
    "/report - hozirgina PDF hisobot tayyorlab beradi\n\n"
    "<b>Premium (Telegram Stars):</b>\n"
    "/premium - narxlar va joriy holatni ko'rish, xarid qilish\n"
    "/exportcsv - hisobotni CSV (Excel) ko'rinishida olish\n\n"
    "<b>Federatsiya (premium):</b>\n"
    "/fnew nom - federatsiya yaratish\n"
    "/fjoin fed_id - guruhni federatsiyaga qo'shish\n"
    "/fban, /funban, /finfo, /fleave\n\n"
    "<b>Bot egasi uchun:</b>\n"
    "/grantpremium 30d|lifetime - guruhga qo'lda premium berish\n"
    "/broadcast [matn] - barcha guruhlarga xabar yuborish\n\n"
    "<b>Adminlik va chaqirish:</b>\n"
    "@admin yoki @admins - adminlarni chaqirish\n"
    "/adminber - kimnidir admin qilish (faqat guruh egasi)\n"
    "/adminol - adminlikdan olish (faqat guruh egasi)\n"
    "/tag [matn] - ko'rilgan barcha a'zolarni chaqirish\n"
    "/staff - guruh adminlari ro'yxati\n"
    "/info - foydalanuvchi profili (reply qilib)\n"
    "/achi - bot haqida ma'lumot\n\n"
    "<b>CS2 narxlari (agar yoqilgan bo'lsa):</b>\n"
    ".skin AK-47 | Redline - Steam Market'dagi narxini so'mda ko'rsatadi\n\n"
    "Savol-tavsiya bo'lsa, guruh adminlariga yozing-a."
)

NOT_ADMIN = "Buni faqat guruh adminlari qila oladi-a, aka/opa."
BOT_NOT_ADMIN = (
    "Meni birinchi admin qilib qo'ying, undan keyin ishlayman-ku! "
    "Ban/mute qilish huquqi kerak menga."
)
ONLY_IN_GROUP = "Bu buyruq faqat guruhda ishlaydi-a."
REPLY_NEEDED = (
    "Kimga nisbatan qilayotganingizni ko'rsating-da: xabariga reply qiling "
    "yoki @username/ID yozing."
)
CANT_ACT_ON_ADMIN = "Bu admin ekan-ku, unga tegmayman men."
CANT_ACT_ON_SELF = "O'zingizga o'zingiz nima qilasiz, aka?"
USER_NOT_FOUND = "Bunday odamni topolmadim, tekshirib ko'ring-chi."

# ------------------------------------------------------------------
# Ban / mute / kick / warn - sabab va muddat
# ------------------------------------------------------------------

# Sabab yozilmasa shu matn ko'rsatiladi (sabab MAJBURIY EMAS - admin
# xohlasa yozadi, xohlamasa yozmaydi).
REASON_NOT_SPECIFIED = "ko'rsatilmagan"

DURATION_USAGE = (
    "Davomiylikni yozing, masalan: 1d, 2h, 30m (masalan: /tban 1d sabab)"
)
DURATION_INVALID = (
    "Davomiylik formati noto'g'ri-a. Masalan: 30m, 2h, 1d, 1w"
)

BAN_DONE = (
    "{target} banlandi.\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
TBAN_DONE = (
    "{target} {duration}ga banlandi.\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
UNBAN_DONE = "{target} bandan chiqarildi. Endi qaytib kirishi mumkin."
MUTE_DONE = (
    "{target}ning ovozi o'chirildi.\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
TMUTE_DONE = (
    "{target} {duration}ga mute qilindi.\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
UNMUTE_DONE = "{target}ning ovozi qaytarildi, gaplashsin endi."
KICK_DONE = (
    "{target} guruhdan chiqarib yuborildi (qaytib kirishi mumkin).\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
WARN_DONE = (
    "{target}ga ogohlantirish berildi ({count}/{max_warns}).\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
WARN_LIMIT_REACHED = (
    "{target} {max_warns} marta ogohlantirish oldi, shu sabab avtomatik "
    "banladim. Boshqacha bo'lmaydi, qoidaga rioya qilish kerak edi-a."
)
UNWARN_DONE = "Bir ogohlantirish qaytarib olindi, {target}da endi {count} ta qoldi."
NO_WARNS = "{target}da hech qanaqa ogohlantirish yo'q ekan."
WARNS_LIST_EMPTY = "{target}da ogohlantirish yo'q, toza ekan."
WARNS_LIST_HEADER = "{target}ning ogohlantirishlari ({count}/{max_warns}):"
WARNS_LIST_ITEM = "{num}. {reason} — {admin} ({date})"

# ------------------------------------------------------------------
# Lock / unlock
# ------------------------------------------------------------------

LOCK_TYPE_UNKNOWN = (
    "Buni tanimadim-a. Mana shulardan birini yozing: "
    "link, photo, video, sticker, forward, gif, all"
)
LOCK_DONE = "Endi guruhda \"{lock_name}\" taqiqlandi."
LOCK_DONE_NO_PERMISSION = (
    "\"{lock_name}\" taqiqlandi, LEKIN diqqat: menda hali xabar o'chirish "
    "(\"Delete Messages\") huquqi yo'q ekan - shu sabab taqiqlangan xabarlar "
    "kelsa ham o'chira olmayman-a. Guruh sozlamalaridan menga admin qilib, "
    "\"Delete messages\" huquqini yoqib bering, shundan keyin ishlayveradi."
)
UNLOCK_DONE = "\"{lock_name}\" endi ochiq, joylashtirish mumkin."
LOCK_DELETE_FAILED_NOTICE = (
    "Diqqat, adminlar: taqiqlangan turdagi xabar keldi, lekin menda "
    "o'chirish huquqi yo'q ekan - o'chira olmadim. Menga \"Delete messages\" "
    "admin huquqini bering, shundan keyin bunaqa xabarlarni avtomatik "
    "o'chiraveraman."
)
LOCKS_HEADER = "Joriy qulflar:"
LOCKS_EMPTY = "Hozircha hech narsa qulflanmagan."
LOCKED_CONTENT_REMOVED = (
    "{mention}, bu turdagi xabar bu yerda taqiqlangan, o'chirib yubordim-a."
)

# ------------------------------------------------------------------
# Personal - o'zingiz yaratadigan maxsus buyruq
# ------------------------------------------------------------------

PERSONAL_USAGE = (
    "Shunday yozing: /personal nom matn - masalan:\n"
    "/personal salom Xush kelibsiz, aka! Qandaysiz?\n\n"
    "Shundan keyin guruhda kimdur \"/salom\" deb yozsa, men \"Xush "
    "kelibsiz, aka! Qandaysiz?\" deb javob beraman.\n\n"
    "O'chirish uchun: /stoppersonal nom\n"
    "Ro'yxatni ko'rish uchun: /personallist"
)
PERSONAL_BAD_NAME = (
    "Buyruq nomi faqat lotin harflari, raqam va \"_\" belgisidan iborat "
    "bo'lishi kerak-a (bo'sh joysiz, bittа so'z)."
)
PERSONAL_NAME_RESERVED = (
    "\"/{name}\" - botning o'zining ichki buyrug'i ekan, buni band qilib "
    "bo'lmaydi-a. Boshqa nom tanlang."
)
PERSONAL_ADDED = (
    "Xo'p, endi \"/{name}\" deb yozilsa, men saqlangan matnni chiqarib "
    "beraman-a."
)
PERSONAL_REMOVED = "\"/{name}\" buyrug'i o'chirildi."
PERSONAL_NOT_FOUND = "Bunday buyruq ro'yxatda yo'q ekan."
PERSONAL_LIST_EMPTY = "Hozircha hech qanaqa \"personal\" buyruq yaratilmagan."
PERSONAL_LIST_HEADER = "Yaratilgan personal buyruqlar:"

# ------------------------------------------------------------------
# AI-yordamchi moderatsiya (premium)
# ------------------------------------------------------------------

AI_MODERATION_USAGE = "Shunday yozing: /aimod on yoki /aimod off"
AI_MODERATION_REQUIRES_PREMIUM = (
    "Aqlli moderatsiya - premium funksiya. Avval /premium orqali guruhga "
    "premium sotib olishingiz kerak."
)
AI_MODERATION_ON = (
    "Aqlli moderatsiya yoqildi. Endi spam/haqoratga o'xshagan xabarlarni "
    "avtomatik aniqlab o'chiraman-a (adminlarga tegmayman)."
)
AI_MODERATION_OFF = "Aqlli moderatsiya o'chirildi."
AI_MODERATION_REMOVED = "Bu xabarni o'chirdim - sabab: {reason}."

LOCK_NAMES = {
    "link": "havolalar",
    "photo": "rasmlar",
    "video": "videolar",
    "sticker": "stikerlar",
    "forward": "forward xabarlar",
    "gif": "GIF/animatsiyalar",
    "all": "hammasi",
}

# ------------------------------------------------------------------
# Flood
# ------------------------------------------------------------------

FLOOD_WARNING = (
    "{mention}, sekinroq yozing-a, tez-tez xabar tashlayapsiz, flood bo'ladi bu!"
)
FLOOD_MUTED = (
    "{mention} flood qilgani uchun 10 daqiqaga mute qilindi. Sekinroq bo'ling-a."
)

# ------------------------------------------------------------------
# Welcome / goodbye / captcha / join
# ------------------------------------------------------------------

DEFAULT_WELCOME = (
    "Hormat, {mention}! Guruhimizga xush kelibsiz-a.\n"
    "Qoidalarni bilish uchun /rules yozing, birga totuv yashaymiz."
)
DEFAULT_GOODBYE = "{mention} guruhdan chiqib ketdi. Xayr, aka/opa."

WELCOME_SET = "Xush kelibsiz xabari o'rnatildi. Mana shunday chiqadi:"
GOODBYE_SET = "Xayrlashuv xabari o'rnatildi."

CAPTCHA_ON = "Captcha yoqildi. Endi yangi qo'shilganlar tugma bosishi kerak bo'ladi."
CAPTCHA_OFF = "Captcha o'chirildi."
CAPTCHA_PROMPT = (
    "{mention}, xush kelibsiz! Odam ekanligingizni bildirish uchun pastdagi "
    "tugmani bosing, aks holda {seconds} soniyadan keyin chiqarib yuboraman-a."
)
CAPTCHA_BUTTON = "Men odamman"
CAPTCHA_PASSED = "Rahmat, {mention}! Endi guruhda erkin yozishingiz mumkin."
CAPTCHA_FAILED_KICK = (
    "{mention} captchani vaqtida bosmadi, shu sabab chiqarib yubordim. "
    "Qaytib kirib, tugmani bossa bo'ladi."
)
CAPTCHA_WRONG_USER = "Bu tugma siz uchun emas-ku, aka/opa."

CLEAN_SERVICE_ON = "\"Guruhga qo'shildi/chiqdi\" degan tizim xabarlari endi o'chiriladi."
CLEAN_SERVICE_OFF = "Tizim xabarlari endi o'chirilmaydi."

JOIN_REQUEST_ACCEPTED_LOG = (
    "{mention} guruhga qo'shilish so'rovi avtomatik qabul qilindi."
)

# ------------------------------------------------------------------
# Filter / notes / rules
# ------------------------------------------------------------------

FILTER_SAVED = "Xo'p, \"{trigger}\" so'ziga endi shu javobni beraman."
FILTER_USAGE = "Shunday yozing: /filter so'z | javob matni"
FILTER_REMOVED = "\"{trigger}\" filtri o'chirildi."
FILTER_NOT_FOUND = "Bunaqa filtr yo'q ekan."
FILTERS_EMPTY = "Hozircha hech qanaqa filtr yo'q."
FILTERS_HEADER = "Guruhdagi filtrlar:"

NOTE_SAVED = "\"{name}\" nomli eslatma saqlandi. #{name} yoki /get {name} deb chaqirasiz."
NOTE_USAGE = "Shunday yozing: /save nom matn"
NOTE_NOT_FOUND = "Bunaqa eslatma topilmadi."
NOTES_EMPTY = "Hozircha eslatma saqlanmagan."
NOTES_HEADER = "Saqlangan eslatmalar:"
NOTE_REMOVED = "\"{name}\" eslatmasi o'chirildi."

RULES_SET = "Guruh qoidalari saqlandi."
RULES_EMPTY = "Hali qoida qo'yilmagan ekan, admin /setrules bilan yozib qo'ysin."
RULES_HEADER = "<b>Guruh qoidalari:</b>\n\n"

# ------------------------------------------------------------------
# Hisobot (/r va PDF)
# ------------------------------------------------------------------

REPORT_GENERATING = "Hisobotni tayyorlayapman, biroz kuting-a..."
REPORT_EMPTY_PERIOD = "Bu davrda hech qanaqa amal bo'lmadi, hammasi tinch ekan."
REPORT_CAPTION = (
    "<b>ACHI BOT hisoboti</b>\n"
    "Davr: {period}\n"
    "Guruh: {chat_title}\n\n"
    "Jami amallar: {total}\n"
    "Ban: {ban_count}\n"
    "Mute: {mute_count}\n"
    "Warn: {warn_count}\n"
    "Kick: {kick_count}"
)
R_COMMAND_USAGE = (
    "Shunday yozing:\n"
    "/r soat - oxirgi 1 soatlik hisobot\n"
    "/r kun - bugungi hisobot\n"
    "/r @username - shu odamning tarixi"
)
R_TEXT_HEADER = "<b>{period}</b> uchun amallar ({chat_title}):\n"
R_TEXT_ITEM = (
    "{num}. <b>{action}</b> — {target}\n"
    "    Sabab: {reason}\n"
    "    Admin: {admin} | {date}\n"
)
# AI-yordamchi xulosa (premium) - hisobot oxiriga qo'shiladi, faqat AI
# sozlangan va ishlagan taqdirda.
R_AI_SUMMARY = "AI xulosasi: {summary}"


# ------------------------------------------------------------------
# Premium (Telegram Stars)
# ------------------------------------------------------------------

PREMIUM_INFO = (
    "<b>ACHI BOT Premium</b>\n\n"
    "Bepulda ham ko'p narsa qiladi bu bot, lekin premium bilan yana "
    "kuchliroq bo'ladi-a:\n\n"
    "- Federatsiya — bir nechta guruhni bog'lab, umumiy ban ro'yxati\n"
    "- Cheksiz filter va eslatma (bepulda {free_filter_limit} tadan chegara)\n"
    "- CSV eksport — hisobotni Excel'da ochish uchun\n"
    "- Aqlli moderatsiya va hisobot xulosasi (AI)\n\n"
    "<b>Narxlar:</b>\n"
    "30 kunlik — {price_30d} Stars\n"
    "Umrbod — {price_lifetime} Stars\n\n"
    "Joriy holat: {status}\n\n"
    "Xarid qilish uchun pastdagi tugmalardan birini bosing."
)
PREMIUM_STATUS_ACTIVE_UNTIL = "Premium yoqilgan, {date} gacha amal qiladi"
PREMIUM_STATUS_LIFETIME = "Umrbod premium yoqilgan"
PREMIUM_STATUS_NONE = "Premium yoqilmagan"
PREMIUM_STATUS_SUPERADMIN = "Siz bot egasisiz, premium funksiyalar sizga har doim tekin."

# Guruhda premium ALLAQACHON faol bo'lsa /premium yozilganda shu qisqa
# xabar ko'rsatiladi - narx/tarif QAYTA chiqmaydi (chunki sotib olingan
# narsani yana sotmoqchi bo'lganday ko'rinib, admin uchun g'alati/keraksiz
# edi - shu bug tuzatildi).
PREMIUM_ALREADY_ACTIVE = (
    "<b>ACHI BOT Premium</b>\n\n"
    "{status}\n\n"
    "Sizda quyidagi premium imkoniyatlar allaqachon ochiq:\n"
    "- Federatsiya — bir nechta guruhni bog'lab, umumiy ban ro'yxati\n"
    "- Cheksiz filter va eslatma\n"
    "- CSV eksport\n"
    "- /broadcast — barcha bot guruhlariga xabar yuborish\n\n"
    "Rahmat, akam/opam! Yana narx ko'rsatib o'tirmayman, allaqachon bor-ku."
)

PREMIUM_BUTTON_30D = "30 kunlik — {price} Stars"
PREMIUM_BUTTON_LIFETIME = "Umrbod — {price} Stars"

PREMIUM_ONLY_IN_GROUP = "Premium xarid qilish faqat guruh ichida ishlaydi-a, shu yerdan /premium deb yozing."
PREMIUM_ONLY_ADMIN_CAN_BUY = "Faqat guruh adminlari premium xarid qila oladi-a."

INVOICE_TITLE_30D = "ACHI BOT Premium — 30 kun"
INVOICE_TITLE_LIFETIME = "ACHI BOT Premium — Umrbod"
INVOICE_DESC_30D = "Bu guruh uchun 30 kunlik premium: federatsiya, cheksiz filter/eslatma, CSV eksport."
INVOICE_DESC_LIFETIME = "Bu guruh uchun umrbod premium: federatsiya, cheksiz filter/eslatma, CSV eksport."

PAYMENT_SUCCESS = (
    "Rahmat! To'lov qabul qilindi, bu guruhga premium yoqildi.\n"
    "Reja: {plan}\n"
    "Endi federatsiya, cheksiz filter/eslatma va CSV eksportdan foydalanishingiz mumkin."
)

# ------------------------------------------------------------------
# /grantpremium - bot egasi (super-admin) tomonidan qo'lda premium berish
# ------------------------------------------------------------------

GRANTPREMIUM_ONLY_SUPERADMIN = (
    "Bu buyruqni faqat bot egasi ishlata oladi-a."
)
GRANTPREMIUM_USAGE = (
    "Shunday yozing:\n"
    "/grantpremium 30d - joriy guruhga 30 kunlik premium berish "
    "(guruh ichida yozilsa)\n"
    "/grantpremium lifetime - joriy guruhga umrbod premium berish\n"
    "/grantpremium <guruh_id> 30d yoki lifetime - istalgan guruhga "
    "(guruh ID orqali, hatto boshqa joyda yozsangiz ham) premium berish\n\n"
    "Guruh ID'larni /achi buyrug'i orqali ko'rishingiz mumkin."
)
GRANTPREMIUM_BAD_CHAT_ID = "Guruh ID raqam bo'lishi kerak-a, masalan: -1001234567890"
GRANTPREMIUM_DONE = (
    "<b>{chat_title}</b> guruhiga {plan_label} premium berildi.\n"
    "Buni qilgan: bot egasi"
)
GRANTPREMIUM_ANNOUNCE = (
    "Diqqat! Bu guruhga ACHI BOT egasi tomonidan {plan_label} premium "
    "yoqildi. Endi federatsiya, cheksiz filter/eslatma, CSV eksport va "
    "/broadcast'dan foydalanishingiz mumkin."
)

PREMIUM_REQUIRED_FEDERATION = (
    "Federatsiya - premium funksiya. Bu guruhda premium yo'q ekan, "
    "/premium yozib xarid qilishingiz mumkin (Telegram Stars orqali)."
)
PREMIUM_REQUIRED_EXPORT = (
    "CSV eksport - premium funksiya. /premium yozib, guruhga premium sotib olishingiz mumkin."
)
PREMIUM_REQUIRED_FILTER_LIMIT = (
    "Bepul guruhda {limit} tadan ortiq filtr qo'shib bo'lmaydi-a. "
    "Cheksiz filtr uchun /premium yozing."
)
PREMIUM_REQUIRED_NOTE_LIMIT = (
    "Bepul guruhda {limit} tadan ortiq eslatma saqlab bo'lmaydi-a. "
    "Cheksiz eslatma uchun /premium yozing."
)

# --- /premiumber - bot egasi uchun DM'da qo'lda BEPUL premium berish ---

PREMIUMBER_ONLY_DM = (
    "Bu funksiya faqat botga shaxsiy xabarda (DM) ishlaydi-a. "
    "Botga shu yerdan yozing: {bot_username}"
)
PREMIUMBER_NO_CHATS = "Hozircha bot hech qaysi guruhda ko'rinmayapti."
PREMIUMBER_PICK_CHAT_HEADER = (
    "<b>Qaysi guruhga premium bermoqchisiz/olib tashlamoqchisiz?</b>\n"
    "(* - hozir premium yoqilgan guruhlar)"
)
PREMIUMBER_PICK_PLAN_HEADER = (
    "<b>{chat_title}</b>\n"
    "Hozirgi holat: {status}\n\n"
    "Nima qilamiz?"
)
PREMIUMBER_BTN_30D = "30 kunlik bepul berish"
PREMIUMBER_BTN_LIFETIME = "Umrbod bepul berish"
PREMIUMBER_BTN_REVOKE = "Premiumni bekor qilish"
PREMIUMBER_BTN_BACK = "Guruhlar ro'yxati"
PREMIUMBER_GRANTED_30D = "\"{chat_title}\" guruhiga 30 kunlik BEPUL premium berildi."
PREMIUMBER_GRANTED_LIFETIME = "\"{chat_title}\" guruhiga UMRBOD BEPUL premium berildi."
PREMIUMBER_REVOKED = "\"{chat_title}\" guruhining premiumi bekor qilindi."

# ------------------------------------------------------------------
# Federatsiya
# ------------------------------------------------------------------

FED_USAGE = (
    "Federatsiya buyruqlari:\n"
    "/fnew nom - yangi federatsiya yaratish\n"
    "/fjoin fed_id - joriy guruhni federatsiyaga qo'shish\n"
    "/fleave - joriy guruhni federatsiyadan chiqarish\n"
    "/finfo - federatsiya ma'lumoti\n"
    "/fban [sabab] - odamni butun federatsiya bo'yicha banlash\n"
    "/funban - odamni federatsiya banidan chiqarish"
)
FED_CREATED = (
    "\"{name}\" federatsiyasi yaratildi.\n"
    "ID: <code>{fed_id}</code>\n"
    "Boshqa guruhlarda shu ID bilan /fjoin {fed_id} deb qo'shishingiz mumkin."
)
FED_ALREADY_OWN = "Sizda allaqachon \"{name}\" federatsiyasi bor ekan (ID: {fed_id})."
FED_NOT_FOUND = "Bunday federatsiya topilmadi, ID'ni tekshirib ko'ring."
FED_JOINED = "Bu guruh \"{name}\" federatsiyasiga qo'shildi."
FED_JOIN_NOT_OWNER = "Faqat federatsiya egasi/adminlari guruhni qo'sha oladi-a."
FED_NOT_IN_ANY = "Bu guruh hech qanaqa federatsiyaga ulanmagan ekan."
FED_LEFT = "Bu guruh federatsiyadan chiqarildi."
FED_INFO = (
    "<b>Federatsiya: {name}</b>\n"
    "ID: <code>{fed_id}</code>\n"
    "Guruhlar soni: {chats_count}\n"
    "Banlanganlar soni: {bans_count}"
)
FED_BAN_DONE = "{target} federatsiyaning barcha guruhlarida banlandi.\nSabab: {reason}"
FED_UNBAN_DONE = "{target} federatsiya banidan chiqarildi."
FED_NOT_BANNED = "Bu odam federatsiyada banlangan emas ekan."
FED_REQUIRES_PREMIUM = (
    "Federatsiya - premium funksiya. Avval /premium orqali guruhga "
    "premium sotib oling, keyin federatsiya yarata olasiz."
)

# ------------------------------------------------------------------
# CSV eksport
# ------------------------------------------------------------------

EXPORT_GENERATING = "CSV fayl tayyorlanyapti..."
EXPORT_CAPTION = "CSV eksport — {period}, {chat_title}"


# ------------------------------------------------------------------
# @admin/@admins ping
# ------------------------------------------------------------------

ADMIN_PING_HEADER = "{caller} adminlarni chaqiryapti:"
ADMIN_PING_NO_ADMINS = "Bu guruhda hech qanaqa admin topilmadi ekan, qiziq."
ADMIN_PING_COOLDOWN = (
    "Sabr qiling-a, adminlarni {seconds} soniyada bir marta chaqirish mumkin."
)

# ------------------------------------------------------------------
# /adminber, /adminol (bot orqali admin qilish/olib tashlash)
# ------------------------------------------------------------------

ADMINBER_USAGE = (
    "Kimni admin qilishni ko'rsating: xabariga reply qilib /adminber yozing, "
    "yoki @username/ID bilan: /adminber @username"
)
ADMINBER_ONLY_OWNER = (
    "Bu buyruqni faqat guruh EGASI (creator) ishlata oladi-a, oddiy adminga "
    "bermaganman ataylab - xavfsizlik uchun."
)
ADMINBER_CANT_PROMOTE_ADMIN = "Bu odam allaqachon admin ekan-ku."
ADMINBER_DONE = (
    "{target} endi admin. Ban, mute, xabar o'chirish va a'zo qo'shish "
    "huquqlari berildi.\nBuni qilgan: {admin}"
)
ADMINOL_USAGE = (
    "Kimdan adminlikni olishni ko'rsating: xabariga reply qilib /adminol yozing, "
    "yoki @username/ID bilan: /adminol @username"
)
ADMINOL_ONLY_OWNER = (
    "Bu buyruqni faqat guruh EGASI (creator) ishlata oladi-a."
)
ADMINOL_NOT_BOT_PROMOTED = (
    "Bu odamni ACHI BOT admin qilmagan ekan (balki Telegram orqali to'g'ridan-to'g'ri "
    "admin qilingan) - shu sabab botdan olib tashlay olmayman, Telegram guruh "
    "sozlamalaridan o'zingiz olib tashlashingiz kerak bo'ladi."
)
ADMINOL_DONE = "{target}dan adminlik olib tashlandi.\nBuni qilgan: {admin}"
ADMINOL_CANT_TARGET_OWNER = "Guruh egasidan adminlikni olib bo'lmaydi-a."

# ------------------------------------------------------------------
# /tag - a'zolarni chaqirish
# ------------------------------------------------------------------

TAG_USAGE = (
    "/tag [matn] - guruhdagi barcha a'zolarni (bot ko'rib turgan) chaqiradi, "
    "xohlasangiz oldin matn qo'shing: /tag Assalomu alaykum, yig'ilishga marhamat"
)
TAG_NO_MEMBERS = (
    "Hozircha hech kimni chaqira olmayman - a'zolar guruhda yozgandan keyin "
    "ro'yxatga tushadi. Birozdan keyin qayta urinib ko'ring."
)
TAG_STARTED = "{count} kishi chaqirilyapti..."
TAG_ONLY_ADMIN = "Bu buyruqni faqat adminlar ishlata oladi-a, hammaboyni chaqirib yubormaylik."


# ------------------------------------------------------------------
# CS2 (Counter-Strike 2) narx qidiruvi - SKINPORT.COM (asosiy manba)
# ------------------------------------------------------------------

CS2_MARKET_USAGE = (
    "Shunday yozing: .skin ak47 redline yoki .oruzhiya awp asiimov\n"
    "To'liq yozish shart emas, men o'zim qaysi buyumni "
    "nazarda tutganingizni topib olishga harakat qilaman-a."
)
CS2_MARKET_SEARCHING = "\"{name}\" qidirilyapti, biroz kuting..."
CS2_MARKET_SEARCHING_RU = "Ищу \"{name}\", подождите немного..."
CS2_MARKET_NOT_FOUND = (
    "Bunaqa buyum topolmadim-a. Boshqacha yozib ko'ring, masalan faqat "
    "qurol nomi va skin nomini yozing: .skin ak47 redline"
)
CS2_MARKET_NOT_FOUND_RU = (
    "Не смог найти такой предмет. Попробуйте написать по-другому, "
    "например только название оружия и скина: .skin ak47 redline"
)
CS2_MARKET_RESULT = (
    "<b>{name}</b>\n\n"
    "Narxi: <b>${usd}</b>\n"
    "So'mda: <b>{uzs} so'm</b>\n"
    "{drop_line}"
    "Manba: {source}\n"
)
CS2_MARKET_RESULT_WITH_VOLUME = (
    "<b>{name}</b>\n\n"
    "Narxi: <b>${usd}</b>\n"
    "So'mda: <b>{uzs} so'm</b>\n"
    "So'nggi 24 soatda sotilgan: {volume} ta\n"
    "{drop_line}"
    "Manba: {source}\n"
)
CS2_MARKET_RESULT_RU = (
    "<b>{name}</b>\n\n"
    "Цена: <b>${usd}</b>\n"
    "В сумах: <b>{uzs} so'm</b>\n"
    "{drop_line}"
    "Источник: {source}\n"
)
CS2_MARKET_RESULT_WITH_VOLUME_RU = (
    "<b>{name}</b>\n\n"
    "Цена: <b>${usd}</b>\n"
    "В сумах: <b>{uzs} so'm</b>\n"
    "Продано за последние 24 часа: {volume} шт\n"
    "{drop_line}"
    "Источник: {source}\n"
)
CS2_MARKET_DROP_LINE = "Qayerdan tushadi: {drop_source}\n"
CS2_MARKET_DROP_LINE_RU = "Выпадает из: {drop_source}\n"
CS2_MARKET_SOURCE_LISSKINS = "LIS-SKINS.COM"
CS2_MARKET_SOURCE_SKINPORT = "SKINPORT.COM (zaxira manba)"
CS2_MARKET_SOURCE_SKINPORT_RU = "SKINPORT.COM (резервный источник)"
CS2_MARKET_SOURCE_STEAM = "Steam Community Market (zaxira manba)"
CS2_MARKET_SOURCE_STEAM_RU = "Steam Community Market (резервный источник)"
CS2_MARKET_ERROR = (
    "Narx manbalari hozir javob bermayapti, birozdan keyin qayta urinib ko'ring-a."
)
CS2_MARKET_COOLDOWN = "Sabr qiling-a, {seconds} soniyada bir marta so'rov yuborish mumkin."
CS2_MARKET_DISABLED = "CS2 narx qidiruvi bu guruhda o'chirilgan."

# Bir nechta mos natija topilganda - tanlash tugmalari
CS2_MULTI_RESULTS_HEADER = (
    "\"{query}\" bo'yicha bir nechta mos buyum topdim, qaysi birini "
    "so'ramoqchisiz?"
)
CS2_MULTI_RESULTS_EXPIRED = (
    "Bu tanlov eskirgan ekan, qaytadan .skin yoki .oruzhiya bilan yozing-a."
)

# ------------------------------------------------------------------
# /staff - adminlar ro'yxati
# ------------------------------------------------------------------

STAFF_HEADER = "<b>{chat_title} - adminlar:</b>\n"
STAFF_OWNER_LINE = "{mention} — egasi"
STAFF_ADMIN_LINE = "{mention} — admin"
STAFF_EMPTY = "Bu guruhda hech qanaqa admin topilmadi, qiziq ekan."

# ------------------------------------------------------------------
# /achi - bot haqida
# ------------------------------------------------------------------

ACHI_ABOUT = (
    "<b>ACHI BOT</b>\n\n"
    "Guruhingizni tozalab-yig'ishtirib turadigan, sof Toshkent shevasida "
    "gaplashadigan yordamchi botman.\n\n"
    "- Moderatsiya, captcha, filtr, eslatma, hisobot (PDF/CSV)\n"
    "- Premium: federatsiya, cheksiz filtr/eslatma, aqlli moderatsiya "
    "(Telegram Stars orqali)\n"
    "- CS2 skinlarining Steam Market narxini so'mda ko'rsataman\n\n"
    "Sozlash uchun DM panel: /panel\n"
    "Buyruqlar ro'yxati uchun /help yozing."
)

# Guruhda /achi buyrug'i berilganda chiqadigan yagona yozuv - FAQAT
# shu ro'yxat chiqishi kerak, boshqa hech nima (bot haqida matn,
# guruhlar ro'yxati va h.k.) QO'SHILMAYDI. MATN VA USERNAME'LAR ANIQ
# FOYDALANUVCHI BERGANIDEK, O'ZGARTIRMASDAN yozilgan - iltimos, keyingi
# tahrirlarda ham shu ro'yxatni aynan saqlagan holda o'zgartiring.
ACHI_GROUP_LINKS_ONLY = (
    "CS2 Skin - @AChi_Drop\n"
    "CS Community- @AChi_Chat\n"
    "Lis Skins - @AChi_Lisskins\n"
    "NFT News - @AChi_NFT\n"
    "NFT Community- @NFT_AChi\n"
    "PC savdo - @AChi_PC\n"
    "Mafia gruppa - @AChi_Mafia\n"
    "NFT rent - @AChi_Rent\n"
    "CS2 Rek - @AChi_Rek"
)



# ------------------------------------------------------------------
# /info - foydalanuvchi profili
# ------------------------------------------------------------------

INFO_USAGE = (
    "Kimning profilini ko'rsatishni bilmadim-a. Xabariga reply qiling, "
    "@username yozing yoki hech narsasiz /info deb o'zingizni ko'rasiz."
)
INFO_NO_USERNAME = "yo'q"
INFO_UNKNOWN_DATE = "noma'lum (men uni ko'rmaganman hali)"
INFO_RESULT = (
    "<b>Foydalanuvchi profili</b>\n\n"
    "Ism: {mention}\n"
    "Username: {username}\n"
    "ID: <code>{user_id}</code>\n"
    "Holati: {status}\n"
    "Birinchi ko'rilgan: {first_seen}\n"
    "Ogohlantirishlar: {warn_count}/{max_warns}"
)



# ------------------------------------------------------------------
# /achi - bot egasi uchun guruhlar ro'yxati
# ------------------------------------------------------------------

ACHI_NO_GROUPS = "Hozircha hech qanaqa guruhda ishlamayapman, qiziq ekan."
ACHI_GROUPS_HEADER = "<b>Ishlab turgan guruhlar ({count} ta):</b>"
ACHI_GROUPS_ITEM = "- {title}{premium}"


CS2_MARKET_FALLBACK_NAME = (
    "{requested}\n"
    "(bu buyum uchun narx topilmadi, o'rniga oddiy \"{resolved}\" narxi "
    "ko'rsatilyapti - taxminiy)"
)
CS2_MARKET_FALLBACK_NAME_RU = (
    "{requested}\n"
    "(цена для этого предмета не найдена, вместо неё показана цена "
    "обычной версии \"{resolved}\" - примерная)"
)


# ------------------------------------------------------------------
# /broadcast - bot egasi tomonidan barcha guruhlarga xabar yuborish
# ------------------------------------------------------------------

BROADCAST_ONLY_SUPERADMIN = "Bu buyruqni faqat bot egasi ishlata oladi-a."
BROADCAST_USAGE = (
    "Shunday yozing: /broadcast matn - shu xabarni bot ishlab turgan "
    "BARCHA guruhlarga yuboraman."
)
BROADCAST_STARTED = "{count} ta guruhga xabar yuborilyapti, biroz kuting..."
BROADCAST_DONE = "Yuborildi: {success} ta guruhga, {failed} tasiga yetmadi (bot chiqarilgan/bloklangan bo'lishi mumkin)."
BROADCAST_NO_CHATS = "Hozircha hech qanaqa guruhda ishlamayapman, yuboradigan joy yo'q ekan."
BROADCAST_MESSAGE_PREFIX = "<b>ACHI BOT e'loni:</b>\n\n"

# ------------------------------------------------------------------
# DM boshqarish paneli (handlers/panel.py)
# ------------------------------------------------------------------

PANEL_ONLY_DM = (
    "Bu buyruq faqat botga shaxsiy xabarda (DM) ishlaydi. "
    "Botga shu yerdan yozing: {bot_username}"
)
PANEL_NOT_ADMIN_OF_THAT_GROUP = "Siz bu guruhda endi admin emas ekansiz-a, kirisholmaysiz."
PANEL_NO_GROUPS = (
    "Sizni admin qilib qo'yilgan hech qanaqa guruh topilmadi. Meni "
    "guruhingizga admin qilib qo'shsangiz, shu yerda paydo bo'ladi."
)
PANEL_PICK_GROUP = "Qaysi guruhni sozlaymiz?"
PANEL_GROUP_MENU_HEADER = "<b>{title}</b>\nNimani sozlaymiz?"

PANEL_BTN_BACK = "Orqaga"
PANEL_BTN_TO_LIST = "Guruhlar ro'yxatiga"
PANEL_BTN_LOCKS = "Qulflar"
PANEL_BTN_GREETINGS = "Salomlashish"
PANEL_BTN_FILTERS = "Filtrlar"
PANEL_BTN_NOTES = "Eslatmalar"
PANEL_BTN_PERSONAL = "Personal"
PANEL_BTN_RULES = "Qoidalar"
PANEL_BTN_PREMIUM = "Premium"
PANEL_BTN_AI_MOD = "Aqlli moderatsiya"
PANEL_BTN_REPORTS = "Hisobot"
PANEL_BTN_FEDERATION = "Federatsiya"
PANEL_BTN_ADMIN_TOOLS = "Adminlar"
PANEL_BTN_ADD_NEW = "+ Yangi qo'shish"
PANEL_BTN_SET_WELCOME = "Xush kelibsiz matnini o'zgartirish"
PANEL_BTN_SET_GOODBYE = "Xayrlashuv matnini o'zgartirish"
PANEL_BTN_CAPTCHA = "Captcha"
PANEL_BTN_AUTOAPPROVE = "Avto qabul qilish"
PANEL_BTN_CLEANSERVICE = "Tizim xabarlarini tozalash"
PANEL_BTN_EDIT_RULES = "Qoidalarni o'zgartirish"
PANEL_BTN_REPORT_TEXT = "Matnli"
PANEL_BTN_REPORT_PDF = "PDF"
PANEL_BTN_REPORT_CSV = "CSV (Excel)"

PANEL_LOCKS_HEADER = "Qaysilarini taqiqlaymiz? (bosib yoqing/o'chiring)"
PANEL_GREETINGS_HEADER = "Salomlashish va yangi a'zolar sozlamalari:"
PANEL_ASK_WELCOME_TEXT = (
    "Xush kelibsiz xabarini yozing. {mention} o'rniga odamning ismi qo'yiladi.\n"
    "Masalan: Salom {mention}, guruhimizga xush kelibsiz!"
)
PANEL_ASK_GOODBYE_TEXT = "Xayrlashuv xabarini yozing. Masalan: Xayr, {mention}!"
PANEL_ASK_FILTER = "So'z va javobni shunday yozing: so'z | javob matni"
PANEL_ASK_NOTE = "Nomi va matnini yozing: nomi matn"
PANEL_ASK_PERSONAL = (
    "Buyruq nomi va matnini yozing: nomi matn\n"
    "Masalan: salom Xush kelibsiz, aka! Qandaysiz?"
)
PANEL_ASK_RULES = "Guruh qoidalarini yozing:"
PANEL_TEXT_EMPTY = "Bo'sh matn qabul qilib bo'lmaydi, qayta urinib ko'ring."
PANEL_REMOVED_OK = "O'chirildi."

PANEL_FILTERS_HEADER = "Guruhdagi filtrlar (bosib o'chirasiz):"
PANEL_FILTERS_EMPTY = "Hozircha filtr yo'q."
PANEL_NOTES_HEADER = "Saqlangan eslatmalar (bosib o'chirasiz):"
PANEL_NOTES_EMPTY = "Hozircha eslatma yo'q."
PANEL_PERSONAL_HEADER = "Yaratilgan personal buyruqlar (bosib o'chirasiz):"
PANEL_PERSONAL_EMPTY = "Hozircha personal buyruq yo'q."

PANEL_PREMIUM_HEADER = "Premium holati:\n{status}"
PANEL_AI_MOD_HEADER = "Aqlli moderatsiya - yoqilgan bo'lsa, spam/haqoratli xabarlarni avtomatik o'chiraman."
PANEL_REPORTS_HEADER = "Qaysi turdagi va qaysi davr uchun hisobot kerak?"
PANEL_REPORT_PREPARING = "Tayyorlanyapti, hozir yuboraman..."
PANEL_FEDERATION_NONE = "Bu guruh hech qanaqa federatsiyaga ulanmagan."
PANEL_ADMIN_TOOLS_HEADER = "Guruh adminlari:"

PANEL_OPEN_BUTTON = "Sozlash panelini ochish"
PANEL_ONBOARDING_DM = (
    "Rahmat, meni \"{chat_title}\" guruhiga qo'shdingiz. Endi guruhni "
    "shu yerdan (DM'da), tugmalar orqali sozlashingiz mumkin - guruh "
    "ichida buyruq yozish shart emas. Pastdagi tugmani bosing."
)
PANEL_ONBOARDING_GROUP_FALLBACK = (
    "Guruhga qo'shdingiz, rahmat. Sozlash paneli endi faqat DM orqali "
    "ishlaydi, lekin sizga shaxsiy xabar yubora olmadim - avval botga "
    "shaxsan yozib \"start\" bosishingiz kerak: @{bot_username}. "
    "Shundan keyin pastdagi tugma orqali to'g'ridan-to'g'ri shu guruh "
    "paneliga o'tkazib yuboraman."
)

AUTOAPPROVE_USAGE = "Shunday yozing: /autoapprove on yoki /autoapprove off"
AUTOAPPROVE_ON = (
    "Endi guruhga qo'shilish so'rovlari avtomatik qabul qilinadi."
)
AUTOAPPROVE_OFF = (
    "Avtomatik qabul o'chirildi. Endi qo'shilish so'rovlarini o'zingiz "
    "qo'lda (Telegram'ning \"join requests\" bo'limidan) ko'rib chiqasiz-a."
)
