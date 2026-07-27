<?php
// ACHI BOT — ilova sozlamalari.
//
// owner_ids: botning egasi hisoblangan Telegram foydalanuvchi ID(lar)i.
// Bularga botning barcha buyruqlari (guruh admini bo'lmasalar ham)
// va cheklovsiz ruxsat beriladi (Permission::Owner - eng yuqori daraja).
//
// .env faylidagi OWNER_IDS (vergul bilan ajratilgan) mavjud bo'lsa, u
// ustunlik qiladi; bo'lmasa quyidagi standart qiymat ishlatiladi.
$envOwnerIds = getenv('OWNER_IDS');
$ownerIds = $envOwnerIds
    ? array_map('intval', array_filter(array_map('trim', explode(',', $envOwnerIds))))
    : [8539436212];

return [
    'owner_ids' => $ownerIds,
    'debug' => false,
    'timezone' => 'Asia/Tashkent',
    // Botning ASOSIY (standart) tili — o'zbek. Har bir guruh o'z tilini
    // /til (yoki /language) buyrug'i orqali "ru"ga o'zgartirishi mumkin -
    // bu holatda faqat shu guruh uchun rus tili ishlatiladi, boshqa
    // guruhlar hech narsa sezmaydi.
    'locale' => 'uz',
];