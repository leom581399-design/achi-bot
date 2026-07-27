<?php
declare(strict_types=1);

namespace Modules\Warn\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Warn\Services\WarnService;

/**
 * /resetwarn — Remove todas as advertências de um usuário.
 */
class ResetwarnCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'resetwarn'; }
    public function getDescription(): string { return 'Foydalanuvchining barcha ogohlantirishlarini tozalaydi'; }
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
        $service  = $app->make(WarnService::class);
        $chatId   = $update->getChatId();
        $args     = $update->getCommandArgs();

        $target = TargetResolver::resolve($update, $args);
        if ($target === null) {
            $telegram->reply($update, $lang->trans('Warn.no_target'));
            return;
        }

        $removed = $service->resetWarns($chatId, $target['id']);

        if ($removed === 0) {
            $telegram->reply($update, $lang->trans('Warn.resetwarn_none'));
            return;
        }

        $text = $lang->trans('Warn.resetwarn_done', [':name' => $target['name']]);
        $telegram->reply($update, $text);
    }
}
