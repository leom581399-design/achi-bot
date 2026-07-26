<?php
declare(strict_types=1);

namespace Modules\Locks\Services;

use App\Core\Application;
use App\Core\Services\SettingsService;

/**
 * LockService — gerencia quais tipos de mensagem estão bloqueados por grupo.
 *
 * Os locks são armazenados no SettingsService como um array JSON sob a chave 'locks'.
 *
 * Tipos suportados:
 *   text, media, sticker, gif, url, forward, poll, photo, video, voice,
 *   button, inline, contact, location, game, all
 */
class LockService
{
    /** Todos os tipos de lock válidos */
    public const VALID_TYPES = [
        'text', 'media', 'sticker', 'gif', 'url', 'forward', 'poll',
        'photo', 'video', 'voice', 'button', 'inline', 'contact',
        'location', 'game', 'all',
    ];

    public function __construct(private readonly Application $app) {}

    /** Retorna os tipos atualmente bloqueados no chat. */
    public function getLockedTypes(int $chatId): array
    {
        return $this->app->make(SettingsService::class)
            ->get($chatId, 'Locks', 'locks', default: []);
    }

    /** Verifica se um tipo específico está bloqueado. */
    public function isLocked(int $chatId, string $type): bool
    {
        $locks = $this->getLockedTypes($chatId);
        return in_array('all', $locks, true) || in_array($type, $locks, true);
    }

    /** Adiciona um lock. Retorna false se o tipo já estava bloqueado. */
    public function lock(int $chatId, string $type): bool
    {
        if (!in_array($type, self::VALID_TYPES, true)) {
            return false;
        }

        $settings = $this->app->make(SettingsService::class);
        $locks    = $settings->get($chatId, 'Locks', 'locks', default: []);

        if (in_array($type, $locks, true)) {
            return false; // já bloqueado
        }

        // 'all' implica todos os outros
        if ($type === 'all') {
            $locks = ['all'];
        } else {
            $locks[] = $type;
            $locks   = array_values(array_unique($locks));
        }

        $settings->set($chatId, 'Locks', 'locks', $locks);
        return true;
    }

    /** Remove um lock. Retorna false se não estava bloqueado. */
    public function unlock(int $chatId, string $type): bool
    {
        $settings = $this->app->make(SettingsService::class);
        $locks    = $settings->get($chatId, 'Locks', 'locks', default: []);

        if (!in_array($type, $locks, true)) {
            return false;
        }

        $locks = array_values(array_filter($locks, fn($t) => $t !== $type));
        $settings->set($chatId, 'Locks', 'locks', $locks);
        return true;
    }

    /** Remove todos os locks. */
    public function unlockAll(int $chatId): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Locks', 'locks', []);
    }
}
