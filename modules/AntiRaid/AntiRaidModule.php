<?php
declare(strict_types=1);

namespace Modules\AntiRaid;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;
use Modules\AntiRaid\Services\RaidDetectorService;

class AntiRaidModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'AntiRaid'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('AntiRaid', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(RaidDetectorService::class, fn($a) => new RaidDetectorService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\AntiRaidCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'user.joined' => [new Events\RaidDetector($this->app)],
        ];
    }
}
