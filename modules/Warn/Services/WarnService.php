<?php
declare(strict_types=1);

namespace Modules\Warn\Services;

use App\Core\Application;
use App\Core\EventDispatcher;
use App\Core\Services\{LoggerService, SettingsService};
use App\Core\Telegram\TelegramClient;
use Modules\Warn\Repository\WarnRepository;

class WarnService
{
    public function __construct(private readonly Application $app) {}

    /**
     * Warn a user. Returns the new warn count.
     * If the limit is reached, applies the configured action automatically.
     */
    public function warn(int $chatId, int $userId, int $warnedBy, ?string $reason): int
    {
        $repo = $this->app->make(WarnRepository::class);

        $repo->create([
            'chat_id'   => $chatId,
            'user_id'   => $userId,
            'reason'    => $reason,
            'warned_by' => $warnedBy,
        ]);

        $count    = $repo->countForUser($chatId, $userId);
        $maxWarns = (int)$this->getSetting($chatId, 'max_warns', 3);

        $this->app->make(LoggerService::class)->security(
            "WARN chat={$chatId} user={$userId} by={$warnedBy} count={$count}/{$maxWarns}"
        );

        $this->app->make(EventDispatcher::class)->emit('member.warned', [
            'chat_id'   => $chatId,
            'user_id'   => $userId,
            'warned_by' => $warnedBy,
            'reason'    => $reason,
            'count'     => $count,
            'max'       => $maxWarns,
        ]);

        if ($count >= $maxWarns) {
            $this->applyLimitAction($chatId, $userId, $warnedBy);
            $repo->resetForUser($chatId, $userId);

            $this->app->make(EventDispatcher::class)->emit('member.warn_limit', [
                'chat_id'  => $chatId,
                'user_id'  => $userId,
                'action'   => $this->getSetting($chatId, 'warn_action', 'ban'),
            ]);
        }

        return $count;
    }

    public function unwarn(int $chatId, int $userId): bool
    {
        return $this->app->make(WarnRepository::class)->deleteLatest($chatId, $userId);
    }

    public function resetWarns(int $chatId, int $userId): int
    {
        return $this->app->make(WarnRepository::class)->resetForUser($chatId, $userId);
    }

    public function getWarnCount(int $chatId, int $userId): int
    {
        return $this->app->make(WarnRepository::class)->countForUser($chatId, $userId);
    }

    public function getWarns(int $chatId, int $userId): array
    {
        return $this->app->make(WarnRepository::class)->findAllForUser($chatId, $userId);
    }

    public function getMaxWarns(int $chatId): int
    {
        return (int)$this->getSetting($chatId, 'max_warns', 3);
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    private function applyLimitAction(int $chatId, int $userId, int $by): void
    {
        $action   = $this->getSetting($chatId, 'warn_action', 'ban');
        $muteTime = (int)$this->getSetting($chatId, 'warn_mute_time', 3600);
        $client   = $this->app->make(TelegramClient::class);

        try {
            match($action) {
                'ban'   => $client->banChatMember($chatId, $userId),
                'kick'  => $this->kickUser($client, $chatId, $userId),
                'mute'  => $client->restrictChatMember($chatId, $userId, ['can_send_messages' => false]),
                'tmute' => $client->restrictChatMember($chatId, $userId, ['can_send_messages' => false], [
                    'until_date' => time() + $muteTime,
                ]),
                default => $client->banChatMember($chatId, $userId),
            };
        } catch (\Throwable $e) {
            $this->app->make(LoggerService::class)->error(
                "WarnService: failed to apply limit action ({$action}) on user {$userId}: " . $e->getMessage()
            );
        }
    }

    private function kickUser(TelegramClient $client, int $chatId, int $userId): void
    {
        $client->banChatMember($chatId, $userId);
        $client->unbanChatMember($chatId, $userId);
    }

    private function getSetting(int $chatId, string $key, mixed $default): mixed
    {
        if (!$this->app->has(SettingsService::class)) return $default;
        return $this->app->make(SettingsService::class)->get($chatId, 'Warn', $key, $default);
    }
}
