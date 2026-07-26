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
 * /unlock <tipo> — remove o bloqueio de um tipo de mensagem.
 * /unlock all — remove todos os bloqueios.
 */
class UnlockCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'unlock'; }
    public function getDescription(): string  { return 'Remove o bloqueio de um tipo de mensagem'; }
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
            $telegram->reply($update, $lang->trans('Locks.usage_unlock', [':types' => $types]));
            return;
        }

        if ($args === 'all') {
            $service->unlockAll($chatId);
            $telegram->reply($update, $lang->trans('Locks.unlocked_all'));
            return;
        }

        if (!in_array($args, LockService::VALID_TYPES, true)) {
            $telegram->reply($update, $lang->trans('Locks.invalid_type', [':type' => $args]));
            return;
        }

        if ($service->unlock($chatId, $args)) {
            $telegram->reply($update, $lang->trans('Locks.unlocked', [':type' => $args]));
        } else {
            $telegram->reply($update, $lang->trans('Locks.not_locked', [':type' => $args]));
        }
    }
}
