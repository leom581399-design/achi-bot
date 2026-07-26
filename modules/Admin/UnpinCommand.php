<?php
declare(strict_types=1);

namespace Modules\Admin;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\TelegramService;
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * /unpin — Unpins the most recent pinned message (or the replied-to one).
 * Requires Administrator permission.
 */
class UnpinCommand implements CommandInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function getCommand(): string     { return 'unpin'; }
    public function getDescription(): string { return 'Unpin the current/replied pinned message'; }
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
        $client   = $app->make(TelegramClient::class);
        $reply    = $update->getReplyToMessage();

        try {
            $params = ['chat_id' => $update->getChatId()];
            if ($reply !== null) {
                $params['message_id'] = $reply['message_id'];
            }
            $client->request('unpinChatMessage', $params);
            $telegram->reply($update, '📌 Message unpinned.');
        } catch (\Throwable) {
            $telegram->reply($update, '❌ Failed to unpin. Make sure I have pin permissions.');
        }
    }
}
