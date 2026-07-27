<?php
declare(strict_types=1);

namespace App\Core\Services;

use App\Core\Application;
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * High-level Telegram helper service.
 *
 * Wraps TelegramClient with convenience methods that understand Update context.
 * Modules should prefer this over TelegramClient directly.
 */
class TelegramService
{
    public function __construct(
        private readonly Application $app
    ) {}

    // -------------------------------------------------------------------------
    // Messaging helpers
    // -------------------------------------------------------------------------

    public function sendMessage(int|string $chatId, string $text, array $options = []): array
    {
        return $this->client()->sendMessage($chatId, $text, $options);
    }

    /** Reply to the message contained in an Update. */
    public function reply(Update $update, string $text, array $options = []): array
    {
        return $this->client()->sendMessage(
            $update->getChatId(),
            $text,
            array_merge(['reply_to_message_id' => $update->getMessageId()], $options)
        );
    }

    /** Send a message without quoting the original. */
    public function send(Update $update, string $text, array $options = []): array
    {
        return $this->client()->sendMessage($update->getChatId(), $text, $options);
    }

    // -------------------------------------------------------------------------
    // Permission helpers
    // -------------------------------------------------------------------------

    public function isAdmin(int|string $chatId, int $userId): bool
    {
        try {
            $member = $this->client()->getChatMember($chatId, $userId);
            return in_array($member['status'], ['creator', 'administrator'], true);
        } catch (\Throwable) {
            return false;
        }
    }

    public function isCreator(int|string $chatId, int $userId): bool
    {
        try {
            return $this->client()->getChatMember($chatId, $userId)['status'] === 'creator';
        } catch (\Throwable) {
            return false;
        }
    }

    public function isBotAdmin(int|string $chatId): bool
    {
        try {
            $me = $this->client()->getMe();
            return $this->isAdmin($chatId, $me['id']);
        } catch (\Throwable) {
            return false;
        }
    }

    // -------------------------------------------------------------------------
    // User formatting helpers
    // -------------------------------------------------------------------------

    public function mentionUser(array $user): string
    {
        $name = htmlspecialchars($user['first_name'] ?? "Foydalanuvchi");
        if (isset($user['last_name'])) {
            $name .= ' ' . htmlspecialchars($user['last_name']);
        }
        return isset($user['username'])
            ? "@{$user['username']}"
            : "<a href=\"tg://user?id={$user['id']}\">{$name}</a>";
    }

    public function formatUser(array $user): string
    {
        $name = htmlspecialchars($user['first_name'] ?? "Noma'lum");
        if (isset($user['last_name'])) {
            $name .= ' ' . htmlspecialchars($user['last_name']);
        }
        $tag = isset($user['username']) ? " (@{$user['username']})" : '';
        return "<b>{$name}</b>{$tag}";
    }

    // -------------------------------------------------------------------------
    // Internal
    // -------------------------------------------------------------------------

    private function client(): TelegramClient
    {
        return $this->app->make(TelegramClient::class);
    }
}
