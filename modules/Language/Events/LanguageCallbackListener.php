<?php
declare(strict_types=1);

namespace Modules\Language\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService, PermissionService, SettingsService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use App\Core\Permission;

/**
 * "callback.received" hodisasiga obuna - /til buyrug'idagi inline
 * tugmalar (🇺🇿 O'zbekcha / 🇷🇺 Русский) bosilganda ishga tushadi.
 *
 * callback_data: "lang_set:uz" yoki "lang_set:ru"
 */
class LanguageCallbackListener
{
    public function __construct(private readonly Application $app) {}

    public function __invoke(mixed $data): void
    {
        $this->handle(is_array($data) ? $data : []);
    }

    public function handle(array $data): void
    {
        /** @var Update $update */
        $update = $data['update'] ?? null;
        if ($update === null || $update->callbackQuery === null) return;

        $cb     = $update->callbackQuery;
        $cbData = $cb['data'] ?? '';

        if ($cbData !== 'lang_menu' && !str_starts_with($cbData, 'lang_set:')) return;

        $chatId    = $update->getChatId();
        $userId    = $update->getUserId();
        $cbQueryId = $cb['id'] ?? '';

        if ($chatId === null || $userId === null) return;

        $client = $this->app->make(TelegramClient::class);

        // Faqat admin (yoki bot egasi) tilni o'zgartirishi mumkin -
        // istalgan a'zo tugmani bosib guruh tilini o'zgartirmasin.
        $permService = $this->app->make(PermissionService::class);
        if (!$permService->can($chatId, $userId, Permission::Administrator)) {
            try {
                $client->answerCallbackQuery($cbQueryId, ['text' => '⛔', 'show_alert' => false]);
            } catch (\Throwable) {}
            return;
        }

        // /help'dagi "🌐 Tilni o'zgartirish" tugmasi - tanlash
        // tugmalarini (uz/ru) ko'rsatadi, xuddi /til buyrug'i kabi.
        if ($cbData === 'lang_menu') {
            $lang = $this->app->make(LanguageService::class);
            try {
                $client->answerCallbackQuery($cbQueryId);
            } catch (\Throwable) {}
            try {
                $client->sendMessage($chatId, $lang->trans('Language.current', [
                    ':flag' => '🌐', ':name' => '',
                ]), [
                    'reply_markup' => ['inline_keyboard' => [[
                        ['text' => $lang->trans('Language.btn_uz'), 'callback_data' => 'lang_set:uz'],
                        ['text' => $lang->trans('Language.btn_ru'), 'callback_data' => 'lang_set:ru'],
                    ]]],
                ]);
            } catch (\Throwable) {}
            return;
        }

        $locale = substr($cbData, strlen('lang_set:'));
        if (!in_array($locale, LanguageService::SUPPORTED_LOCALES, true)) {
            return;
        }

        $settings = $this->app->make(SettingsService::class);
        $settings->set($chatId, 'Language', 'locale', $locale);

        $lang = $this->app->make(LanguageService::class);
        $lang->setLocale($locale);
        $name = $lang->trans('Language.name_' . $locale);

        try {
            $client->answerCallbackQuery($cbQueryId, ['text' => '✅', 'show_alert' => false]);
        } catch (\Throwable) {}

        try {
            $client->editMessageText(
                $chatId,
                $cb['message']['message_id'] ?? 0,
                $lang->trans('Language.changed', [':name' => $name])
            );
        } catch (\Throwable) {}
    }
}
