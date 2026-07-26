<?php
declare(strict_types=1);

namespace Modules\Filters\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Filters\Services\FilterService;

/**
 * /stop <palavra> — remove um filtro de palavra-chave.
 */
class StopCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'stop'; }
    public function getDescription(): string  { return 'Remove um filtro automático'; }
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
        $chatId   = $update->getChatId();
        $keyword  = trim($update->getCommandArgs());

        if ($keyword === '') {
            $telegram->reply($update, $lang->trans('Filters.stop_usage'));
            return;
        }

        $deleted = $app->make(FilterService::class)->delete($chatId, $keyword);

        if ($deleted) {
            $telegram->reply($update, $lang->trans('Filters.stopped', [':keyword' => htmlspecialchars($keyword)]));
        } else {
            $telegram->reply($update, $lang->trans('Filters.not_found', [':keyword' => htmlspecialchars($keyword)]));
        }
    }
}
