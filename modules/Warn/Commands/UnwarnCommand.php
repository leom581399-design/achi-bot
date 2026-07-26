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
 * /unwarn — Remove a advertência mais recente de um usuário.
 */
class UnwarnCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'unwarn'; }
    public function getDescription(): string { return 'Remove a última advertência de um usuário'; }
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

        $removed = $service->unwarn($chatId, $target['id']);

        if (!$removed) {
            $telegram->reply($update, $lang->trans('Warn.unwarn_none'));
            return;
        }

        $count = $service->getWarnCount($chatId, $target['id']);
        $max   = $service->getMaxWarns($chatId);

        $text = $lang->trans('Warn.unwarn_done', [
            ':name'  => $target['name'],
            ':count' => $count,
            ':max'   => $max,
        ]);
        $telegram->reply($update, $text);
    }
}
