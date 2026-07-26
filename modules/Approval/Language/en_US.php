<?php
return [
    'approval_on'       => '✅ Approval mode enabled. New members will be muted until approved.',
    'approval_off'      => '✅ Approval mode disabled.',
    'approval_invalid'  => '❌ Usage: /approval on|off',
    'pending_join'      => "🔔 <b>:name</b> joined the group and is awaiting approval.\nAdmins: use /approve or /deny to allow or remove.",
    'approved'          => '✅ <b>:name</b> was approved and can now participate.',
    'denied'            => '🚫 <b>:name</b> was denied and removed from the group.',
    'no_target'         => '❌ Reply to a message or provide @username or ID.',
    'cannot_approve_admin' => '⛔ No need to approve an administrator.',
    'approve_failed'    => '❌ Failed to approve. The user may have already left or does not need approval.',
    'deny_failed'       => '❌ Failed to deny.',
    'status_on'         => '📊 Approval: <b>Active</b>',
    'status_off'        => '📊 Approval: <b>Disabled</b>',
    'no_permission'     => '⛔ You need to be an administrator to use this command.',
    'group_only'        => '⛔ This command only works in groups.',
];
