<?php
declare(strict_types=1);

namespace Modules\Warn;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\Warn\Repository\WarnRepository;
use Modules\Warn\Services\WarnService;

class WarnModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Warn'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Warn', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(WarnRepository::class, fn($a) => new WarnRepository($a->make(DatabaseService::class)));
        $app->singleton(WarnService::class,    fn($a) => new WarnService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\WarnCommand($this->app),
            new Commands\UnwarnCommand($this->app),
            new Commands\ResetwarnCommand($this->app),
            new Commands\WarnsCommand($this->app),
        ];
    }

    public function getEvents(): array { return []; }
}
