<?php
declare(strict_types=1);

namespace App\Core\Services;

use App\Core\Database\QueryBuilder;

/**
 * Per-group, per-module settings with in-memory cache.
 *
 * Each setting is stored as (chat_id, module, key, value) in group_settings.
 * Modules declare their own defaults; the service merges defaults with stored values.
 *
 * Usage:
 *   $settings = $app->make(SettingsService::class);
 *
 *   $settings->get($chatId, 'Welcome', 'enabled', default: true);
 *   $settings->set($chatId, 'Welcome', 'enabled', false);
 *   $settings->all($chatId, 'Welcome');    // → ['enabled' => false, ...]
 *   $settings->reset($chatId, 'Welcome'); // removes stored, reverts to defaults
 */
class SettingsService
{
    /** In-memory cache: [chatId][module][key] → value */
    private array $cache = [];

    public function __construct(
        private readonly DatabaseService $db
    ) {}

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    /**
     * Get a single setting value.
     * Returns stored value if present, otherwise $default.
     */
    public function get(int $chatId, string $module, string $key, mixed $default = null): mixed
    {
        $this->loadModule($chatId, $module);

        if (array_key_exists($key, $this->cache[$chatId][$module] ?? [])) {
            return $this->decode($this->cache[$chatId][$module][$key]);
        }

        return $default;
    }

    /**
     * Store a setting. The value is JSON-encoded so any scalar / array is accepted.
     */
    public function set(int $chatId, string $module, string $key, mixed $value): void
    {
        $encoded = $this->encode($value);

        // Upsert
        $driver = $this->db->driver();

        if ($driver === 'pgsql') {
            $this->db->statement(
                "INSERT INTO group_settings (chat_id, module, key, value)
                 VALUES (:c, :m, :k, :v)
                 ON CONFLICT (chat_id, module, key) DO UPDATE SET value = EXCLUDED.value",
                [':c' => $chatId, ':m' => $module, ':k' => $key, ':v' => $encoded]
            );
        } else {
            // SQLite
            $this->db->statement(
                "INSERT OR REPLACE INTO group_settings (chat_id, module, key, value)
                 VALUES (:c, :m, :k, :v)",
                [':c' => $chatId, ':m' => $module, ':k' => $key, ':v' => $encoded]
            );
        }

        // Invalidate cache for this key
        if (isset($this->cache[$chatId][$module])) {
            $this->cache[$chatId][$module][$key] = $encoded;
        }
    }

    /**
     * Return all stored settings for a module in a given chat.
     * Does NOT merge with module defaults — callers must provide their own defaults.
     */
    public function all(int $chatId, string $module): array
    {
        $this->loadModule($chatId, $module);

        $result = [];
        foreach ($this->cache[$chatId][$module] ?? [] as $key => $encoded) {
            $result[$key] = $this->decode($encoded);
        }

        return $result;
    }

    /**
     * Remove all stored settings for a module in a given chat.
     * The module will fall back to its declared defaults on next read.
     */
    public function reset(int $chatId, string $module): void
    {
        $this->db->table('group_settings')
            ->where('chat_id', $chatId)
            ->where('module', $module)
            ->delete();

        unset($this->cache[$chatId][$module]);
    }

    /**
     * Remove a single setting (revert to default).
     */
    public function forget(int $chatId, string $module, string $key): void
    {
        $this->db->table('group_settings')
            ->where('chat_id', $chatId)
            ->where('module', $module)
            ->where('key', $key)
            ->delete();

        unset($this->cache[$chatId][$module][$key]);
    }

    /**
     * Invalidate the in-memory cache for a specific chat (or all chats).
     */
    public function invalidate(?int $chatId = null, ?string $module = null): void
    {
        if ($chatId === null) {
            $this->cache = [];
        } elseif ($module === null) {
            unset($this->cache[$chatId]);
        } else {
            unset($this->cache[$chatId][$module]);
        }
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    /**
     * Load all settings for (chat_id, module) into the in-memory cache
     * if they haven't been loaded yet.
     */
    private function loadModule(int $chatId, string $module): void
    {
        if (isset($this->cache[$chatId][$module])) {
            return; // already loaded
        }

        $rows = $this->db->table('group_settings')
            ->where('chat_id', $chatId)
            ->where('module', $module)
            ->get();

        $this->cache[$chatId][$module] = [];

        foreach ($rows as $row) {
            $this->cache[$chatId][$module][$row['key']] = $row['value'];
        }
    }

    private function encode(mixed $value): string
    {
        return json_encode($value, JSON_UNESCAPED_UNICODE);
    }

    private function decode(string $encoded): mixed
    {
        return json_decode($encoded, true);
    }
}
