<?php
return [
    'captcha_on'       => '✅ Captcha ativado. Tipo: <b>:type</b>.',
    'captcha_off'      => '✅ Captcha desativado.',
    'captcha_invalid'  => '❌ Uso: /captcha on|off|button|math|text',
    'captcha_button'   => "🔐 <b>:name</b>, bem-vindo(a)!\nClique no botão abaixo para provar que não é um robô.\nVocê tem <b>:timeout</b> segundos.",
    'captcha_math'     => "🔐 <b>:name</b>, bem-vindo(a)!\nResolva o cálculo para entrar:\n<b>:question = ?</b>\nVocê tem <b>:timeout</b> segundos.",
    'captcha_text'     => "🔐 <b>:name</b>, bem-vindo(a)!\nDigite a palavra abaixo para entrar:\n<code>:word</code>\nVocê tem <b>:timeout</b> segundos.",
    'captcha_passed'   => '✅ <b>:name</b> passou pelo captcha.',
    'captcha_failed'   => '❌ <b>:name</b> falhou no captcha e foi removido.',
    'captcha_expired'  => '⏰ <b>:name</b> não respondeu ao captcha a tempo e foi removido.',
    'btn_verify'       => '✅ Não sou um robô',
    'btn_wrong'        => '❌ Errado',
    'status_on'        => '📊 Captcha: <b>Ativo</b> (tipo: :type, timeout: :timeout s)',
    'status_off'       => '📊 Captcha: <b>Desativado</b>',
    'no_permission'    => '⛔ Você precisa ser administrador para usar este comando.',
    'group_only'       => '⛔ Este comando só funciona em grupos.',
];
