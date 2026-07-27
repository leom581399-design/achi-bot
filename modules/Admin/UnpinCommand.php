<?php
declare(strict_types=1);

namespace Modules\Admin;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * /unpin — Eng oxirgi qadalgan xabarni (yoki reply qilinganini) qadaqdan oladi.
 * Administrator ruxsati talab qilinadi.
 */
class UnpinCommand implements CommandInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function getCommand(): string     { return 'unpin'; }
    public function getDescription(): string { return 'Qadalgan xabarni qadaqdan oladi'; }
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
        $reply    = $update->getReplyToMessage();

        try {
            $params = ['chat_id' => $update->getChatId()];
            if ($reply !== null) {
                $params['message_id'] = $reply['message_id'];
            }
            $client->request('unpinChatMessage', $params);
            $telegram->reply($update, $lang->trans('Admin.unpin_success'));
        } catch (\Throwable) {
            $telegram->reply($update, $lang->trans('Admin.unpin_fail'));
        }
    }
}
