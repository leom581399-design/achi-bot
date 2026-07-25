# 🌹 ACHI BOT

Toshkent shevasida gaplashadigan, guruh/kanal boshqaruvi uchun Telegram bot.
`aiogram 3` + `SQLite` + `fpdf2` (PDF hisobot) + `APScheduler` (har soatlik
avtomatik vazifalar) asosida yozilgan.

## ✨ Asosiy imkoniyatlar

### Moderatsiya
- `/ban`, `/tban <muddat>`, `/unban`
- `/mute`, `/tmute <muddat>`, `/unmute`
- `/kick`
- `/warn`, `/unwarn`, `/warns` — 3 marta ogohlantirish yig'ilsa, avtomatik ban
- **Nishonni belgilashning 3 yo'li bor:**
  1. Xabarga **reply** qilib buyruq yozish (masalan reply qilib `/ban spam`)
  2. Buyruqda to'g'ridan-to'g'ri **raqamli Telegram ID** yozish (masalan
     `/ban 8387547842 spam qildi`) — bu odam hozir guruhda bo'lmasa ham
     ishlaydi, chunki Telegram bunday amallarni ID orqali qabul qiladi
  3. Buyruqda **@username** yozish (bot avval shu odamni ko'rgan bo'lishi
     kerak, chunki Telegram Bot API'da "@username → ID" ni topishning
     umumiy usuli yo'q)
- **Sabab ixtiyoriy** — yozmasangiz ham amal bajariladi, hisobotda "sabab:
  ko'rsatilmagan" deb yoziladi. Xohlasangiz nishondan keyin (yoki muddatdan
  keyin, `/tban`/`/tmute` uchun) sababni yozib qo'yishingiz mumkin
- `/lock`, `/unlock`, `/locks` — link, rasm, video, stiker, forward, gif
  taqiqlash

### Salomlashish va himoya
- `/setwelcome`, `/setgoodbye` — xush kelibsiz/xayrlashuv xabarlari
  (`{mention}` o'rniga ism qo'yiladi)
- `/cleanservice on|off` — "... guruhga qo'shildi/chiqdi" degan Telegram
  tizim xabarlarini avtomatik o'chirish
- `/captcha on|off` — yangi qo'shilganlar tugma bosmaguncha yoza olmaydi
  (90 soniya ichida bosmasa, avtomatik chiqarib yuboriladi)
- `/autoapprove on|off` — guruhga **join request** (a'zolikka so'rov)
  kelganda avtomatik qabul qilinsinmi yoki yo'q. **Standart holatda
  o'chirilgan** — admin ataylab yoqmaguncha, so'rovlar Telegram'ning o'z
  "join requests" bo'limida qolib, qo'lda ko'rib chiqiladi

### Filtr, eslatma, qoidalar
- `/filter so'z | javob`, `/filters`, `/stopfilter so'z`
- `/save nom matn`, `/get nom` yoki `#nom`, `/notes`, `/delnote nom`
- `/setrules matn`, `/rules`

### 📊 Hisobot (ACHI BOT'ning o'ziga xos qismi)
- `/r soat` — so'nggi 1 soatlik amallar (matn ko'rinishida, tez)
- `/r kun` — bugungi amallar
- `/r @username` yoki xabarga reply qilib `/r` — shu odamning butun tarixi
- `/report [soat|kun|hafta]` — chiroyli **PDF hisobot**, har bir amal uchun
  foydalanuvchining **profil rasmi**, ismi, sababi, admin kim ekanligi va
  vaqti bilan
- **Har soatda avtomatik** — bot har bir faol guruhga (agar shu soat ichida
  amal bo'lgan bo'lsa) PDF hisobotni o'zi yuboradi. Xohlasangiz
  `REPORT_CHAT_ID` ni `.env`ga yozib, hisobotning nusxasi alohida
  kanal/chatga ham tushishini sozlashingiz mumkin.

### ⭐ Premium (Telegram Stars orqali to'lov)

- `/premium` — narxlarni va joriy holatni ko'rish, tugma orqali xarid qilish
- To'lov **Telegram Stars** (⭐) orqali amalga oshiriladi — tashqi bank/karta
  integratsiyasi shart emas, hammasi Telegram ichida
- **Bepul guruhda:** filter/eslatma sonida chegara bor (standart: 5 tadan),
  federatsiya va CSV eksport yopiq
- **Premium guruhda:** cheksiz filter/eslatma, federatsiya, CSV eksport
- **Bot egasi (`SUPER_ADMINS`) uchun barcha premium funksiyalar QAYERDA
  BO'LMASIN har doim tekin** — hech qanday to'lov talab qilinmaydi
- Narxlar `config.py`da: 30 kunlik va umrbod reja (o'zgartirish mumkin)

### 🔗 Federatsiya (premium funksiya)

- `/fnew nom` — yangi federatsiya yaratish
- `/fjoin fed_id` — boshqa guruhni shu federatsiyaga qo'shish
- `/fban`, `/funban` — federatsiyaning BARCHA guruhlarida birdan ban/unban
- `/finfo`, `/fleave` — ma'lumot va federatsiyadan chiqish
- Federatsiyaga a'zo guruhga banlangan odam qo'shilishga urinsa, avtomatik
  chiqarib yuboriladi

### 👥 Adminlik va a'zolarni chaqirish

- **@admin** yoki **@admins** — guruhdagi barcha adminlarni "ping" qilib
  chaqiradi (spam bo'lmasligi uchun bitta odam 30 soniyada faqat bir marta
  chaqira oladi)
- `/adminber` — kimnidir (reply qilib yoki @username bilan) ACHI BOT
  orqali admin qiladi. **Faqat guruh EGASI (creator)** ishlata oladi —
  oddiy adminga berilmagan, aks holda "buzilgan" bitta admin cheksiz
  yangi admin yaratib, guruhni egallab olishi mumkin edi
- `/adminol` — ACHI BOT orqali berilgan adminlikni olib tashlaydi (faqat
  guruh egasi; Telegram orqali to'g'ridan-to'g'ri tayinlangan adminlarga
  tegmaydi - ularni faqat Telegram guruh sozlamalaridan olib tashlash
  mumkin)
- `/tag [matn]` — bot ko'rgan barcha a'zolarni (5 talik guruhlarga bo'lib,
  flood-limitiga tushmaslik uchun) chaqiradi. Admin buyrug'i.
- `/staff` — guruh adminlari ro'yxati (egasi va adminlar alohida)
- `/achi` — bot haqida qisqacha ma'lumot. **Bot egasi (`SUPER_ADMINS`)
  uchun** — bot qaysi guruhlarda ishlab turganining to'liq ro'yxatini
  ham ko'rsatadi (premium guruhlar ⭐ belgisi bilan)

### 🔫 CS2 (Counter-Strike 2) narx qidiruvi — SKINPORT.COM

- `.skin ak47 redline` yoki `.oruzhiya awp asiimov` — **to'liq nom yozish
  shart emas**, bot o'zi eng mos keladigan buyumni topib beradi (fuzzy
  qidiruv, ~20 ming CS2 buyumi bazasi asosida, `data_cs2_items.json.gz`)
- Bir nechta mos nom topilsa, tanlash uchun tugmalar chiqadi
- Narx birinchi navbatda **Skinport.com**'dan olinadi (asosiy manba —
  bu CS2 skinlar uchun **rasmiy hujjatlashtirilgan va avtorizatsiyasiz**
  ochiq API, https://docs.skinport.com/items), topilmasa avtomatik
  **Steam Community Market**'ga (zaxira manba) o'tadi — natija qaysi
  manbadan olinganini xabarda ko'rsatadi
- ⚠️ Bilib qo'yish kerak: har ikkala manba ham **rate-limit**ga ega
  (Skinport: 5 daqiqada 8 so'rov endpoint guruhi bo'yicha; Steam esa
  ayniqsa bulut/server IP manzillarini tez-tez vaqtincha bloklab
  turadi). Shu sabab Skinport'dan olingan narxlar ro'yxati xotirada
  10 daqiqa saqlanadi (`config.lis_skins_cache_ttl_sec`), shu bilan
  qayta-qayta so'rov yuborilib rate-limitga tushib qolmaydi. Agar
  narx "topilmadi" bo'lib chiqsa, Railway loglarida sababini (masalan
  Skinport/Steam qanday status kod qaytargani) ko'rishingiz mumkin.
- `USD_TO_UZS_RATE` (`.env`) orqali dollar-so'm kursini sozlash mumkin -
  bu **statik** qiymat (real vaqtdagi valyuta API ishlatilmagan, chunki
  bu qo'shimcha tashqi bog'liqlik va nosozlik nuqtasi bo'lardi), shu
  sabab vaqti-vaqti bilan qo'lda yangilab turishingiz tavsiya etiladi
- `CS2_MARKET_ENABLED=false` qilib bu funksiyani butunlay o'chirish mumkin
- Har foydalanuvchi uchun 5 soniyalik so'rov cheklovi bor (narx manbalarini
  haddan tashqari ko'p so'rov bilan bloklatib qo'ymaslik uchun)

### 👤 /info — foydalanuvchi profili

- Xabarga reply qilib `/info` yozing (yoki hech kimga reply qilmasdan
  yozsangiz, o'zingizning profilingiz chiqadi)
- Ism, username, Telegram ID, guruhdagi holati (admin/oddiy a'zo/mute/ban),
  botning bu odamni birinchi ko'rgan sanasi, ogohlantirishlar sonini
  ko'rsatadi

### 🛡️ Anti-flood

- Bir foydalanuvchi qisqa vaqt ichida (standart: 8 soniyada 6 tadan ortiq)
  xabar yozsa, avtomatik 10 daqiqaga mute qilinadi — sozlamalar
  `config.flood_message_limit` / `config.flood_time_window_sec`

## 🛠 O'rnatish

1. Talab qilinadigan paketlarni o'rnating (tavsiya: virtual environment):

   ```bash
   cd achi_bot
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. `.env` faylini yarating:

   ```bash
   cp .env.example .env
   ```

3. `.env` faylini to'ldiring:
   - `BOT_TOKEN` — [@BotFather](https://t.me/BotFather)'dan `/newbot` orqali
     oling. **Eslatma:** `config.py` ichida standart (fallback) token allaqachon
     yozilgan, shu sabab `.env` yaratmasangiz ham bot ishlaydi — lekin
     tokenni almashtirish kerak bo'lsa, shu yerga yangisini yozing, u
     ustunlik qiladi.
   - `SUPER_ADMINS` — sizning Telegram ID'ingiz (masalan
     [@userinfobot](https://t.me/userinfobot) orqali bilib olasiz), guruh
     admini bo'lmasangiz ham botning barcha buyruqlari **va premium
     funksiyalar** sizga har doim tekin ishlashi uchun
   - `REPORT_CHAT_ID` — ixtiyoriy, hisobotlarning nusxasi tushadigan chat

4. Botni ishga tushiring:

   ```bash
   python main.py
   ```

5. Botni guruhingizga qo'shing va **admin huquqlarini** bering (kamida:
   foydalanuvchilarni ban qilish, xabarlarni o'chirish, a'zolarni taklif
   qilish huquqlari).

## 🚀 Railway'ga deploy qilish

1. Ushbu papkani (`achi_bot/`) GitHub'ga push qiling (repo **xususiy**
   bo'lishi tavsiya etiladi, chunki .env orqali maxfiy ma'lumot sozlanadi).
2. [railway.app](https://railway.app)'da yangi loyiha yarating →
   **"Deploy from GitHub repo"** → shu repo'ni tanlang.
3. Railway avtomatik ravishda `requirements.txt`ni topib, Python muhitini
   o'rnatadi (`railway.json`da `NIXPACKS` builder ko'rsatilgan).
4. Railway loyihasining **Variables** bo'limiga kamida shuni qo'shing
   (token kod ichida standart sifatida bor, lekin Railway'da environment
   variable orqali boshqarish tavsiya etiladi):
   - `BOT_TOKEN` = BotFather'dan olingan token
   - `SUPER_ADMINS` = sizning Telegram ID'ingiz
   - (ixtiyoriy) `REPORT_CHAT_ID`, `DB_PATH`, `REPORTS_DIR`
5. Deploy tugagach, loglarda `"ACHI BOT ishga tushdi"` degan yozuvni
   ko'rsangiz — bot ishlab turibdi.

**Muhim:** Railway'da fayl tizimi har deploy'da tozalanishi mumkin (agar
persistent volume ulamagan bo'lsangiz), ya'ni SQLite bazasi (`achi_bot.db`)
va PDF fayllar qayta deploy qilinganda yo'qolishi mumkin. Uzoq muddatli
saqlash uchun Railway'da **Volume** qo'shib, `DB_PATH`/`REPORTS_DIR`ni shu
volume ichiga ko'rsating.

## 🚀 Fly.io'ga deploy qilish

**Muhim eslatma:** Bot HTTP server emas, Telegram bilan "long polling"
orqali gaplashadi. Fly.io standart holatda web-servis kutib, HTTP
health-check qiladi — agar bu sozlanmagan bo'lsa, deploy **"failed"**
bo'lib qoladi. Shu sabab loyihada tayyor `fly.toml` bor, unda ataylab
`[http_service]` bo'limi YO'Q (worker rejimi ishlatilgan).

1. `flyctl` CLI'ni o'rnating: `curl -L https://fly.io/install.sh | sh`
   (batafsil: [fly.io/docs/flyctl/install](https://fly.io/docs/flyctl/install/))
2. Kirish: `fly auth login`
3. Repo papkasiga o'ting va ilovani ro'yxatdan o'tkazing (bu bosqichda
   `fly.toml` allaqachon bor bo'lgani uchun `fly launch` so'ramaydi,
   to'g'ridan-to'g'ri shu nom bilan yaratadi; agar nom band bo'lsa,
   `fly.toml`dagi `app = "achi-bot"` qatorini o'zgartiring):

   ```bash
   fly apps create achi-bot
   ```

4. Ma'lumotlarni saqlash uchun doimiy disk (volume) yarating (SQLite baza
   va PDF/CSV fayllar shu yerda saqlanadi, aks holda har deploy'da
   o'chib ketadi):

   ```bash
   fly volumes create achi_data --size 1 --region ams
   ```

5. Kerakli maxfiy o'zgaruvchilarni sozlang (token kodda standart sifatida
   bor, lekin shu orqali almashtirish/qo'shish mumkin):

   ```bash
   fly secrets set SUPER_ADMINS=123456789
   ```

6. Deploy qiling:

   ```bash
   fly deploy
   ```

7. Loglarni kuzatish: `fly logs` — `"ACHI BOT ishga tushdi"` yozuvini
   ko'rsangiz, bot ishlab turibdi.

**Fly.io haqida bilish kerak bo'lgan narsa:** 2024-yil oktyabrdan boshlab
Fly.io "har doim bepul" tarifni olib tashlagan, endi **"Pay As You Go"**
(ishlatgan resursga qarab to'lash) tizimi ishlaydi va bank kartasi talab
qiladi. Bizning bot kabi kichik va yengil ilova odatda oylik bepul
limitga (~$5 grant) sig'ib ketadi, lekin "birinchi oy butunlay tekin"
degan kafolat endi yo'q — foydalanishga qarab kichik summa yechilishi
mumkin.

## 📁 Loyiha strukturasi

```
achi_bot/
├── main.py              # kirish nuqtasi, routerlarni yig'ish, scheduler
├── config.py            # sozlamalar (.env + standart bot tokeni + premium narxlari)
├── database.py           # SQLite bilan ishlash (aiosqlite)
├── texts.py              # Toshkent shevasidagi barcha matnlar
├── utils.py               # yordamchi funksiyalar (mention, admin tekshiruvi...)
├── states.py              # FSM holatlari (sabab so'rash uchun)
├── middlewares.py         # guruhni avtomatik ro'yxatga olish + anti-flood
├── pdf_report.py          # PDF hisobot generatori (fpdf2)
├── cs2_items.py            # CS2 buyum nomlari bazasi + fuzzy qidiruv
├── data_cs2_items.json.gz  # ~20 ming CS2 buyum nomi (siqilgan, ~85KB)
├── fonts/                 # PDF uchun Unicode shrift (kirill/lotin)
├── handlers/
│   ├── moderation.py     # ban/mute/warn/kick/lock
│   ├── greetings.py      # welcome/goodbye/captcha/join-request
│   ├── content.py        # filter/notes/rules (limit bilan)
│   ├── report.py         # /r, /report, /exportcsv, har soatlik hisobot
│   ├── premium.py        # /premium, Telegram Stars to'lov oqimi
│   ├── federation.py     # /fnew, /fjoin, /fban va h.k.
│   ├── admin_tools.py    # @admin ping, /adminber, /adminol, /tag, /staff, /achi, /info
│   └── cs2_market.py     # .skin/.oruzhiya - Skinport/Steam narx qidiruvi
├── requirements.txt
├── railway.json           # Railway deploy sozlamasi
├── Procfile                # muqobil ishga tushirish buyrug'i
├── Dockerfile              # Fly.io/Docker-asosidagi hostinglar uchun
├── fly.toml                # Fly.io deploy sozlamasi (worker rejimi)
└── .env.example
```

## ⚙️ Sozlash mumkin bo'lgan qiymatlar (`config.py`)

- `max_warns` — nechta ogohlantirishdan keyin avtomatik ban (standart: 3)
- `hourly_report_interval_hours` — hisobot qanchа soatda bir yuborilsin
  (standart: 1)
- `free_filter_limit` / `free_note_limit` — bepul guruhdagi chegara
  (standart: 5 tadan)
- `premium_30d_price_stars` / `premium_lifetime_price_stars` — Telegram
  Stars'dagi narx (standart: 150 va 500 ⭐)
- `usd_to_uzs_rate` — CS2 narxlarini so'mga aylantirish uchun kurs
  (`.env`dagi `USD_TO_UZS_RATE` orqali ham sozlanadi)
- `admin_ping_cooldown_sec` — @admin necha soniyada bir marta chaqirilishi
  mumkin (standart: 30)

## ❗ Eslatmalar

- Bot ishlashi uchun guruhda **admin** bo'lishi shart (ban/mute/xabar
  o'chirish huquqlari bilan).
- Profil rasmi hisobotga tushishi uchun foydalanuvchining Telegramda ochiq
  (barchaga ko'rinadigan) profil rasmi bo'lishi kerak — aks holda o'rniga
  "rasm yo'q" degan bo'sh joy chiqadi.
- Ma'lumotlar bazasi (`achi_bot.db`) va hisobot PDF fayllari (`reports/`)
  loyiha papkasida saqlanadi — serverga joylashda shu papkalarni backup
  qilishni unutmang.
