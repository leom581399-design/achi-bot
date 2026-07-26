<?php
declare(strict_types=1);

namespace Modules\AntiRaid\Services;

use App\Core\Application;
use App\Core\Services\{CacheService, LoggerService, SettingsService};
use App\Core\Telegram\TelegramClient;

/**
 * RaidDetectorService — detecta picos de entrada e ativa modo de raid.
 *
 * Configurações por grupo (SettingsService, módulo 'AntiRaid'):
 *   enabled    bool   — padrão: false
 *   threshold  int    — entradas na janela para disparar (padrão: 10)
 *   window     int    — janela em segundos (padrão: 60)
 *   action     string — ban|kick|mute (padrão: ban)
 *   duration   int    — duração do modo raid em minutos (padrão: 15)
 *
 * Cache keys (por grupo):
 *   raid:count:{chatId}    — número de entradas na janela atual
 *   raid:active:{chatId}   — 1 se modo raid ativo
 *   raid:expires:{chatId}  — timestamp de fim do modo raid
 */
class RaidDetectorService
{
    public function __construct(private readonly Application $app) {}

    /**
     * Registra uma entrada. Retorna true se o modo raid está (ou foi) ativado.
     */
    public function trackJoin(int $chatId): bool
    {
        if (!$this->isEnabled($chatId)) return false;

        // Se raid já ativo, retorna true diretamente
        if ($this->isRaidActive($chatId)) return true;

        $threshold = $this->getThreshold($chatId);
        $window    = $this->getWindow($chatId);

        $count = $this->cache()->increment("raid:count:{$chatId}", 1, $window);

        if ($count >= $threshold) {
            $this->activateRaid($chatId);
            return true;
        }

        return false;
    }

    /**
     * Aplica a ação de raid ao usuário (ban/kick/mute).
     */
    public function applyRaidAction(int $chatId, int $userId): void
    {
        $action = $this->getAction($chatId);
        $client = $this->app->make(TelegramClient::class);

        $this->app->make(LoggerService::class)->security(
            "RAID_ACTION chat={$chatId} user={$userId} action={$action}"
        );

        try {
            match ($action) {
                'ban'   => $client->banChatMember($chatId, $userId),
                'kick'  => $this->kick($client, $chatId, $userId),
                'mute'  => $client->restrictChatMember($chatId, $userId, ['can_send_messages' => false]),
                default => $client->banChatMember($chatId, $userId),
            };
        } catch (\Throwable) {}
    }

    // -------------------------------------------------------------------------
    // Raid mode state
    // -------------------------------------------------------------------------

    public function isRaidActive(int $chatId): bool
    {
        // Verifica se o modo expirou
        $expires = $this->cache()->get("raid:expires:{$chatId}");
        if ($expires !== null && time() > (int)$expires) {
            $this->deactivateRaid($chatId);
            return false;
        }
        return (bool)$this->cache()->get("raid:active:{$chatId}");
    }

    public function activateRaid(int $chatId): void
    {
        $duration = $this->getDuration($chatId) * 60; // minutos → segundos
        $this->cache()->set("raid:active:{$chatId}",  1,              $duration + 60);
        $this->cache()->set("raid:expires:{$chatId}", time() + $duration, $duration + 60);

        $this->app->make(LoggerService::class)->security(
            "RAID_ACTIVATED chat={$chatId} duration={$duration}s"
        );
    }

    public function deactivateRaid(int $chatId): void
    {
        $this->cache()->delete("raid:active:{$chatId}");
        $this->cache()->delete("raid:expires:{$chatId}");
        $this->cache()->delete("raid:count:{$chatId}");
    }

    public function getRemainingSeconds(int $chatId): int
    {
        $expires = $this->cache()->get("raid:expires:{$chatId}");
        if ($expires === null) return 0;
        return max(0, (int)$expires - time());
    }

    // -------------------------------------------------------------------------
    // Settings accessors
    // -------------------------------------------------------------------------

    public function isEnabled(int $chatId): bool
    {
        return (bool)$this->setting($chatId, 'enabled', false);
    }

    public function getThreshold(int $chatId): int
    {
        return max(2, (int)$this->setting($chatId, 'threshold', 10));
    }

    public function getWindow(int $chatId): int
    {
        return max(10, (int)$this->setting($chatId, 'window', 60));
    }

    public function getAction(int $chatId): string
    {
        return $this->setting($chatId, 'action', 'ban');
    }

    public function getDuration(int $chatId): int
    {
        return max(1, (int)$this->setting($chatId, 'duration', 15));
    }

    public function setEnabled(int $chatId, bool $value): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'AntiRaid', 'enabled', $value);
    }

    public function setThreshold(int $chatId, int $threshold): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'AntiRaid', 'threshold', $threshold);
    }

    public function setAction(int $chatId, string $action): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'AntiRaid', 'action', $action);
    }

    // -------------------------------------------------------------------------
    // Helpers
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
        return $this->app->make(SettingsService::class)->get($chatId, 'AntiRaid', $key, $default);
    }
}
