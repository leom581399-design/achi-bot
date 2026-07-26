# 🤖 ACHI BOT

Telegram guruhlarini boshqarish uchun modulli **PHP 8.2+** framework asosida
qurilgan bot. Plugin-architecture (har bir funksiya alohida modul) va IoC
container asosida ishlaydi — yangi funksiya qo'shish uchun `Core`ga tegish
shart emas, `modules/` papkasiga yangi papka qo'yish kifoya.

## ✨ Asosiy imkoniyatlar

- **Moderatsiya:** `/ban` `/tban` `/unban` `/sban` `/banme` `/kick` `/kickme`
  `/mute` `/tmute` `/unmute` `/muteall` `/warn` `/unwarn` `/resetwarn` `/warns`
- **Guruh boshqaruvi:** `/lock` `/unlock` `/locks`, `/filter` `/stop` `/filters`,
  `/save` `/get` `/clear` `/notes`, `/setrules` `/rules` `/clearrules`,
  `/welcome` `/goodbye` `/cleanwelcome`
- **Anti-abuse:** Flood (`/setflood`, `/setfloodmode`), Captcha (tugma/matn/
  matematik), AntiSpam (CAS + havola cheklovi), AntiRaid (avtomatik reyd
  himoyasi), Approval (`/approval`, `/approve`, `/deny`)
- **Ilg'or funksiyalar:** Federatsiya (`/newfed`, `/fban`, `/fedinfo`),
  `/backup` / `/restore`, `/stats` / `/top`, web-dashboard (`public/dashboard`)
  va token bilan himoyalangan REST API (`public/api.php`)

## 🛠 O'rnatish

1. Talablar: PHP **8.2+**, kengaytmalar: `pdo`, `pdo_sqlite`, `mbstring`,
   `curl`, `json`, `openssl`. Composer bog'liqliklarini o'rnatish:

   ```bash
   composer install
   ```

2. `.env` faylini yarating:

   ```bash
   cp .env.example .env
   ```

3. `.env` faylini to'ldiring:
   - `TELEGRAM_BOT_TOKEN` — [@BotFather](https://t.me/BotFather)dan `/newbot`
     orqali oling. **Bu maydon MAJBURIY** — token kodning hech bir joyida
     standart (fallback) qiymat sifatida yozilmagan, xavfsizlik uchun faqat
     `.env` orqali beriladi.
   - `OWNER_IDS` — botning egasi hisoblangan Telegram foydalanuvchi ID(lar)i
     (vergul bilan ajratilgan). Bularga botning barcha buyruqlari va cheklovsiz
     ruxsat beriladi. Standart qiymat `app/config/app.php`da bor, lekin
     `.env`dagi qiymat ustunlik qiladi.
   - `DASHBOARD_PASSWORD_HASH` — web-panel (`public/dashboard`) uchun parol
     hash: `php -r "echo password_hash('parolingiz', PASSWORD_DEFAULT);"`
   - `PUBLIC_API_TOKEN` — REST API uchun token: `php -r "echo bin2hex(random_bytes(32));"`

4. Ma'lumotlar bazasi migratsiyalarini ishga tushiring:

   ```bash
   php console.php migrate
   ```

5. Botni ishga tushiring (long polling rejimi — lokal ishlatish uchun qulay):

   ```bash
   php run.php
   ```

   Yoki webhook rejimida ishlatish uchun (production uchun tavsiya etiladi):

   ```bash
   php console.php webhook:set https://your-domain.com/public/webhook.php
   ```

6. Botni guruhingizga qo'shing va **admin huquqlarini** bering (kamida:
   foydalanuvchilarni ban qilish, xabarlarni o'chirish, a'zolarni taklif
   qilish huquqlari).

## 🚂 Railway'ga deploy qilish

Repo Railway uchun tayyor (`Dockerfile` + `railway.json` bilan). Qadamlar:

1. [railway.app](https://railway.app)da hisob oching (GitHub orqali kirish tavsiya
   etiladi — repo'ga ruxsat berish osonlashadi).
2. **New Project → Deploy from GitHub repo** → `achi-bot` repongizni tanlang.
   Railway `Dockerfile`ni avtomatik topib, shu orqali build qiladi.
3. **Muhim:** SQLite fayli Railway'ning vaqtinchalik fayl tizimida har
   qayta deploy qilinganda o'chib ketadi — shu sabab **Postgres qo'shish
   tavsiya etiladi**: loyihaga **+ New → Database → PostgreSQL** qo'shing.
   Railway avtomatik `DATABASE_URL` o'zgaruvchisini yaratadi va botga
   ulaydi (kod buni allaqachon qo'llab-quvvatlaydi — qo'shimcha sozlash
   kerak emas).
4. Bot servisining **Variables** bo'limida quyidagilarni qo'shing:
   - `TELEGRAM_BOT_TOKEN` — @BotFather'dan olingan token
   - `OWNER_IDS` — `8539436212` (yoki o'zingiznikini kiriting)
   - (Postgres qo'shgan bo'lsangiz, `DATABASE_URL` Railway tomonidan
     avtomatik qo'shiladi — qo'lda kiritish kerak emas)
5. Deploy tugagach, **Logs** bo'limida `✅ Bot started: @sizning_bot_username`
   degan xabarni ko'rishingiz kerak — shu bot ishga tushgani va Telegram
   bilan bog'langanini bildiradi.
6. Bot **uzluksiz ishlaydigan jarayon** (long-polling) sifatida ishlaydi,
   HTTP so'rov kutmaydi — shu sabab Railway'da "Public Networking"
   (domain) yoqish shart emas.

## 🎨 Render'ga deploy qilish

Render'da **"Background Worker"** turini tanlash tavsiya etiladi (bot
HTTP server emas). Agar **"Web Service"** turini tanlagan bo'lsangiz
ham muammo emas — repo shunga ham moslashtirilgan:

1. [render.com](https://render.com)da **New → Web Service** (yoki
   **Background Worker**) → GitHub repongizni ulang.
2. **Runtime:** Docker (Render `Dockerfile`ni avtomatik topadi).
3. **Environment Variables** bo'limida qo'shing:
   - `TELEGRAM_BOT_TOKEN` — @BotFather tokeningiz
   - `OWNER_IDS` — `8539436212`
   - Postgres qo'shsangiz (**New → PostgreSQL**), Render avtomatik
     yaratgan "Internal Database URL"ni nusxalab, `DATABASE_URL`
     nomida qo'shing.
4. **"Web Service" tanlagan bo'lsangiz:** Render sizdan portni so'raydi
   yoki avtomatik `$PORT`ni beradi — bu haqida qo'shimcha sozlash shart
   emas, `docker-entrypoint.sh` buni o'zi avtomatik o'qiydi va bot bilan
   bir vaqtda juda kichik "sog'lom" javob beruvchi server ishga
   tushiradi (Render shu orqali servisni "tirik" deb biladi).
5. Deploy tugagach, **Logs**da `✅ Bot started: @...` xabarini
   ko'rishingiz kerak.

**Eslatma:** Render'ning **bepul** reja (Free tier)dagi Web Service'lari
odatda ~15 daqiqa harakatsiz qolgandan keyin "uxlab qoladi" va keyingi
so'rovda qayta uyg'onadi. Bizning holatda health-check serveri Render
tomonidan ichkarida davriy tekshirilib turadi, shu sabab odatda uxlab
qolmaydi — lekin agar shunday muammo sezsangiz, Render'ning to'lovli
"Starter" rejasiga o'tish yoki **Background Worker** turini tanlash
uzluksizlikni kafolatlaydi.

## 📁 Loyiha strukturasi

```
achi-bot/
├── run.php                # kirish nuqtasi — long polling
├── console.php            # kirish nuqtasi — CLI (migrate, webhook va h.k.)
├── composer.json
├── app/
│   ├── bootstrap/app.php
│   ├── config/             # app.php (owner_ids), telegram.php (bot_token)
│   └── Core/               # framework yadrosi — funksiya qo'shish uchun
│                            # tegish SHART EMAS
├── modules/                # har bir funksiya — alohida modul
│   ├── Ban/  Kick/  Mute/  Warn/  Notes/
│   ├── Locks/  Filters/  Reports/  Rules/  Welcome/
│   ├── Flood/  Captcha/  AntiSpam/  AntiRaid/  Approval/
│   ├── Backup/  FedBan/  Stats/  Admin/  Help/  Start/
├── public/
│   ├── webhook.php          # webhook kirish nuqtasi
│   ├── api.php              # REST API
│   └── dashboard/           # web-panel (parol bilan himoyalangan)
├── storage/                 # SQLite baza va cache (git'ga tushmaydi)
├── docs/                    # texnik hujjatlar (arxitektura, modullar va h.k.)
└── .env.example
```

## ❗ Eslatmalar

- Bot ishlashi uchun guruhda **admin** bo'lishi shart (ban/mute/xabar
  o'chirish huquqlari bilan).
- `.env` fayli **hech qachon** git'ga tushmasligi kerak (`.gitignore`da bor) —
  unda haqiqiy bot tokeni va parol hash saqlanadi.
- Ma'lumotlar bazasi (`storage/database.sqlite`) va loglar (`logs/`) serverga
  joylashda backup qilinishi tavsiya etiladi.

## 📚 Texnik hujjatlar

Batafsil arxitektura, modul yaratish qo'llanmasi, servislar, hodisalar
(events), ruxsatlar (permissions) va REST API haqida — `docs/` papkasiga
qarang (`docs/README.md`dan boshlang).
