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
- **Sababsiz ban/mute/kick/warn qilib bo'lmaydi** — bot sababni so'raydi va
  bazaga saqlaydi (kim, kimni, nima uchun, qachon)
- `/lock`, `/unlock`, `/locks` — link, rasm, video, stiker, forward, gif
  taqiqlash

### Salomlashish va himoya
- `/setwelcome`, `/setgoodbye` — xush kelibsiz/xayrlashuv xabarlari
  (`{mention}` o'rniga ism qo'yiladi)
- `/cleanservice on|off` — "... guruhga qo'shildi/chiqdi" degan Telegram
  tizim xabarlarini avtomatik o'chirish
- `/captcha on|off` — yangi qo'shilganlar tugma bosmaguncha yoza olmaydi
  (90 soniya ichida bosmasa, avtomatik chiqarib yuboriladi)
- Guruhga **join request** (a'zolikka so'rov) kelsa, avtomatik qabul
  qilinadi

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
├── fonts/                 # PDF uchun Unicode shrift (kirill/lotin)
├── handlers/
│   ├── moderation.py     # ban/mute/warn/kick/lock
│   ├── greetings.py      # welcome/goodbye/captcha/join-request
│   ├── content.py        # filter/notes/rules (limit bilan)
│   ├── report.py         # /r, /report, /exportcsv, har soatlik hisobot
│   ├── premium.py        # /premium, Telegram Stars to'lov oqimi
│   └── federation.py     # /fnew, /fjoin, /fban va h.k.
├── requirements.txt
├── railway.json           # Railway deploy sozlamasi
├── Procfile                # muqobil ishga tushirish buyrug'i
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

## ❗ Eslatmalar

- Bot ishlashi uchun guruhda **admin** bo'lishi shart (ban/mute/xabar
  o'chirish huquqlari bilan).
- Profil rasmi hisobotga tushishi uchun foydalanuvchining Telegramda ochiq
  (barchaga ko'rinadigan) profil rasmi bo'lishi kerak — aks holda o'rniga
  "rasm yo'q" degan bo'sh joy chiqadi.
- Ma'lumotlar bazasi (`achi_bot.db`) va hisobot PDF fayllari (`reports/`)
  loyiha papkasida saqlanadi — serverga joylashda shu papkalarni backup
  qilishni unutmang.
