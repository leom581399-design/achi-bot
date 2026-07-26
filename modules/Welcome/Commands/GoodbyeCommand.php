<?php
declare(strict_types=1);

namespace Modules\Welcome\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Welcome\Services\WelcomeService;

/**
 * /goodbye on|off|<mensagem> — configura a mensagem de despedida.
 */
class GoodbyeCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'goodbye'; }
    public function getDescription(): string  { return 'Configura a mensagem de despedida'; }
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
        $service  = $app->make(WelcomeService::class);
        $chatId   = $update->getChatId();
        $args     = trim($update->getCommandArgs());
        $reply    = $update->getReplyToMessage();

        if ($args === '') {
            $cfg = $service->getSettings($chatId);
            $status = $cfg['goodbye_enabled'] ? $lang->trans('Welcome.on') : $lang->trans('Welcome.off');
            $msg    = $cfg['goodbye_message'] ?? $lang->trans('Welcome.default_goodbye_msg');
            $telegram->reply($update, $lang->trans('Welcome.goodbye_status', [
                ':status'  => $status,
                ':message' => htmlspecialchars($msg),
            ]));
            return;
        }

        match(strtolower($args)) {
            'on'  => (function() use ($service, $chatId, $telegram, $update, $lang) {
                $service->setGoodbyeEnabled($chatId, true);
                $telegram->reply($update, $lang->trans('Welcome.goodbye_enabled'));
            })(),
            'off' => (function() use ($service, $chatId, $telegram, $update, $lang) {
                $service->setGoodbyeEnabled($chatId, false);
                $telegram->reply($update, $lang->trans('Welcome.goodbye_disabled'));
            })(),
            default => (function() use ($args, $reply, $service, $chatId, $telegram, $update, $lang) {
                $msg = $args !== '' ? $args : ($reply['text'] ?? $reply['caption'] ?? '');
                if ($msg === '') {
                    $telegram->reply($update, $lang->trans('Welcome.usage_goodbye'));
                    return;
                }
                $service->setGoodbyeMessage($chatId, $msg);
                $telegram->reply($update, $lang->trans('Welcome.goodbye_message_set'));
            })(),
        };
    }
}
