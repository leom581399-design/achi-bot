<?php
declare(strict_types=1);

namespace Modules\Start;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;

class StartModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Start'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void     { $this->app = $app; }
    public function register(Application $app): void {}

    public function getCommands(): array
    {
        return [new StartCommand($this->app)];
    }

    public function getEvents(): array { return []; }
}
