<?php
declare(strict_types=1);

namespace Modules\Locks\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Locks\Services\LockService;

/**
 * /locks — lista todos os locks ativos no grupo.
 */
class LocksCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'locks'; }
    public function getDescription(): string  { return 'Lista os bloqueios ativos'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $service  = $app->make(LockService::class);
        $chatId   = $update->getChatId();

        $locked = $service->getLockedTypes($chatId);

        if (empty($locked)) {
            $telegram->reply($update, $lang->trans('Locks.no_locks'));
            return;
        }

        $list = implode(', ', array_map(fn($t) => "<code>{$t}</code>", $locked));
        $telegram->reply($update, $lang->trans('Locks.list', [':list' => $list]));
    }
}
