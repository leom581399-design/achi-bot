<?php
declare(strict_types=1);

namespace Modules\FedBan;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\FedBan\Repository\FedRepository;
use Modules\FedBan\Services\FedService;

class FedBanModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'FedBan'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('FedBan', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(FedRepository::class, fn($a) => new FedRepository($a->make(DatabaseService::class)));
        $app->singleton(FedService::class,    fn($a) => new FedService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\NewfedCommand($this->app),
            new Commands\JoinfedCommand($this->app),
            new Commands\LeavefedCommand($this->app),
            new Commands\FbanCommand($this->app),
            new Commands\UnfbanCommand($this->app),
            new Commands\FedInfoCommand($this->app),
        ];
    }

    public function getEvents(): array { return []; }
}
