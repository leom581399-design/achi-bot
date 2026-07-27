<?php
declare(strict_types=1);

namespace Modules\Language;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;

/**
 * ACHI BOT — guruh darajasida til tanlash (/til, /language).
 *
 * Har bir guruh o'zining tilini tanlashi mumkin (standart: o'zbek).
 * Tanlov SettingsService orqali (chat_id, module='Language', key='locale')
 * saqlanadi va Router har update kelganda shu qiymatni o'qib
 * LanguageService::setLocale() chaqiradi - shu bilan bitta bot bir
 * vaqtning o'zida turli guruhlarda turli tillarda gaplasha oladi.
 */
class LanguageModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Language'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Language', __DIR__ . '/Language');
    }

    public function register(Application $app): void {}

    public function getCommands(): array
    {
        return [
            new Commands\LanguageCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'callback.received' => [new Events\LanguageCallbackListener($this->app)],
        ];
    }
}
