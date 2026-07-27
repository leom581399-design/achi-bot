<?php
declare(strict_types=1);

namespace Modules\Kick\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * /kickme — O usuário se auto-expulsa do grupo.
 */
class KickmeCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'kickme'; }
    public function getDescription(): string { return 'O\'zini o\'zi guruhdan chiqarib yuboradi'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $client   = $app->make(TelegramClient::class);
        $chatId   = $update->getChatId();
        $userId   = $update->getUserId();
        $user     = $update->getFrom();
        $name     = $user ? htmlspecialchars($user['first_name'] ?? 'Foydalanuvchi') : 'Foydalanuvchi';

        if ($telegram->isAdmin($chatId, $userId)) {
            $telegram->reply($update, $lang->trans('Kick.cannot_kick_admin'));
            return;
        }

        try {
            $text = $lang->trans('Kick.kickme_bye', [':name' => $name]);
            $telegram->reply($update, $text);

            $client->banChatMember($chatId, $userId);
            $client->unbanChatMember($chatId, $userId);
        } catch (\Throwable) {
            // Silencioso
        }
    }
}
