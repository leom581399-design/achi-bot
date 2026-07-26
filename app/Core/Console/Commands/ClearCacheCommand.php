<?php
declare(strict_types=1);

namespace App\Core\Console\Commands;

use App\Core\Application;
use App\Core\Services\CacheService;

class ClearCacheCommand
{
    public function __construct(private readonly Application $app) {}

    public function handle(array $args): int
    {
        echo "🗑️  Clearing filesystem cache...\n";

        $cache = $this->app->make(CacheService::class);
        $cache->flush();

        echo "✅ Cache cleared.\n";
        return 0;
    }
}
