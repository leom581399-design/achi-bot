<?php
declare(strict_types=1);

namespace Modules\Help;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;

class HelpModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Help'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Help', __DIR__ . '/Language');
    }

    public function register(Application $app): void {}

    public function getCommands(): array
    {
        return [new HelpCommand($this->app)];
    }

    public function getEvents(): array { return []; }
}
