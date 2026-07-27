<?php
return [
    'usage'          => "🔒 Использование: /lock <тип>\nДоступные типы: :types",
    'usage_unlock'   => "🔓 Использование: /unlock <тип> или /unlock all\nДоступные типы: :types",
    'invalid_type'   => '❌ Неверный тип: <code>:type</code>',
    'locked'         => '🔒 Блокировка <code>:type</code> включена.',
    'already_locked' => '⚠️ Блокировка <code>:type</code> уже активна.',
    'unlocked'       => '🔓 Блокировка <code>:type</code> снята.',
    'unlocked_all'   => '🔓 Все блокировки сняты.',
    'not_locked'     => '⚠️ Блокировка <code>:type</code> не была активна.',
    'no_locks'       => '✅ В этой группе нет активных блокировок.',
    'list'           => '🔒 <b>Активные блокировки:</b>\n:list',
];
