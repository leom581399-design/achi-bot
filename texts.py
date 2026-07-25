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
    "Buyruqlarni bilish uchun /help yozing."
)

HELP = (
    "🌹 <b>ACHI BOT — buyruqlar ro'yxati</b>\n\n"
    "<b>👮 Moderatsiya:</b>\n"
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
    "<b>🔒 Qulflar:</b>\n"
    "/lock link|photo|video|sticker|forward|all\n"
    "/unlock link|photo|video|sticker|forward|all\n"
    "/locks - joriy qulflar holati\n\n"
    "<b>👋 Salomlashish:</b>\n"
    "/setwelcome [matn] - xush kelibsiz xabarini o'rnatish\n"
    "/setgoodbye [matn] - xayrlashuv xabarini o'rnatish\n"
    "/cleanservice on/off - \"...guruhga qo'shildi\" xabarlarini o'chirish\n"
    "/captcha on/off - yangi a'zolarga captcha talab qilish\n"
    "/autoapprove on/off - qo'shilish so'rovlarini avtomatik qabul qilish "
    "(standart: o'chirilgan, qo'lda tasdiqlanadi)\n\n"
    "<b>📝 Filtr va eslatmalar:</b>\n"
    "/filter so'z | javob - avtomatik javob o'rnatish\n"
    "/filters - barcha filtrlar ro'yxati\n"
    "/stopfilter so'z - filtrni o'chirish\n"
    "/save nom matn - eslatma saqlash\n"
    "#nom yoki /get nom - eslatmani chaqirish\n"
    "/notes - eslatmalar ro'yxati\n"
    "/setrules [matn] - guruh qoidalarini yozish\n"
    "/rules - qoidalarni ko'rish\n\n"
    "<b>📊 Hisobot:</b>\n"
    "/r - shu kunlik/soatlik hisobotni chatga chiqarish\n"
    "/report - hozirgina PDF hisobot tayyorlab beradi\n\n"
    "<b>⭐ Premium (Telegram Stars):</b>\n"
    "/premium - narxlar va joriy holatni ko'rish, xarid qilish\n"
    "/exportcsv - hisobotni CSV (Excel) ko'rinishida olish\n\n"
    "<b>🔗 Federatsiya (premium):</b>\n"
    "/fnew nom - federatsiya yaratish\n"
    "/fjoin fed_id - guruhni federatsiyaga qo'shish\n"
    "/fban, /funban, /finfo, /fleave\n\n"
    "<b>👥 Adminlik va chaqirish:</b>\n"
    "@admin yoki @admins - adminlarni chaqirish\n"
    "/adminber - kimnidir admin qilish (faqat guruh egasi)\n"
    "/adminol - adminlikdan olish (faqat guruh egasi)\n"
    "/tag [matn] - ko'rilgan barcha a'zolarni chaqirish\n"
    "/staff - guruh adminlari ro'yxati\n"
    "/info - foydalanuvchi profili (reply qilib)\n"
    "/achi - bot haqida ma'lumot\n\n"
    "<b>🔫 CS2 narxlari (agar yoqilgan bo'lsa):</b>\n"
    ".skin AK-47 | Redline - Steam Market'dagi narxini so'mda ko'rsatadi\n\n"
    "Savol-tavsiya bo'lsa, guruh adminlariga yozing-a 🌹"
)

NOT_ADMIN = "Buni faqat guruh adminlari qila oladi-a, aka/opa 🙂"
BOT_NOT_ADMIN = (
    "Meni birinchi admin qilib qo'ying, undan keyin ishlayman-ku! "
    "Ban/mute qilish huquqi kerak menga."
)
ONLY_IN_GROUP = "Bu buyruq faqat guruhda ishlaydi-a."
REPLY_NEEDED = (
    "Kimga nisbatan qilayotganingizni ko'rsating-da: xabariga reply qiling "
    "yoki @username/ID yozing."
)
CANT_ACT_ON_ADMIN = "Bu admin ekan-ku, unga tegmayman men 🙅"
CANT_ACT_ON_SELF = "O'zingizga o'zingiz nima qilasiz, aka? 😄"
USER_NOT_FOUND = "Bunday odamni topolmadim, tekshirib ko'ring-chi."

# ------------------------------------------------------------------
# Ban / mute / kick / warn - sabab so'rash (FSM)
# ------------------------------------------------------------------

ASK_REASON = (
    "Sababsiz {action} qila olmayman-a, tartib shunday! "
    "Sababini yozib yuboring (yoki /cancel bilan bekor qiling)."
)
ACTION_CANCELLED = "Xo'p bo'ladi, bekor qildim."

BAN_DONE = (
    "🚫 {target} banlandi.\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
TBAN_DONE = (
    "🚫 {target} {duration}ga banlandi.\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
UNBAN_DONE = "✅ {target} bandan chiqarildi. Endi qaytib kirishi mumkin."
MUTE_DONE = (
    "🔇 {target}ning ovozi o'chirildi.\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
TMUTE_DONE = (
    "🔇 {target} {duration}ga mute qilindi.\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
UNMUTE_DONE = "🔊 {target}ning ovozi qaytarildi, gaplashsin endi."
KICK_DONE = (
    "👋 {target} guruhdan chiqarib yuborildi (qaytib kirishi mumkin).\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
WARN_DONE = (
    "⚠️ {target}ga ogohlantirish berildi ({count}/{max_warns}).\n"
    "Sabab: {reason}\n"
    "Admin: {admin}"
)
WARN_LIMIT_REACHED = (
    "⚠️ {target} {max_warns} marta ogohlantirish oldi, shu sabab avtomatik "
    "banladim. Boshqacha bo'lmaydi, qoidaga rioya qilish kerak edi-a."
)
UNWARN_DONE = "Bir ogohlantirish qaytarib olindi, {target}da endi {count} ta qoldi."
NO_WARNS = "{target}da hech qanaqa ogohlantirish yo'q ekan."
WARNS_LIST_EMPTY = "{target}da ogohlantirish yo'q, toza ekan 👍"
WARNS_LIST_HEADER = "{target}ning ogohlantirishlari ({count}/{max_warns}):"
WARNS_LIST_ITEM = "{num}. {reason} — {admin} ({date})"

# ------------------------------------------------------------------
# Lock / unlock
# ------------------------------------------------------------------

LOCK_TYPE_UNKNOWN = (
    "Buni tanimadim-a. Mana shulardan birini yozing: "
    "link, photo, video, sticker, forward, gif, all"
)
LOCK_DONE = "🔒 Endi guruhda \"{lock_name}\" taqiqlandi."
UNLOCK_DONE = "🔓 \"{lock_name}\" endi ochiq, joylashtirish mumkin."
LOCKS_HEADER = "Joriy qulflar:"
LOCKS_EMPTY = "Hozircha hech narsa qulflanmagan."
LOCKED_CONTENT_REMOVED = (
    "{mention}, bu turdagi xabar bu yerda taqiqlangan, o'chirib yubordim-a."
)

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
    "Hormat, {mention}! Guruhimizga xush kelibsiz-a 🌹\n"
    "Qoidalarni bilish uchun /rules yozing, birga totuv yashaymiz."
)
DEFAULT_GOODBYE = "{mention} guruhdan chiqib ketdi. Xayr, aka/opa 👋"

WELCOME_SET = "Xush kelibsiz xabari o'rnatildi. Mana shunday chiqadi:"
GOODBYE_SET = "Xayrlashuv xabari o'rnatildi."

CAPTCHA_ON = "Captcha yoqildi. Endi yangi qo'shilganlar tugma bosishi kerak bo'ladi."
CAPTCHA_OFF = "Captcha o'chirildi."
CAPTCHA_PROMPT = (
    "{mention}, xush kelibsiz! Odam ekanligingizni bildirish uchun pastdagi "
    "tugmani bosing, aks holda {seconds} soniyadan keyin chiqarib yuboraman-a."
)
CAPTCHA_BUTTON = "✅ Men odamman"
CAPTCHA_PASSED = "Rahmat, {mention}! Endi guruhda erkin yozishingiz mumkin 🌹"
CAPTCHA_FAILED_KICK = (
    "{mention} captchani vaqtida bosmadi, shu sabab chiqarib yubordim. "
    "Qaytib kirib, tugmani bossa bo'ladi."
)
CAPTCHA_WRONG_USER = "Bu tugma siz uchun emas-ku, aka/opa 🙂"

CLEAN_SERVICE_ON = "\"Guruhga qo'shildi/chiqdi\" degan tizim xabarlari endi o'chiriladi."
CLEAN_SERVICE_OFF = "Tizim xabarlari endi o'chirilmaydi."

JOIN_REQUEST_ACCEPTED_LOG = (
    "✅ {mention} guruhga qo'shilish so'rovi avtomatik qabul qilindi."
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
RULES_HEADER = "📜 <b>Guruh qoidalari:</b>\n\n"

# ------------------------------------------------------------------
# Hisobot (/r va PDF)
# ------------------------------------------------------------------

REPORT_GENERATING = "Hisobotni tayyorlayapman, biroz kuting-a... 📊"
REPORT_EMPTY_PERIOD = "Bu davrda hech qanaqa amal bo'lmadi, hammasi tinch ekan 👍"
REPORT_CAPTION = (
    "📊 <b>ACHI BOT hisoboti</b>\n"
    "Davr: {period}\n"
    "Guruh: {chat_title}\n\n"
    "Jami amallar: {total}\n"
    "🚫 Ban: {ban_count}\n"
    "🔇 Mute: {mute_count}\n"
    "⚠️ Warn: {warn_count}\n"
    "👋 Kick: {kick_count}"
)
R_COMMAND_USAGE = (
    "Shunday yozing:\n"
    "/r soat - oxirgi 1 soatlik hisobot\n"
    "/r kun - bugungi hisobot\n"
    "/r @username - shu odamning tarixi"
)
R_TEXT_HEADER = "📋 <b>{period}</b> uchun amallar ({chat_title}):\n"
R_TEXT_ITEM = (
    "{num}. {icon} <b>{action}</b> — {target}\n"
    "    Sabab: {reason}\n"
    "    Admin: {admin} | {date}\n"
)


# ------------------------------------------------------------------
# Premium (Telegram Stars)
# ------------------------------------------------------------------

PREMIUM_INFO = (
    "⭐ <b>ACHI BOT Premium</b>\n\n"
    "Bepulda ham ko'p narsa qiladi bu bot, lekin premium bilan yana "
    "kuchliroq bo'ladi-a:\n\n"
    "🔗 Federatsiya — bir nechta guruhni bog'lab, umumiy ban ro'yxati\n"
    "📝 Cheksiz filter va eslatma (bepulda {free_filter_limit} tadan chegara)\n"
    "📁 CSV eksport — hisobotni Excel'da ochish uchun\n"
    "🚀 Va kelgusida qo'shiladigan boshqa imkoniyatlar\n\n"
    "<b>Narxlar:</b>\n"
    "30 kunlik — {price_30d} ⭐\n"
    "Umrbod — {price_lifetime} ⭐\n\n"
    "Joriy holat: {status}\n\n"
    "Xarid qilish uchun pastdagi tugmalardan birini bosing 👇"
)
PREMIUM_STATUS_ACTIVE_UNTIL = "✅ Premium yoqilgan, {date} gacha amal qiladi"
PREMIUM_STATUS_LIFETIME = "✅ Umrbod premium yoqilgan"
PREMIUM_STATUS_NONE = "❌ Premium yoqilmagan"
PREMIUM_STATUS_SUPERADMIN = "✅ Siz bot egasisiz, premium funksiyalar sizga har doim tekin 🌹"

PREMIUM_BUTTON_30D = "⭐ 30 kunlik — {price} ⭐"
PREMIUM_BUTTON_LIFETIME = "⭐ Umrbod — {price} ⭐"

PREMIUM_ONLY_IN_GROUP = "Premium xarid qilish faqat guruh ichida ishlaydi-a, shu yerdan /premium deb yozing."
PREMIUM_ONLY_ADMIN_CAN_BUY = "Faqat guruh adminlari premium xarid qila oladi-a."

INVOICE_TITLE_30D = "ACHI BOT Premium — 30 kun"
INVOICE_TITLE_LIFETIME = "ACHI BOT Premium — Umrbod"
INVOICE_DESC_30D = "Bu guruh uchun 30 kunlik premium: federatsiya, cheksiz filter/eslatma, CSV eksport."
INVOICE_DESC_LIFETIME = "Bu guruh uchun umrbod premium: federatsiya, cheksiz filter/eslatma, CSV eksport."

PAYMENT_SUCCESS = (
    "🎉 Rahmat! To'lov qabul qilindi, bu guruhga premium yoqildi.\n"
    "Reja: {plan}\n"
    "Endi federatsiya, cheksiz filter/eslatma va CSV eksportdan foydalanishingiz mumkin 🌹"
)

PREMIUM_REQUIRED_FEDERATION = (
    "🔒 Federatsiya - premium funksiya. Bu guruhda premium yo'q ekan, "
    "/premium yozib xarid qilishingiz mumkin (Telegram Stars orqali)."
)
PREMIUM_REQUIRED_EXPORT = (
    "🔒 CSV eksport - premium funksiya. /premium yozib, guruhga premium sotib olishingiz mumkin."
)
PREMIUM_REQUIRED_FILTER_LIMIT = (
    "🔒 Bepul guruhda {limit} tadan ortiq filtr qo'shib bo'lmaydi-a. "
    "Cheksiz filtr uchun /premium yozing."
)
PREMIUM_REQUIRED_NOTE_LIMIT = (
    "🔒 Bepul guruhda {limit} tadan ortiq eslatma saqlab bo'lmaydi-a. "
    "Cheksiz eslatma uchun /premium yozing."
)

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
    "✅ \"{name}\" federatsiyasi yaratildi.\n"
    "ID: <code>{fed_id}</code>\n"
    "Boshqa guruhlarda shu ID bilan /fjoin {fed_id} deb qo'shishingiz mumkin."
)
FED_ALREADY_OWN = "Sizda allaqachon \"{name}\" federatsiyasi bor ekan (ID: {fed_id})."
FED_NOT_FOUND = "Bunday federatsiya topilmadi, ID'ni tekshirib ko'ring."
FED_JOINED = "✅ Bu guruh \"{name}\" federatsiyasiga qo'shildi."
FED_JOIN_NOT_OWNER = "Faqat federatsiya egasi/adminlari guruhni qo'sha oladi-a."
FED_NOT_IN_ANY = "Bu guruh hech qanaqa federatsiyaga ulanmagan ekan."
FED_LEFT = "Bu guruh federatsiyadan chiqarildi."
FED_INFO = (
    "🔗 <b>Federatsiya: {name}</b>\n"
    "ID: <code>{fed_id}</code>\n"
    "Guruhlar soni: {chats_count}\n"
    "Banlanganlar soni: {bans_count}"
)
FED_BAN_DONE = "🚫 {target} federatsiyaning barcha guruhlarida banlandi.\nSabab: {reason}"
FED_UNBAN_DONE = "✅ {target} federatsiya banidan chiqarildi."
FED_NOT_BANNED = "Bu odam federatsiyada banlangan emas ekan."
FED_REQUIRES_PREMIUM = (
    "🔒 Federatsiya - premium funksiya. Avval /premium orqali guruhga "
    "premium sotib oling, keyin federatsiya yarata olasiz."
)

# ------------------------------------------------------------------
# CSV eksport
# ------------------------------------------------------------------

EXPORT_GENERATING = "CSV fayl tayyorlanyapti..."
EXPORT_CAPTION = "📁 CSV eksport — {period}, {chat_title}"


# ------------------------------------------------------------------
# @admin/@admins ping
# ------------------------------------------------------------------

ADMIN_PING_HEADER = "🆘 {caller} adminlarni chaqiryapti:"
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
    "✅ {target} endi admin! Ban, mute, xabar o'chirish va a'zo qo'shish "
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
ADMINOL_DONE = "✅ {target}dan adminlik olib tashlandi.\nBuni qilgan: {admin}"
ADMINOL_CANT_TARGET_OWNER = "Guruh egasidan adminlikni olib bo'lmaydi-a 😄"

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
TAG_STARTED = "📣 {count} kishi chaqirilyapti..."
TAG_ONLY_ADMIN = "Bu buyruqni faqat adminlar ishlata oladi-a, hammaboyni chaqirib yubormaylik."


# ------------------------------------------------------------------
# CS2 (Counter-Strike 2) narx qidiruvi - SKINPORT.COM (asosiy manba)
# ------------------------------------------------------------------

CS2_MARKET_USAGE = (
    "Shunday yozing: .skin ak47 redline yoki .oruzhiya awp asiimov\n"
    "To'liq yozish shart emas, men o'zim qaysi buyumni "
    "nazarda tutganingizni topib olishga harakat qilaman-a."
)
CS2_MARKET_SEARCHING = "🔍 \"{name}\" qidirilyapti, biroz kuting..."
CS2_MARKET_NOT_FOUND = (
    "Bunaqa buyum topolmadim-a. Boshqacha yozib ko'ring, masalan faqat "
    "qurol nomi va skin nomini yozing: .skin ak47 redline"
)
CS2_MARKET_RESULT = (
    "🔫 <b>{name}</b>\n\n"
    "💵 Narxi: <b>${usd}</b>\n"
    "💰 So'mda: <b>{uzs} so'm</b>\n"
    "🌐 Manba: {source}\n"
)
CS2_MARKET_RESULT_WITH_VOLUME = (
    "🔫 <b>{name}</b>\n\n"
    "💵 Narxi: <b>${usd}</b>\n"
    "💰 So'mda: <b>{uzs} so'm</b>\n"
    "📦 So'nggi 24 soatda sotilgan: {volume} ta\n"
    "🌐 Manba: {source}\n"
)
CS2_MARKET_SOURCE_LISSKINS = "SKINPORT.COM"
CS2_MARKET_SOURCE_STEAM = "Steam Community Market (zaxira manba)"
CS2_MARKET_ERROR = (
    "Narx manbalari hozir javob bermayapti, birozdan keyin qayta urinib ko'ring-a."
)
CS2_MARKET_COOLDOWN = "Sabr qiling-a, {seconds} soniyada bir marta so'rov yuborish mumkin."
CS2_MARKET_DISABLED = "CS2 narx qidiruvi bu guruhda o'chirilgan."

# Bir nechta mos natija topilganda - tanlash tugmalari
CS2_MULTI_RESULTS_HEADER = (
    "🔍 \"{query}\" bo'yicha bir nechta mos buyum topdim, qaysi birini "
    "so'ramoqchisiz?"
)
CS2_MULTI_RESULTS_EXPIRED = (
    "Bu tanlov eskirgan ekan, qaytadan .skin yoki .oruzhiya bilan yozing-a."
)

# ------------------------------------------------------------------
# /staff - adminlar ro'yxati
# ------------------------------------------------------------------

STAFF_HEADER = "👮 <b>{chat_title} - adminlar:</b>\n"
STAFF_OWNER_LINE = "👑 {mention} — egasi"
STAFF_ADMIN_LINE = "🛡 {mention} — admin"
STAFF_EMPTY = "Bu guruhda hech qanaqa admin topilmadi, qiziq ekan."

# ------------------------------------------------------------------
# /achi - bot haqida
# ------------------------------------------------------------------

ACHI_ABOUT = (
    "🌹 <b>ACHI BOT</b>\n\n"
    "Guruhingizni tozalab-yig'ishtirib turadigan, sof Toshkent shevasida "
    "gaplashadigan yordamchi botman.\n\n"
    "🛡 Moderatsiya, captcha, filtr, eslatma, hisobot (PDF/CSV)\n"
    "⭐ Premium: federatsiya, cheksiz filtr/eslatma (Telegram Stars orqali)\n"
    "🔫 CS2 skinlarining Steam Market narxini so'mda ko'rsataman\n\n"
    "Buyruqlar ro'yxati uchun /help yozing."
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
    "👤 <b>Foydalanuvchi profili</b>\n\n"
    "Ism: {mention}\n"
    "To'liq ism: {full_name}\n"
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
ACHI_GROUPS_HEADER = "📋 <b>Ishlab turgan guruhlar ({count} ta):</b>"
ACHI_GROUPS_ITEM = "• {title}{premium}"


CS2_MARKET_FALLBACK_NAME = (
    "{requested}\n"
    "⚠️ (bu buyum uchun narx topilmadi, o'rniga oddiy \"{resolved}\" narxi "
    "ko'rsatilyapti - taxminiy)"
)


AUTOAPPROVE_USAGE = "Shunday yozing: /autoapprove on yoki /autoapprove off"
AUTOAPPROVE_ON = (
    "✅ Endi guruhga qo'shilish so'rovlari avtomatik qabul qilinadi."
)
AUTOAPPROVE_OFF = (
    "🔒 Avtomatik qabul o'chirildi. Endi qo'shilish so'rovlarini o'zingiz "
    "qo'lda (Telegram'ning \"join requests\" bo'limidan) ko'rib chiqasiz-a."
)
