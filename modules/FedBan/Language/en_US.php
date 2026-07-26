<?php
return [
    // Creation
    'newfed_usage'    => '❌ Usage: /newfed <federation name>',
    'already_owner'   => '❌ You already own a federation. Delete it before creating another.',
    'newfed_done'     => "✅ Federation <b>:name</b> created!\n\n🆔 ID: <code>:fed_id</code>\n\nUse this ID to link groups with /joinfed.",

    // Join
    'joinfed_usage'   => '❌ Usage: /joinfed <fed_id>',
    'already_in_fed'  => '❌ This group is already in a federation. Use /leavefed first.',
    'fed_not_found'   => '❌ Federation not found. Check the ID.',
    'not_fed_owner'   => '⛔ Only the federation owner can link groups.',
    'joinfed_done'    => '✅ Group successfully linked to federation <b>:name</b>!',

    // Leave
    'not_in_fed'      => '❌ This group does not belong to any federation.',
    'leavefed_done'   => '✅ Group unlinked from federation <b>:name</b>.',

    // Fban
    'no_target'       => '❌ Reply to a message or provide a user ID.',
    'no_reason'       => 'No reason provided',
    'already_fbanned' => '❌ <b>:name</b> is already banned in this federation.',
    'fban_done'       => "🔨 <b>:name</b> was banned in federation <b>:fed</b>.\n📝 Reason: <i>:reason</i>\n🌐 Banned across <b>:chats</b> group(s).",

    // Unfban
    'not_fbanned'     => '❌ <b>:name</b> is not banned in this federation.',
    'unfban_done'     => '✅ <b>:name</b> was unbanned in federation <b>:fed</b>.',

    // Info
    'fedinfo'         => "🌐 <b>Federation: :name</b>\n🆔 ID: <code>:fed_id</code>\n👤 Owner: <code>:owner</code>\n📋 Groups: <b>:chats</b>\n🔨 Bans: <b>:bans</b>\n📅 Created: <i>:created</i>",
];
