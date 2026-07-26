<?php
declare(strict_types=1);

namespace Modules\Flood;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;
use Modules\Flood\Services\FloodService;

class FloodModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Flood'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Flood', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(FloodService::class, fn($a) => new FloodService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\SetfloodCommand($this->app),
            new Commands\SetfloodmodeCommand($this->app),
            new Commands\FloodCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'message.received' => [new Events\FloodChecker($this->app)],
        ];
    }
}
