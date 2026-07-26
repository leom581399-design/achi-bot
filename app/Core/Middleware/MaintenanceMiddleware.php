<?php
declare(strict_types=1);

namespace App\Core\Middleware;

use App\Core\Application;
use App\Core\Contracts\MiddlewareInterface;
use App\Core\Permission;
use App\Core\Services\{CacheService, PermissionService, TelegramService};
use App\Core\Update;

/**
 * Puts the bot in maintenance mode.
 *
 * When enabled (cache key `maintenance:enabled`), only Owners can use the bot.
 * Enable:  $cache->set('maintenance:enabled', true);
 * Disable: $cache->delete('maintenance:enabled');
 */
class MaintenanceMiddleware implements MiddlewareInterface
{
    public function __construct(private readonly Application $app) {}

    public function handle(Update $update, callable $next): mixed
    {
        $cache = $this->app->make(CacheService::class);

        if (!$cache->get('maintenance:enabled', false)) {
            return $next($update);
        }

        $userId = $update->getUserId();
        $chatId = $update->getChatId();

        if ($userId === null) {
            return $next($update);
        }

        $perms = $this->app->make(PermissionService::class);

        if ($perms->getPermission($chatId ?? 0, $userId)->isAtLeast(Permission::Owner)) {
            return $next($update);
        }

        // Bot is in maintenance — silently ignore non-owner updates
        return null;
    }
}
