<?php
declare(strict_types=1);

namespace App\Core;

use App\Core\Services\{LanguageService, LoggerService, SettingsService};

/**
 * Routes incoming Telegram updates to the right handler.
 *
 * The Router emits events so modules can react to anything
 * (UserJoined, MessageReceived, etc.) without touching the Core.
 */
class Router
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function dispatch(Update $update): void
    {
        $this->applyChatLocale($update);

        $dispatcher = $this->app->make(EventDispatcher::class);
        $registry   = $this->app->make(CommandRegistry::class);
        $logger     = $this->app->make(LoggerService::class);

        match($update->type) {
            'message'       => $this->handleMessage($update, $dispatcher, $registry, $logger),
            'callback_query' => $dispatcher->emit('callback.received', $update),
            'inline_query'   => $dispatcher->emit('inline.received', $update),
            'chat_member',
            'my_chat_member' => $dispatcher->emit('member.updated', $update),
            default          => null,
        };
    }

    private function handleMessage(
        Update          $update,
        EventDispatcher $dispatcher,
        CommandRegistry $registry,
        LoggerService   $logger
    ): void {
        // Always emit generic event
        $dispatcher->emit('message.received', $update);

        // New members joined
        if ($update->isNewChatMember()) {
            foreach ($update->message['new_chat_members'] as $member) {
                $dispatcher->emit('user.joined', ['update' => $update, 'member' => $member]);
            }
        }

        // Member left
        if ($update->isLeftChatMember()) {
            $dispatcher->emit('user.left', [
                'update' => $update,
                'member' => $update->message['left_chat_member'],
            ]);
        }

        // Command
        if ($update->isCommand()) {
            $cmd = $update->getCommand();
            $logger->info("/{$cmd} — user:{$update->getUserId()} chat:{$update->getChatId()}");

            // beforeCommand hook
            $dispatcher->emit('command.before', ['command' => $cmd, 'update' => $update]);

            $registry->dispatch($update);

            // afterCommand hook
            $dispatcher->emit('command.after', ['command' => $cmd, 'update' => $update]);
            $dispatcher->emit('command.executed', ['command' => $cmd, 'update' => $update]);
        }
    }

    /**
     * Har bir update kelganda, shu guruh (chat) uchun /til orqali
     * tanlangan tilni SettingsService'dan o'qib, LanguageService'ga
     * o'rnatadi. Shu bilan bitta bot bir vaqtning o'zida turli
     * guruhlarda turli tillarda (uz/ru) javob beradi - hech qanday
     * global holat qolmaydi, har so'rov o'zining tilini o'z ichida
     * olib yuradi.
     *
     * Shaxsiy (private) chatlarda chat_id foydalanuvchi ID'siga teng
     * bo'ladi - u holatda ham xuddi shu mexanizm ishlaydi (har kim
     * o'zi uchun /til bilan tilni tanlashi mumkin).
     */
    private function applyChatLocale(Update $update): void
    {
        $chatId = $update->getChatId();
        $lang   = $this->app->make(LanguageService::class);

        if ($chatId === null) {
            $lang->setLocale(LanguageService::FALLBACK_LOCALE);
            return;
        }

        try {
            $settings = $this->app->make(SettingsService::class);
            $locale   = $settings->get($chatId, 'Language', 'locale', LanguageService::FALLBACK_LOCALE);
        } catch (\Throwable) {
            $locale = LanguageService::FALLBACK_LOCALE;
        }

        $lang->setLocale($locale);
    }
}
