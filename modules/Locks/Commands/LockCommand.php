<?php
declare(strict_types=1);

namespace Modules\Locks\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Locks\Services\LockService;

/**
 * /lock <tipo> — bloqueia um tipo de mensagem no grupo.
 */
class LockCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'lock'; }
    public function getDescription(): string  { return 'Xabar turini qulflaydi'; }
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
        $service  = $app->make(LockService::class);
        $chatId   = $update->getChatId();
        $args     = strtolower(trim($update->getCommandArgs()));

        if ($args === '') {
            $types = implode(', ', LockService::VALID_TYPES);
            $telegram->reply($update, $lang->trans('Locks.usage', [':types' => $types]));
            return;
        }

        if (!in_array($args, LockService::VALID_TYPES, true)) {
            $telegram->reply($update, $lang->trans('Locks.invalid_type', [':type' => $args]));
            return;
        }

        if ($service->lock($chatId, $args)) {
            $telegram->reply($update, $lang->trans('Locks.locked', [':type' => $args]));
        } else {
            $telegram->reply($update, $lang->trans('Locks.already_locked', [':type' => $args]));
        }
    }
}
