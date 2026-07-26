<?php
declare(strict_types=1);

namespace App\Core\Services;

/**
 * Simple filesystem-based cache.
 *
 * Designed to be swapped for Redis/APCu without changing modules.
 * All modules access cache only through this service — never directly.
 */
class CacheService
{
    public function __construct(
        private readonly string $cacheDir
    ) {
        if (!is_dir($cacheDir)) {
            mkdir($cacheDir, 0755, true);
        }
    }

    public function get(string $key, mixed $default = null): mixed
    {
        $path = $this->path($key);
        if (!file_exists($path)) return $default;

        $data = unserialize(file_get_contents($path));

        if ($data['expires'] !== null && $data['expires'] < time()) {
            @unlink($path);
            return $default;
        }

        return $data['value'];
    }

    public function set(string $key, mixed $value, ?int $ttl = null): void
    {
        file_put_contents($this->path($key), serialize([
            'value'   => $value,
            'expires' => $ttl !== null ? time() + $ttl : null,
        ]), LOCK_EX);
    }

    public function has(string $key): bool
    {
        return $this->get($key) !== null;
    }

    public function delete(string $key): void
    {
        $path = $this->path($key);
        if (file_exists($path)) @unlink($path);
    }

    /** Increment an integer value atomically (approximate — filesystem based). */
    public function increment(string $key, int $by = 1, ?int $ttl = null): int
    {
        $current = (int)($this->get($key) ?? 0);
        $new     = $current + $by;
        $this->set($key, $new, $ttl);
        return $new;
    }

    public function flush(): void
    {
        foreach (glob($this->cacheDir . '/*.cache') ?: [] as $file) {
            @unlink($file);
        }
    }

    private function path(string $key): string
    {
        return $this->cacheDir . '/' . md5($key) . '.cache';
    }
}
