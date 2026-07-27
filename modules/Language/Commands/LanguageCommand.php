<?php
declare(strict_types=1);

namespace Modules\Language\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, SettingsService, TelegramService};
use App\Core\Update;

/**
 * /til (yoki /language) — guruh uchun tilni ko'rish/o'zgartirish.
 *
 * Argumentsiz chaqirilsa - joriy tilni va tanlash tugmalarini (inline
 * keyboard) ko'rsatadi. Tugma bosilganda LanguageCallbackListener
 * ishlaydi (pastroqda).
 */
class LanguageCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'til'; }
    public function getDescription(): string    { return "Guruh tilini ko'rish/o'zgartirish (uz/ru)"; }
    public function getPermission(): Permission { return Permission::Administrator; }

    public function getMiddleware(): array
    {
        return [
            new GroupOnlyMiddleware($this->app),
            new PermissionMiddleware($this->app, Permission::Administrator),
        ];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $settings = $app->make(SettingsService::class);
        $chatId   = $update->getChatId();

        $current = $settings->get($chatId, 'Language', 'locale', LanguageService::FALLBACK_LOCALE);
        $flag    = $current === 'ru' ? '🇷🇺' : '🇺🇿';
        $name    = $lang->trans('Language.name_' . $current);

        $keyboard = [
            'inline_keyboard' => [[
                ['text' => $lang->trans('Language.btn_uz'), 'callback_data' => 'lang_set:uz'],
                ['text' => $lang->trans('Language.btn_ru'), 'callback_data' => 'lang_set:ru'],
            ]],
        ];

        $telegram->reply(
            $update,
            $lang->trans('Language.current', [':flag' => $flag, ':name' => $name]),
            ['reply_markup' => $keyboard]
        );
    }
}
