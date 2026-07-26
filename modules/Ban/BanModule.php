<?php
declare(strict_types=1);

namespace Modules\Ban;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\Ban\Repository\BanRepository;
use Modules\Ban\Services\BanService;

class BanModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Ban'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Ban', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(BanRepository::class, fn($a) => new BanRepository($a->make(DatabaseService::class)));
        $app->singleton(BanService::class,    fn($a) => new BanService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\BanCommand($this->app),
            new Commands\TbanCommand($this->app),
            new Commands\UnbanCommand($this->app),
            new Commands\SbanCommand($this->app),
            new Commands\BanmeCommand($this->app),
        ];
    }

    public function getEvents(): array { return []; }
}
