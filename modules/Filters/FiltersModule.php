<?php
declare(strict_types=1);

namespace Modules\Filters;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\Filters\Repository\FilterRepository;
use Modules\Filters\Services\FilterService;

class FiltersModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Filters'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Filters', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(FilterRepository::class, fn($a) => new FilterRepository($a->make(DatabaseService::class)));
        $app->singleton(FilterService::class,    fn($a) => new FilterService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\FilterCommand($this->app),
            new Commands\StopCommand($this->app),
            new Commands\FiltersCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'message.received' => [new Events\FilterListener($this->app)],
        ];
    }
}
