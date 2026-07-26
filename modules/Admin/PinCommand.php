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
 * /pin — Pin the replied-to message in the group.
 * Requires Administrator permission.
 */
class PinCommand implements CommandInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function getCommand(): string     { return 'pin'; }
    public function getDescription(): string { return 'Pin the replied message (reply to a message)'; }
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

        if ($reply === null) {
            $telegram->reply($update, '❌ Reply to a message to pin it.');
            return;
        }

        try {
            $client->request('pinChatMessage', [
                'chat_id'              => $update->getChatId(),
                'message_id'           => $reply['message_id'],
                'disable_notification' => false,
            ]);
            $telegram->reply($update, '📌 Message pinned successfully.');
        } catch (\Throwable) {
            $telegram->reply($update, '❌ Failed to pin the message. Make sure I have pin permissions.');
        }
    }
}
