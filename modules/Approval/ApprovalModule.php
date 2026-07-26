<?php
declare(strict_types=1);

namespace Modules\Approval;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;
use Modules\Approval\Services\ApprovalService;

class ApprovalModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Approval'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Approval', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(ApprovalService::class, fn($a) => new ApprovalService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\ApprovalCommand($this->app),
            new Commands\ApproveCommand($this->app),
            new Commands\DenyCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'user.joined' => [new Events\NewMemberApproval($this->app)],
        ];
    }
}
