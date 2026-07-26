<?php
return [
    'captcha_on'       => '✅ Captcha enabled. Type: <b>:type</b>.',
    'captcha_off'      => '✅ Captcha disabled.',
    'captcha_invalid'  => '❌ Usage: /captcha on|off|button|math|text',
    'captcha_button'   => "🔐 <b>:name</b>, welcome!\nClick the button below to prove you're not a robot.\nYou have <b>:timeout</b> seconds.",
    'captcha_math'     => "🔐 <b>:name</b>, welcome!\nSolve the calculation to enter:\n<b>:question = ?</b>\nYou have <b>:timeout</b> seconds.",
    'captcha_text'     => "🔐 <b>:name</b>, welcome!\nType the word below to enter:\n<code>:word</code>\nYou have <b>:timeout</b> seconds.",
    'captcha_passed'   => '✅ <b>:name</b> passed the captcha.',
    'captcha_failed'   => '❌ <b>:name</b> failed the captcha and was removed.',
    'captcha_expired'  => '⏰ <b>:name</b> did not respond to the captcha in time and was removed.',
    'btn_verify'       => '✅ I\'m not a robot',
    'btn_wrong'        => '❌ Wrong',
    'status_on'        => '📊 Captcha: <b>Active</b> (type: :type, timeout: :timeout s)',
    'status_off'       => '📊 Captcha: <b>Disabled</b>',
    'no_permission'    => '⛔ You need to be an administrator to use this command.',
    'group_only'       => '⛔ This command only works in groups.',
];
