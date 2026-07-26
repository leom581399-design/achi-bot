<?php
declare(strict_types=1);

namespace App\Core\Middleware;

use App\Core\Application;
use App\Core\Contracts\MiddlewareInterface;
use App\Core\Services\CacheService;
use App\Core\Update;

/**
 * Global user blacklist middleware.
 *
 * Blacklisted users have ALL their updates silently ignored by the bot.
 * The blacklist is stored in the CacheService under the key `blacklist:users`.
 *
 * Usage:
 *   $cache->set('blacklist:users', [123456, 789012]);
 *
 * Or use the helper methods below.
 */
class BlacklistMiddleware implements MiddlewareInterface
{
    private const CACHE_KEY = 'blacklist:users';

    public function __construct(private readonly Application $app) {}

    public function handle(Update $update, callable $next): mixed
    {
        $userId = $update->getUserId();

        if ($userId !== null && $this->isBlacklisted($userId)) {
            return null; // silently drop
        }

        return $next($update);
    }

    // -------------------------------------------------------------------------
    // Management helpers
    // -------------------------------------------------------------------------

    public function add(int $userId): void
    {
        $list   = $this->getList();
        $list[] = $userId;
        $this->app->make(CacheService::class)->set(self::CACHE_KEY, array_unique($list));
    }

    public function remove(int $userId): void
    {
        $list = array_filter($this->getList(), fn($id) => $id !== $userId);
        $this->app->make(CacheService::class)->set(self::CACHE_KEY, array_values($list));
    }

    public function isBlacklisted(int $userId): bool
    {
        return in_array($userId, $this->getList(), true);
    }

    private function getList(): array
    {
        return $this->app->make(CacheService::class)->get(self::CACHE_KEY, []);
    }
}
