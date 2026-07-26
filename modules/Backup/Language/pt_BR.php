<?php
return [
    'generating'         => '⏳ Gerando backup do grupo, aguarde...',
    'caption'            => "📦 <b>Backup do Grupo</b>\n📅 <i>:date</i>\n\n📝 Notas: <b>:notes</b>\n🔇 Filtros: <b>:filters</b>\n⚠️ Advertências: <b>:warns</b>\n⚙️ Configurações: <b>:settings</b>\n\nUse /restore respondendo a este arquivo para restaurar.",
    'error'              => '❌ Erro ao gerar backup: <i>:msg</i>',

    'restore_no_file'    => '❌ Responda a uma mensagem que contenha um arquivo <code>.json</code> de backup.',
    'restore_invalid_file' => '❌ O arquivo deve ter extensão <code>.json</code>.',
    'restoring'          => '⏳ Restaurando configurações do grupo, aguarde...',
    'restore_done'       => "✅ <b>Backup restaurado com sucesso!</b>\n\n⚙️ Configurações: <b>:settings</b>\n📝 Notas: <b>:notes</b>\n🔇 Filtros: <b>:filters</b>\n⚠️ Advertências: <b>:warns</b>\n🔨 Bans: <b>:bans</b>\n🔇 Silenciamentos: <b>:mutes</b>\n📜 Regras: <b>:rules</b>",
    'restore_json_error' => '❌ O arquivo não é um JSON válido.',
    'restore_invalid'    => '❌ Backup inválido: <i>:msg</i>',
];
