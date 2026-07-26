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
 * /welcome on|off|<mensagem> — configura a boas-vindas do grupo.
 *
 * Variáveis disponíveis: {first} {last} {full} {username} {mention} {id} {count} {chatname}
 */
class WelcomeCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'welcome'; }
    public function getDescription(): string  { return 'Configura a mensagem de boas-vindas'; }
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
            // Sem args: mostra status atual
            $cfg = $service->getSettings($chatId);
            $status = $cfg['welcome_enabled'] ? $lang->trans('Welcome.on') : $lang->trans('Welcome.off');
            $msg    = $cfg['welcome_message'] ?? $lang->trans('Welcome.default_msg');
            $telegram->reply($update, $lang->trans('Welcome.status', [
                ':status'  => $status,
                ':message' => htmlspecialchars($msg),
            ]));
            return;
        }

        match(strtolower($args)) {
            'on'  => (function() use ($service, $chatId, $telegram, $update, $lang) {
                $service->setWelcomeEnabled($chatId, true);
                $telegram->reply($update, $lang->trans('Welcome.enabled'));
            })(),
            'off' => (function() use ($service, $chatId, $telegram, $update, $lang) {
                $service->setWelcomeEnabled($chatId, false);
                $telegram->reply($update, $lang->trans('Welcome.disabled'));
            })(),
            default => (function() use ($args, $reply, $service, $chatId, $telegram, $update, $lang) {
                $msg = $args !== '' ? $args : ($reply['text'] ?? $reply['caption'] ?? '');
                if ($msg === '') {
                    $telegram->reply($update, $lang->trans('Welcome.usage'));
                    return;
                }
                $service->setWelcomeMessage($chatId, $msg);
                $telegram->reply($update, $lang->trans('Welcome.message_set'));
            })(),
        };
    }
}
