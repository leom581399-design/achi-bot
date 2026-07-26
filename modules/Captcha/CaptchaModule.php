<?php
declare(strict_types=1);

namespace Modules\Captcha;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;
use Modules\Captcha\Services\CaptchaService;

class CaptchaModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Captcha'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Captcha', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(CaptchaService::class, fn($a) => new CaptchaService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\CaptchaCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'user.joined'      => [new Events\NewMemberCaptcha($this->app)],
            'message.received' => [new Events\CaptchaAnswerListener($this->app)],
            'callback.received' => [new Events\CaptchaCallbackListener($this->app)],
        ];
    }
}
