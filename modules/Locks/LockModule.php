<?php
declare(strict_types=1);

namespace Modules\Locks;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;
use Modules\Locks\Services\LockService;

class LockModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Locks'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Locks', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(LockService::class, fn($a) => new LockService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\LockCommand($this->app),
            new Commands\UnlockCommand($this->app),
            new Commands\LocksCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'message.received' => [new Events\LockEnforcer($this->app)],
        ];
    }
}
