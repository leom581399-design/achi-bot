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
 * /pin — Reply qilingan xabarni guruhda qadaydi.
 * Administrator ruxsati talab qilinadi.
 */
class PinCommand implements CommandInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function getCommand(): string     { return 'pin'; }
    public function getDescription(): string { return 'Reply qilingan xabarni qadaydi'; }
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

        if ($reply === null) {
            $telegram->reply($update, $lang->trans('Admin.reply_required'));
            return;
        }

        try {
            $client->request('pinChatMessage', [
                'chat_id'              => $update->getChatId(),
                'message_id'           => $reply['message_id'],
                'disable_notification' => false,
            ]);
            $telegram->reply($update, $lang->trans('Admin.pin_success'));
        } catch (\Throwable) {
            $telegram->reply($update, $lang->trans('Admin.pin_fail'));
        }
    }
}
