<?php
// Render (Web Service turi) uchun juda kichik "sog'lomlik" sahifasi.
//
// ACHI BOT o'zi HTTP server emas - u faqat Telegram bilan long-polling
// orqali gaplashadi. Render Web Service esa doim biror portni "tirik"
// deb ko'rishni kutadi, aks holda servisni "unhealthy" deb belgilaydi.
// Shu sabab bot fonda (background) ishlaydi, shu faylni esa PHP'ning
// o'z ichki serveri (`php -S`) alohida jarayonda ko'rsatib turadi -
// Render shu manzilga so'rov yuborib, "OK" javobini ko'radi va servisni
// sog'lom deb hisoblaydi.
header('Content-Type: text/plain; charset=utf-8');
echo "ACHI BOT ishlayapti (long-polling jarayoni fonda davom etmoqda).\n";
