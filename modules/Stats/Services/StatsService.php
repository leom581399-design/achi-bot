<?php
declare(strict_types=1);

namespace Modules\Stats\Services;

use App\Core\Application;
use Modules\Stats\Repository\StatsRepository;

class StatsService
{
    public function __construct(private readonly Application $app) {}

    public function record(int $chatId, int $userId): void
    {
        $this->app->make(StatsRepository::class)->increment($chatId, $userId);
    }

    public function topUsers(int $chatId, int $limit = 10): array
    {
        return $this->app->make(StatsRepository::class)->topUsers($chatId, $limit);
    }

    public function groupStats(int $chatId): array
    {
        $repo = $this->app->make(StatsRepository::class);
        return [
            'total_messages' => $repo->totalMessages($chatId),
            'total_users'    => $repo->totalUsers($chatId),
        ];
    }

    public function userStats(int $chatId, int $userId): ?array
    {
        return $this->app->make(StatsRepository::class)->userRank($chatId, $userId);
    }
}
