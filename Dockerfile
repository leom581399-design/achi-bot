# ACHI BOT — Railway, Render va boshqa Docker asosidagi platformalar
# uchun.
#
# Bot uzluksiz ishlaydigan jarayon (long-polling, run.php) sifatida
# ishlaydi — HTTP server emas. Lekin Render kabi ba'zi platformalar
# "Web Service" turida doim biror $PORT'ni tinglashini kutadi - shu
# sabab docker-entrypoint.sh orqali botni FONDA ishga tushiramiz va
# bir vaqtda juda kichik "sog'lom" javob beruvchi HTTP server ham
# qo'shamiz (Railway'da "Worker" turi tanlansa, $PORT ishlatilmaydi -
# lekin health-check serveri baribir zararsiz ishlab turadi).
FROM php:8.2-cli

# Kerakli PHP extensionlar:
# - pdo_pgsql / pdo_sqlite — ma'lumotlar bazasi uchun (Railway'da
#   DATABASE_URL orqali Postgres ishlatish tavsiya etiladi, chunki
#   fayl tizimi Railway'da doimiy emas - SQLite qayta deploy
#   qilinganda yo'qoladi)
# - curl — TelegramClient Telegram Bot API bilan cURL orqali
#   gaplashadi (standart php:8.2-cli image'da bu YO'Q, o'rnatish
#   MAJBURIY, aks holda bot ishlamaydi)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        libcurl4-openssl-dev \
        unzip \
        git \
    && docker-php-ext-install pdo_pgsql pdo_sqlite curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

COPY composer.json composer.lock ./
RUN composer install --no-dev --no-interaction --optimize-autoloader --no-scripts

COPY . .

# storage/ va logs/ yozish huquqiga ega bo'lishi kerak (SQLite/cache/log
# fayllari uchun — Postgres ishlatilsa ham cache/log kerak bo'ladi).
RUN mkdir -p storage/cache logs && chmod -R 777 storage logs

RUN chmod +x docker-entrypoint.sh

# entrypoint bot (php run.php) va sog'lomlik-serverini (php -S) PARALEL
# ishga tushiradi - Render/Railway "Web Service" turida $PORT'ni
# tinglash talab qilinsa ham, "Worker" turida esa buning zarari yo'q.
CMD ["./docker-entrypoint.sh"]
