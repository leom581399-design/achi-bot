<?php
return [
    // Criação
    'newfed_usage'    => '❌ Uso: /newfed <nome da federação>',
    'already_owner'   => '❌ Você já é dono de uma federação. Exclua-a antes de criar outra.',
    'newfed_done'     => "✅ Federação <b>:name</b> criada!\n\n🆔 ID: <code>:fed_id</code>\n\nUse este ID para vincular grupos com /joinfed.",

    // Vincular grupo
    'joinfed_usage'   => '❌ Uso: /joinfed <fed_id>',
    'already_in_fed'  => '❌ Este grupo já pertence a uma federação. Use /leavefed primeiro.',
    'fed_not_found'   => '❌ Federação não encontrada. Verifique o ID.',
    'not_fed_owner'   => '⛔ Apenas o dono da federação pode vincular grupos.',
    'joinfed_done'    => '✅ Grupo vinculado à federação <b>:name</b> com sucesso!',

    // Desvincular
    'not_in_fed'      => '❌ Este grupo não pertence a nenhuma federação.',
    'leavefed_done'   => '✅ Grupo desvinculado da federação <b>:name</b>.',

    // Fban
    'no_target'       => '❌ Responda a uma mensagem ou forneça o ID do usuário.',
    'no_reason'       => 'Sem motivo',
    'already_fbanned' => '❌ <b>:name</b> já está banido nesta federação.',
    'fban_done'       => "🔨 <b>:name</b> foi banido na federação <b>:fed</b>.\n📝 Motivo: <i>:reason</i>\n🌐 Banido em <b>:chats</b> grupo(s).",

    // Unfban
    'not_fbanned'     => '❌ <b>:name</b> não está banido nesta federação.',
    'unfban_done'     => '✅ <b>:name</b> foi desbanido na federação <b>:fed</b>.',

    // Info
    'fedinfo'         => "🌐 <b>Federação: :name</b>\n🆔 ID: <code>:fed_id</code>\n👤 Dono: <code>:owner</code>\n📋 Grupos: <b>:chats</b>\n🔨 Banimentos: <b>:bans</b>\n📅 Criada em: <i>:created</i>",
];
