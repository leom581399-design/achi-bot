<?php
declare(strict_types=1);

namespace Modules\Admin;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;

class AdminModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Admin'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Admin', __DIR__ . '/Language');
    }

    public function register(Application $app): void {}

    public function getCommands(): array
    {
        return [
            new AdminListCommand($this->app),
            new PinCommand($this->app),
            new UnpinCommand($this->app),
        ];
    }

    public function getEvents(): array { return []; }
}
