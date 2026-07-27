<?php
return [
    // Yaratish
    'newfed_usage'    => '❌ Foydalanish: /newfed <federatsiya nomi>',
    'already_owner'   => '❌ Sizda allaqachon federatsiya bor. Yangisini yaratishdan oldin eskisini o\'chiring.',
    'newfed_done'     => "✅ <b>:name</b> federatsiyasi yaratildi!\n\n🆔 ID: <code>:fed_id</code>\n\nGuruhlarni bog'lash uchun shu ID'ni /joinfed bilan ishlatng.",

    // Qo'shilish
    'joinfed_usage'   => '❌ Foydalanish: /joinfed <fed_id>',
    'already_in_fed'  => '❌ Bu guruh allaqachon federatsiyaga a\'zo. Avval /leavefed ishlating.',
    'fed_not_found'   => '❌ Federatsiya topilmadi. ID\'ni tekshiring.',
    'not_fed_owner'   => '⛔ Faqat federatsiya egasi guruhlarni bog\'lashi mumkin.',
    'joinfed_done'    => '✅ Guruh <b>:name</b> federatsiyasiga muvaffaqiyatli bog\'landi!',

    // Chiqish
    'not_in_fed'      => '❌ Bu guruh hech qanday federatsiyaga tegishli emas.',
    'leavefed_done'   => '✅ Guruh <b>:name</b> federatsiyasidan chiqarildi.',

    // Fban
    'no_target'       => '❌ Xabarga reply qiling yoki foydalanuvchi ID kiriting.',
    'no_reason'       => 'Sabab ko\'rsatilmagan',
    'already_fbanned' => '❌ <b>:name</b> bu federatsiyada allaqachon banlangan.',
    'fban_done'       => "🔨 <b>:name</b> <b>:fed</b> federatsiyasida banlandi.\n📝 Sabab: <i>:reason</i>\n🌐 <b>:chats</b> ta guruhda banlandi.",

    // Unfban
    'not_fbanned'     => '❌ <b>:name</b> bu federatsiyada banlangan emas.',
    'unfban_done'     => '✅ <b>:name</b> <b>:fed</b> federatsiyasida bandan chiqarildi.',

    // Info
    'fedinfo'         => "🌐 <b>Federatsiya: :name</b>\n🆔 ID: <code>:fed_id</code>\n👤 Egasi: <code>:owner</code>\n📋 Guruhlar: <b>:chats</b>\n🔨 Banlar: <b>:bans</b>\n📅 Yaratilgan: <i>:created</i>",
];
