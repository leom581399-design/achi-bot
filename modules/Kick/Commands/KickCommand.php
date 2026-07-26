<?php
declare(strict_types=1);

namespace Modules\Kick\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * /kick — Expulsa um usuário do grupo (ban + unban imediato).
 */
class KickCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'kick'; }
    public function getDescription(): string { return 'Expulsa um usuário do grupo'; }
    public function getPermission(): Permission { return Permission::Administrator; }

    public function getMiddleware(): array
    {
        return [
            new GroupOnlyMiddleware($this->app),
            new PermissionMiddleware($this->app, Permission::Administrator),
        ];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $client   = $app->make(TelegramClient::class);
        $chatId   = $update->getChatId();
        $args     = $update->getCommandArgs();

        $target = TargetResolver::resolve($update, $args);
        if ($target === null) {
            $telegram->reply($update, $lang->trans('Kick.no_target'));
            return;
        }

        $targetId = $target['id'];
        $name     = $target['name'];

        if ($telegram->isAdmin($chatId, $targetId)) {
            $telegram->reply($update, $lang->trans('Kick.cannot_kick_admin'));
            return;
        }

        try {
            // Kick = ban temporário + unban imediato
            $client->banChatMember($chatId, $targetId);
            $client->unbanChatMember($chatId, $targetId);

            $text = $lang->trans('Kick.kicked', [':name' => $name]);
            $telegram->reply($update, $text);
        } catch (\Throwable) {
            $telegram->reply($update, $lang->trans('Kick.kick_failed'));
        }
    }
}
