<?php
declare(strict_types=1);

namespace Modules\Mute;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\Mute\Repository\MuteRepository;
use Modules\Mute\Services\MuteService;

class MuteModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Mute'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Mute', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(MuteRepository::class, fn($a) => new MuteRepository($a->make(DatabaseService::class)));
        $app->singleton(MuteService::class,    fn($a) => new MuteService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\MuteCommand($this->app),
            new Commands\TmuteCommand($this->app),
            new Commands\UnmuteCommand($this->app),
            new Commands\MuteallCommand($this->app),
        ];
    }

    public function getEvents(): array { return []; }
}
