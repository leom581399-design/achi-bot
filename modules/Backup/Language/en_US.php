<?php
return [
    'generating'         => '⏳ Generating group backup, please wait...',
    'caption'            => "📦 <b>Group Backup</b>\n📅 <i>:date</i>\n\n📝 Notes: <b>:notes</b>\n🔇 Filters: <b>:filters</b>\n⚠️ Warnings: <b>:warns</b>\n⚙️ Settings: <b>:settings</b>\n\nUse /restore replying to this file to restore.",
    'error'              => '❌ Error generating backup: <i>:msg</i>',

    'restore_no_file'    => '❌ Reply to a message containing a backup <code>.json</code> file.',
    'restore_invalid_file' => '❌ The file must have a <code>.json</code> extension.',
    'restoring'          => '⏳ Restoring group settings, please wait...',
    'restore_done'       => "✅ <b>Backup restored successfully!</b>\n\n⚙️ Settings: <b>:settings</b>\n📝 Notes: <b>:notes</b>\n🔇 Filters: <b>:filters</b>\n⚠️ Warnings: <b>:warns</b>\n🔨 Bans: <b>:bans</b>\n🔇 Mutes: <b>:mutes</b>\n📜 Rules: <b>:rules</b>",
    'restore_json_error' => '❌ The file is not valid JSON.',
    'restore_invalid'    => '❌ Invalid backup: <i>:msg</i>',
];
