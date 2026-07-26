<?php
declare(strict_types=1);

namespace Modules\AntiSpam;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;
use Modules\AntiSpam\Services\SpamDetector;

class AntiSpamModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'AntiSpam'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('AntiSpam', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(SpamDetector::class, fn($a) => new SpamDetector($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\AntispamCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'user.joined'      => [new Events\CasChecker($this->app)],
            'message.received' => [new Events\SpamChecker($this->app)],
        ];
    }
}
