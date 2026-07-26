<?php
// ACHI BOT — Telegram sozlamalari.
//
// Xavfsizlik uchun MUHIM: haqiqiy bot tokenini bu faylga yozmang.
// Token .env faylidan (TELEGRAM_BOT_TOKEN) o'qiladi - .env git'ga
// tushmaydi (.gitignore'da bor), shu sabab token repo ichida ochiq
// saqlanmaydi.
return [
    'bot_token' => getenv('TELEGRAM_BOT_TOKEN') ?: '',
    'parse_mode' => 'HTML',
];