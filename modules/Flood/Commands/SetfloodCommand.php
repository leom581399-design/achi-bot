<?php
declare(strict_types=1);

namespace Modules\Flood\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Flood\Services\FloodService;

/**
 * /setflood N — define o limite de mensagens por janela (0 = desativar).
 */
class SetfloodCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'setflood'; }
    public function getDescription(): string    { return 'Define o limite de flood'; }
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
        $service  = $app->make(FloodService::class);
        $chatId   = $update->getChatId();
        $args     = trim($update->getCommandArgs());

        if ($args === '' || !ctype_digit($args)) {
            $telegram->reply($update, $lang->trans('Flood.setflood_invalid'));
            return;
        }

        $n = (int)$args;
        $service->setLimit($chatId, $n);

        if ($n === 0) {
            $telegram->reply($update, $lang->trans('Flood.setflood_off'));
        } else {
            $telegram->reply($update, $lang->trans('Flood.setflood_ok', [':n' => $n]));
        }
    }
}
