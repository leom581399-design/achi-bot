<?php
declare(strict_types=1);

namespace Modules\Stats;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\Stats\Events\MessageStatsListener;
use Modules\Stats\Repository\StatsRepository;
use Modules\Stats\Services\StatsService;

class StatsModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Stats'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Stats', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(StatsRepository::class, fn($a) => new StatsRepository($a->make(DatabaseService::class)));
        $app->singleton(StatsService::class,    fn($a) => new StatsService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\StatsCommand($this->app),
            new Commands\TopCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'message.received' => [new MessageStatsListener($this->app)],
        ];
    }
}
