<?php
return [
    'antiraid_on'       => '✅ Anti-raid enabled. Limit: <b>:n</b> joins in <b>:window</b> s.',
    'antiraid_off_cmd'  => '✅ Anti-raid disabled.',
    'antiraid_invalid'  => '❌ Usage: /antiraid on|off|N (N = max joins to trigger)',
    'raid_detected'     => "🚨 <b>RAID DETECTED!</b>\nToo many joins in a short time. Raid mode active for <b>:duration</b> min.\nAction: <b>:action</b>",
    'raid_mode_active'  => '🛡️ Raid mode active. Action: <b>:action</b>. Remaining: <b>:remaining</b> s.',
    'raid_mode_ended'   => '✅ Raid mode ended automatically.',
    'setmode_ok'        => '✅ Raid action set to: <b>:action</b>.',
    'setmode_invalid'   => '❌ Invalid action. Use: ban, kick, mute.',
    'status_off'        => '📊 Anti-raid: <b>Disabled</b>',
    'status_on'         => "📊 Anti-raid: <b>Active</b>\n• Limit: <b>:threshold</b> joins/:window s\n• Action: <b>:action</b>",
    'no_permission'     => '⛔ You need to be an administrator to use this command.',
    'group_only'        => '⛔ This command only works in groups.',
];
