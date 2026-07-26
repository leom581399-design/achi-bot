<?php
declare(strict_types=1);

namespace App\Core\Middleware;

use App\Core\Application;
use App\Core\Contracts\MiddlewareInterface;
use App\Core\Update;
use App\Core\Services\CacheService;

/**
 * Rate-limits command usage per user per minute.
 * Silently drops requests that exceed the threshold.
 */
class FloodMiddleware implements MiddlewareInterface
{
    public function __construct(
        private readonly Application $app,
        private readonly int         $maxPerMinute = 15
    ) {}

    public function handle(Update $update, callable $next): mixed
    {
        $userId = $update->getUserId();
        if ($userId === null) return $next($update);

        $cache = $this->app->make(CacheService::class);
        $key   = "flood:{$userId}:" . date('Y-m-d-H-i');
        $count = (int)($cache->get($key) ?? 0);

        if ($count >= $this->maxPerMinute) {
            // Silently ignore — do not reply to avoid spamming the user
            return null;
        }

        $cache->set($key, $count + 1, 70); // 70 s TTL to cover the whole minute
        return $next($update);
    }
}
