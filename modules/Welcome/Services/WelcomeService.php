<?php
declare(strict_types=1);

namespace Modules\Welcome\Services;

use App\Core\Application;
use App\Core\Services\{SettingsService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * WelcomeService — gerencia mensagens de boas-vindas e despedida.
 *
 * Configurações por grupo (SettingsService, módulo 'Welcome'):
 *   welcome.enabled      bool   — padrão: true
 *   welcome.message      string — padrão: mensagem do sistema
 *   goodbye.enabled      bool   — padrão: false
 *   goodbye.message      string — padrão: mensagem do sistema
 *   cleanwelcome.enabled bool   — padrão: false (apaga a welcome anterior ao novo membro entrar)
 *   cleanwelcome.last_id int    — ID da última mensagem de boas-vindas enviada
 *
 * Variáveis suportadas no template:
 *   {first} {last} {full} {username} {mention} {id} {count} {chatname}
 */
class WelcomeService
{
    public function __construct(private readonly Application $app) {}

    // -------------------------------------------------------------------------
    // Welcome
    // -------------------------------------------------------------------------

    public function sendWelcome(int $chatId, array $user, Update $update): void
    {
        $settings = $this->app->make(SettingsService::class);

        $enabled = $settings->get($chatId, 'Welcome', 'welcome.enabled', default: true);
        if (!$enabled) return;

        $client   = $this->app->make(TelegramClient::class);
        $telegram = $this->app->make(TelegramService::class);

        // Apaga welcome anterior se cleanwelcome estiver ativo
        $clean   = $settings->get($chatId, 'Welcome', 'cleanwelcome.enabled', default: false);
        $lastId  = $settings->get($chatId, 'Welcome', 'cleanwelcome.last_id');
        if ($clean && $lastId) {
            try { $client->deleteMessage($chatId, $lastId); } catch (\Throwable) {}
        }

        $defaultMsg = "👋 Bem-vindo(a), {mention}!\nVocê é o membro #{count} de {chatname}.";
        $template   = $settings->get($chatId, 'Welcome', 'welcome.message', default: $defaultMsg);
        $text       = $this->renderTemplate($template, $user, $chatId, $telegram);

        try {
            $result = $client->sendMessage($chatId, $text, ['parse_mode' => 'HTML']);
            if ($clean) {
                $settings->set($chatId, 'Welcome', 'cleanwelcome.last_id', $result['result']['message_id'] ?? null);
            }
        } catch (\Throwable) {}
    }

    public function sendGoodbye(int $chatId, array $user, Update $update): void
    {
        $settings = $this->app->make(SettingsService::class);

        $enabled = $settings->get($chatId, 'Welcome', 'goodbye.enabled', default: false);
        if (!$enabled) return;

        $telegram   = $this->app->make(TelegramService::class);
        $defaultMsg = '👋 {mention} saiu do grupo.';
        $template   = $settings->get($chatId, 'Welcome', 'goodbye.message', default: $defaultMsg);
        $text       = $this->renderTemplate($template, $user, $chatId, $telegram);

        try {
            $this->app->make(TelegramClient::class)->sendMessage($chatId, $text, ['parse_mode' => 'HTML']);
        } catch (\Throwable) {}
    }

    // -------------------------------------------------------------------------
    // Settings helpers
    // -------------------------------------------------------------------------

    public function setWelcomeEnabled(int $chatId, bool $enabled): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Welcome', 'welcome.enabled', $enabled);
    }

    public function setWelcomeMessage(int $chatId, string $message): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Welcome', 'welcome.message', $message);
    }

    public function setGoodbyeEnabled(int $chatId, bool $enabled): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Welcome', 'goodbye.enabled', $enabled);
    }

    public function setGoodbyeMessage(int $chatId, string $message): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Welcome', 'goodbye.message', $message);
    }

    public function setCleanwelcome(int $chatId, bool $enabled): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Welcome', 'cleanwelcome.enabled', $enabled);
    }

    public function getSettings(int $chatId): array
    {
        $s = $this->app->make(SettingsService::class);
        return [
            'welcome_enabled'      => $s->get($chatId, 'Welcome', 'welcome.enabled', default: true),
            'welcome_message'      => $s->get($chatId, 'Welcome', 'welcome.message', default: null),
            'goodbye_enabled'      => $s->get($chatId, 'Welcome', 'goodbye.enabled', default: false),
            'goodbye_message'      => $s->get($chatId, 'Welcome', 'goodbye.message', default: null),
            'cleanwelcome_enabled' => $s->get($chatId, 'Welcome', 'cleanwelcome.enabled', default: false),
        ];
    }

    // -------------------------------------------------------------------------
    // Template renderer
    // -------------------------------------------------------------------------

    private function renderTemplate(string $template, array $user, int $chatId, TelegramService $telegram): string
    {
        $firstName = htmlspecialchars($user['first_name'] ?? 'Usuário');
        $lastName  = htmlspecialchars($user['last_name']  ?? '');
        $full      = trim("{$firstName} {$lastName}");
        $username  = isset($user['username']) ? '@' . $user['username'] : $full;
        $mention   = isset($user['username'])
            ? "@{$user['username']}"
            : "<a href=\"tg://user?id={$user['id']}\">{$firstName}</a>";
        $id        = (string)($user['id'] ?? '');

        // Contagem de membros
        $count = '?';
        try {
            $count = (string)$this->app->make(TelegramClient::class)->getChatMemberCount($chatId);
        } catch (\Throwable) {}

        // Nome do chat
        $chatname = '?';
        try {
            $chat     = $this->app->make(TelegramClient::class)->getChat($chatId);
            $chatname = htmlspecialchars($chat['title'] ?? '');
        } catch (\Throwable) {}

        return strtr($template, [
            '{first}'    => $firstName,
            '{last}'     => $lastName,
            '{full}'     => $full,
            '{username}' => $username,
            '{mention}'  => $mention,
            '{id}'       => $id,
            '{count}'    => $count,
            '{chatname}' => $chatname,
        ]);
    }
}
