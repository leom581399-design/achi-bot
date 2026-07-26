<?php
declare(strict_types=1);

namespace App\Core\Middleware;

use App\Core\Application;
use App\Core\Contracts\MiddlewareInterface;
use App\Core\Permission;
use App\Core\Update;
use App\Core\Services\{PermissionService, TelegramService};

/**
 * Enforces a minimum permission level before letting the command through.
 *
 * Usage in a command:
 *   public function getMiddleware(): array {
 *       return [new PermissionMiddleware($app, Permission::Administrator)];
 *   }
 */
class PermissionMiddleware implements MiddlewareInterface
{
    public function __construct(
        private readonly Application $app,
        private readonly Permission  $required
    ) {}

    public function handle(Update $update, callable $next): mixed
    {
        $chatId = $update->getChatId();
        $userId = $update->getUserId();

        if ($chatId === null || $userId === null) {
            return null;
        }

        $permService = $this->app->make(PermissionService::class);

        if (!$permService->can($chatId, $userId, $this->required)) {
            $this->app->make(TelegramService::class)->reply(
                $update,
                "⛔ <b>Permission denied.</b>\nYou need at least <b>{$this->required->label()}</b> to use this command."
            );
            return null;
        }

        return $next($update);
    }
}
