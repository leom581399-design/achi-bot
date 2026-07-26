<?php
declare(strict_types=1);

namespace Modules\Ban\Services;

use App\Core\Application;
use App\Core\EventDispatcher;
use App\Core\Services\LoggerService;
use App\Core\Telegram\TelegramClient;
use Modules\Ban\Repository\BanRepository;

class BanService
{
    public function __construct(private readonly Application $app) {}

    /**
     * Ban a user from a chat.
     *
     * @param int      $chatId    Target chat
     * @param int      $userId    User to ban
     * @param int      $bannedBy  Who issued the ban
     * @param string|null $reason Reason for the ban
     * @param int|null $untilDate Unix timestamp (null = permanent)
     */
    public function ban(int $chatId, int $userId, int $bannedBy, ?string $reason, ?int $untilDate = null): void
    {
        $options = ['revoke_messages' => false];
        if ($untilDate !== null) {
            $options['until_date'] = $untilDate;
        }

        $this->app->make(TelegramClient::class)->banChatMember($chatId, $userId, $options);

        $this->app->make(BanRepository::class)->create([
            'chat_id'    => $chatId,
            'user_id'    => $userId,
            'reason'     => $reason,
            'banned_by'  => $bannedBy,
            'until_date' => $untilDate ? date('Y-m-d H:i:s', $untilDate) : null,
        ]);

        $this->app->make(LoggerService::class)->security(
            "BAN chat={$chatId} user={$userId} by={$bannedBy} until={$untilDate} reason={$reason}"
        );

        $this->app->make(EventDispatcher::class)->emit('member.banned', [
            'chat_id'    => $chatId,
            'user_id'    => $userId,
            'banned_by'  => $bannedBy,
            'reason'     => $reason,
            'until_date' => $untilDate,
        ]);
    }

    public function unban(int $chatId, int $userId, int $unbannedBy): void
    {
        $this->app->make(TelegramClient::class)->unbanChatMember($chatId, $userId);

        $this->app->make(BanRepository::class)->deleteForUser($chatId, $userId);

        $this->app->make(LoggerService::class)->security(
            "UNBAN chat={$chatId} user={$userId} by={$unbannedBy}"
        );

        $this->app->make(EventDispatcher::class)->emit('member.unbanned', [
            'chat_id'      => $chatId,
            'user_id'      => $userId,
            'unbanned_by'  => $unbannedBy,
        ]);
    }
}
