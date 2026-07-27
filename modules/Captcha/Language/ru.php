<?php
return [
    'captcha_on'       => '✅ Капча включена. Тип: <b>:type</b>.',
    'captcha_off'      => '✅ Капча отключена.',
    'captcha_invalid'  => '❌ Использование: /captcha on|off|button|math|text',
    'captcha_button'   => "🔐 <b>:name</b>, добро пожаловать!\nНажмите кнопку ниже, чтобы подтвердить, что вы не робот.\nУ вас <b>:timeout</b> секунд.",
    'captcha_math'     => "🔐 <b>:name</b>, добро пожаловать!\nРешите пример, чтобы войти:\n<b>:question = ?</b>\nУ вас <b>:timeout</b> секунд.",
    'captcha_text'     => "🔐 <b>:name</b>, добро пожаловать!\nВведите слово ниже, чтобы войти:\n<code>:word</code>\nУ вас <b>:timeout</b> секунд.",
    'captcha_passed'   => '✅ <b>:name</b> прошёл капчу.',
    'captcha_failed'   => '❌ <b>:name</b> не прошёл капчу и был удалён.',
    'captcha_expired'  => '⏰ <b>:name</b> не ответил на капчу вовремя и был удалён.',
    'btn_verify'       => '✅ Я не робот',
    'btn_wrong'        => '❌ Неверно',
    'status_on'        => '📊 Капча: <b>Активна</b> (тип: :type, время: :timeout сек)',
    'status_off'       => '📊 Капча: <b>Отключена</b>',
    'no_permission'    => '⛔ Для использования этой команды нужны права администратора.',
    'group_only'       => '⛔ Эта команда работает только в группах.',
];
