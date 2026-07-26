<?php
declare(strict_types=1);

namespace Modules\Backup;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\Backup\Services\BackupService;

class BackupModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Backup'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Backup', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(BackupService::class, fn($a) => new BackupService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\BackupCommand($this->app),
            new Commands\RestoreCommand($this->app),
        ];
    }

    public function getEvents(): array { return []; }
}
