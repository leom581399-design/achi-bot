#!/bin/bash
# ACHI BOT — Render (Web Service) va shunga o'xshash platformalar uchun
# kirish nuqtasi.
#
# MUHIM: shebang aynan `bash` bo'lishi kerak (`sh` emas) - quyida
# ishlatilgan `wait -n` bash'ga xos buyruq, POSIX `sh`da mavjud emas
# ("Illegal option -n" xatosi shundan kelib chiqadi). php:8.2-cli
# image'i Debian asosida bo'lgani uchun bash standart o'rnatilgan.
#
# Muammo: ACHI BOT HTTP server emas, u Telegram bilan faqat
# long-polling orqali gaplashadi (php run.php - cheksiz sikl). Lekin
# Render "Web Service" turi doim biror $PORT'ni tinglashini kutadi,
# aks holda deploy'ni "unhealthy" deb belgilaydi va doim qayta ishga
# tushirib turadi.
#
# Yechim: ikkita jarayonni PARALEL ishga tushiramiz:
#   1) php run.php          — haqiqiy bot (Telegram bilan gaplashadi)
#   2) php -S 0.0.0.0:$PORT — juda kichik "men tirikman" javob beruvchi
#      server (public_health/index.php)
#
# Ikkisidan BIRI to'xtasa, butun konteyner to'xtaydi (`wait -n`) - shu
# orqali platforma buni "ishdan chiqdi" deb bilib, qayta ishga tushiradi
# (bot xatosiz "yolg'iz o'zi ishlab qolib ketishi"ning oldi olinadi).
set -e

PORT="${PORT:-8080}"

echo "[entrypoint] ACHI BOT (long-polling) fonda ishga tushirilyapti..."
php run.php &
BOT_PID=$!

echo "[entrypoint] Sog'lomlik-tekshiruv serveri 0.0.0.0:${PORT} portida ishga tushirilyapti..."
php -S "0.0.0.0:${PORT}" -t public_health &
HEALTH_PID=$!

wait -n "$BOT_PID" "$HEALTH_PID"
EXIT_CODE=$?
echo "[entrypoint] Jarayonlardan biri to'xtadi (kod: ${EXIT_CODE}), konteyner yopilyapti..."
exit "$EXIT_CODE"
