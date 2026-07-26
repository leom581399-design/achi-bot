<?php
declare(strict_types=1);

namespace Modules\Admin;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\TelegramService;
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * /adminlist — Lists all administrators in the group.
 */
class AdminListCommand implements CommandInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function getCommand(): string     { return 'adminlist'; }
    public function getDescription(): string { return 'List all group administrators'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $client   = $app->make(TelegramClient::class);
        $chatId   = $update->getChatId();

        try {
            $admins = $client->getChatAdministrators($chatId);
            $chat   = $client->getChat($chatId);

            $title = htmlspecialchars($chat['title'] ?? 'This Group');
            $text  = "<b>👮 Admins of {$title}</b>\n\n";

            foreach ($admins as $admin) {
                $user   = $admin['user'];
                $name   = htmlspecialchars($user['first_name'] ?? 'Unknown');
                if (isset($user['last_name'])) {
                    $name .= ' ' . htmlspecialchars($user['last_name']);
                }
                $tag    = isset($user['username']) ? " (@{$user['username']})" : '';
                $isBot  = ($user['is_bot'] ?? false) ? ' 🤖' : '';
                $role   = $admin['status'] === 'creator' ? '👑' : '⚙️';
                $title2 = isset($admin['custom_title']) && $admin['custom_title'] !== ''
                    ? " <i>[{$admin['custom_title']}]</i>"
                    : '';
                $text  .= "{$role} <b>{$name}</b>{$tag}{$isBot}{$title2}\n";
            }

            $total = count($admins);
            $text .= "\n<i>{$total} administrator(s) total.</i>";

            $telegram->reply($update, $text);

        } catch (\Throwable $e) {
            $telegram->reply(
                $update,
                '❌ Failed to fetch admin list. Make sure I have admin permissions.'
            );
        }
    }
}
