<?php
declare(strict_types=1);

namespace Modules\Flood\Services;

use App\Core\Application;
use App\Core\Services\{CacheService, LoggerService, SettingsService};
use App\Core\Telegram\TelegramClient;

/**
 * FloodService — rastreia mensagens por usuário/grupo e aplica ação ao atingir o limite.
 *
 * Configurações por grupo (SettingsService, módulo 'Flood'):
 *   limit      int    — número máximo de msgs na janela (0 = desativado, padrão 0)
 *   window     int    — janela em segundos (padrão 10)
 *   action     string — warn|mute|kick|ban|tban|tmute (padrão mute)
 *   mute_time  int    — segundos para tmute/tban (padrão 600)
 */
class FloodService
{
    public function __construct(private readonly Application $app) {}

    /**
     * Registra uma mensagem do usuário. Retorna true se o limite foi atingido.
     */
    public function track(int $chatId, int $userId): bool
    {
        $limit = $this->getLimit($chatId);
        if ($limit === 0) return false;

        $window = $this->getWindow($chatId);
        $key    = "flood:{$chatId}:{$userId}";
        $count  = $this->cache()->increment($key, 1, $window);

        return $count >= $limit;
    }

    /**
     * Zera o contador do usuário (após aplicar a ação).
     */
    public function reset(int $chatId, int $userId): void
    {
        $this->cache()->delete("flood:{$chatId}:{$userId}");
    }

    /**
     * Aplica a ação configurada ao usuário que flooded.
     */
    public function applyAction(int $chatId, int $userId): void
    {
        $action   = $this->getAction($chatId);
        $muteTime = $this->getMuteTime($chatId);
        $client   = $this->app->make(TelegramClient::class);

        $this->app->make(LoggerService::class)->security(
            "FLOOD chat={$chatId} user={$userId} action={$action}"
        );

        try {
            match ($action) {
                'ban'   => $client->banChatMember($chatId, $userId),
                'tban'  => $client->banChatMember($chatId, $userId, ['until_date' => time() + $muteTime]),
                'kick'  => $this->kick($client, $chatId, $userId),
                'mute'  => $client->restrictChatMember($chatId, $userId, ['can_send_messages' => false]),
                'tmute' => $client->restrictChatMember($chatId, $userId, ['can_send_messages' => false], ['until_date' => time() + $muteTime]),
                default => $client->restrictChatMember($chatId, $userId, ['can_send_messages' => false]),
            };
        } catch (\Throwable $e) {
            $this->app->make(LoggerService::class)->error(
                "FloodService: applyAction failed for user {$userId}: " . $e->getMessage()
            );
        }
    }

    // -------------------------------------------------------------------------
    // Settings accessors
    // -------------------------------------------------------------------------

    public function getLimit(int $chatId): int
    {
        return (int) $this->setting($chatId, 'limit', 0);
    }

    public function getWindow(int $chatId): int
    {
        return max(1, (int) $this->setting($chatId, 'window', 10));
    }

    public function getAction(int $chatId): string
    {
        return $this->setting($chatId, 'action', 'mute');
    }

    public function getMuteTime(int $chatId): int
    {
        return max(30, (int) $this->setting($chatId, 'mute_time', 600));
    }

    public function setLimit(int $chatId, int $limit): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Flood', 'limit', $limit);
    }

    public function setAction(int $chatId, string $action): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Flood', 'action', $action);
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    private function kick(TelegramClient $client, int $chatId, int $userId): void
    {
        $client->banChatMember($chatId, $userId);
        $client->unbanChatMember($chatId, $userId);
    }

    private function cache(): CacheService
    {
        return $this->app->make(CacheService::class);
    }

    private function setting(int $chatId, string $key, mixed $default): mixed
    {
        if (!$this->app->has(SettingsService::class)) return $default;
        return $this->app->make(SettingsService::class)->get($chatId, 'Flood', $key, $default);
    }
}
