<?php
return [
    'usage'          => "🔒 Use: /lock <type>\nAvailable types: :types",
    'usage_unlock'   => "🔓 Use: /unlock <type> or /unlock all\nAvailable types: :types",
    'invalid_type'   => '❌ Invalid type: <code>:type</code>',
    'locked'         => '🔒 Lock <code>:type</code> enabled.',
    'already_locked' => '⚠️ Lock <code>:type</code> is already active.',
    'unlocked'       => '🔓 Lock <code>:type</code> removed.',
    'unlocked_all'   => '🔓 All locks have been removed.',
    'not_locked'     => '⚠️ Lock <code>:type</code> was not active.',
    'no_locks'       => '✅ No active locks in this group.',
    'list'           => '🔒 <b>Active locks:</b>\n:list',
];
