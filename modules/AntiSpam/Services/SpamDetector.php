<?php
declare(strict_types=1);

namespace Modules\AntiSpam\Services;

use App\Core\Application;
use App\Core\Services\{CacheService, LoggerService, SettingsService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * SpamDetector — detecta spam e verifica o banco CAS (Combot Anti-Spam).
 *
 * Configurações por grupo (SettingsService, módulo 'AntiSpam'):
 *   enabled        bool — padrão: true
 *   cas_check      bool — verificar CAS ao entrar (padrão: true)
 *   max_links      int  — máximo de links por mensagem (padrão: 3)
 *   block_forwards bool — bloquear forwards de canais desconhecidos (padrão: false)
 */
class SpamDetector
{
    private const CAS_API = 'https://api.cas.chat/check?user_id=';

    public function __construct(private readonly Application $app) {}

    // -------------------------------------------------------------------------
    // CAS check
    // -------------------------------------------------------------------------

    /**
     * Verifica se o userId está banido no CAS.
     * Retorna true se banido.
     */
    public function isCasBanned(int $userId): bool
    {
        $cacheKey = "cas:check:{$userId}";
        $cached   = $this->cache()->get($cacheKey);
        if ($cached !== null) return (bool)$cached;

        try {
            $url     = self::CAS_API . $userId;
            $ctx     = stream_context_create(['http' => ['timeout' => 5, 'ignore_errors' => true]]);
            $body    = @file_get_contents($url, false, $ctx);
            $data    = $body ? json_decode($body, true) : null;
            $banned  = ($data['ok'] ?? false) === true;
        } catch (\Throwable) {
            $banned = false;
        }

        // Cache por 6 horas (não banido) ou 24 horas (banido)
        $this->cache()->set($cacheKey, $banned, $banned ? 86400 : 21600);
        return $banned;
    }

    /**
     * Bane o usuário da CAS em todos os grupos onde for detectado.
     */
    public function banCasUser(int $chatId, int $userId, string $name): void
    {
        $client = $this->app->make(TelegramClient::class);
        try {
            $client->banChatMember($chatId, $userId);
        } catch (\Throwable) {}

        $this->app->make(LoggerService::class)->security(
            "CAS_BAN chat={$chatId} user={$userId} name={$name}"
        );
    }

    // -------------------------------------------------------------------------
    // Message spam detection
    // -------------------------------------------------------------------------

    /**
     * Analisa a mensagem e retorna o tipo de spam detectado, ou null se limpa.
     * Possíveis valores: 'links', 'repeated'
     */
    public function detectSpam(Update $update, int $chatId, int $userId): ?string
    {
        $maxLinks = (int)$this->setting($chatId, 'max_links', 3);

        // Verifica links na mensagem
        $linkCount = 0;
        foreach ($update->getEntities() as $entity) {
            if (in_array($entity['type'], ['url', 'text_link'], true)) {
                $linkCount++;
            }
        }
        if ($linkCount > $maxLinks) return 'links';

        // Verifica mensagens repetidas (cache de hash por usuário)
        $text = $update->getText();
        if ($text !== null && strlen($text) > 10) {
            $hash     = md5(strtolower(trim($text)));
            $cacheKey = "spam:repeat:{$chatId}:{$userId}:{$hash}";
            $count    = $this->cache()->increment($cacheKey, 1, 30);
            if ($count >= 3) {
                $this->cache()->delete($cacheKey);
                return 'repeated';
            }
        }

        return null;
    }

    /**
     * Remove a mensagem spam e aplica uma advertência ao usuário.
     */
    public function handleSpam(int $chatId, int $userId, ?int $messageId, string $type): void
    {
        $client = $this->app->make(TelegramClient::class);

        // Deleta a mensagem
        if ($messageId !== null) {
            try { $client->deleteMessage($chatId, $messageId); } catch (\Throwable) {}
        }

        $this->app->make(LoggerService::class)->security(
            "SPAM chat={$chatId} user={$userId} type={$type}"
        );
    }

    // -------------------------------------------------------------------------
    // Settings
    // -------------------------------------------------------------------------

    public function isEnabled(int $chatId): bool
    {
        return (bool)$this->setting($chatId, 'enabled', true);
    }

    public function isCasCheckEnabled(int $chatId): bool
    {
        return (bool)$this->setting($chatId, 'cas_check', true);
    }

    public function setEnabled(int $chatId, bool $value): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'AntiSpam', 'enabled', $value);
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private function cache(): CacheService
    {
        return $this->app->make(CacheService::class);
    }

    private function setting(int $chatId, string $key, mixed $default): mixed
    {
        if (!$this->app->has(SettingsService::class)) return $default;
        return $this->app->make(SettingsService::class)->get($chatId, 'AntiSpam', $key, $default);
    }
}
