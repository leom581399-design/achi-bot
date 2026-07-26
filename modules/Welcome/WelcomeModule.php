<?php
declare(strict_types=1);

namespace Modules\Welcome;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\Welcome\Services\WelcomeService;

class WelcomeModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Welcome'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Welcome', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(WelcomeService::class, fn($a) => new WelcomeService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\WelcomeCommand($this->app),
            new Commands\GoodbyeCommand($this->app),
            new Commands\CleanwelcomeCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'user.joined' => [new Events\JoinListener($this->app)],
            'user.left'   => [new Events\LeaveListener($this->app)],
        ];
    }
}
