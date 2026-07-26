<?php
declare(strict_types=1);

namespace App\Core\Services;

/**
 * Loads and caches PHP config files from the app/config directory.
 *
 * Usage:
 *   $config->get('app.owner_ids')
 *   $config->get('telegram.parse_mode', 'HTML')
 */
class ConfigService
{
    private array $cache = [];

    public function __construct(
        private readonly string $configDir
    ) {}

    public function get(string $key, mixed $default = null): mixed
    {
        $parts   = explode('.', $key, 2);
        $file    = $parts[0];
        $subkey  = $parts[1] ?? null;
        $config  = $this->load($file);

        if ($subkey === null) {
            return $config ?? $default;
        }

        return $this->nested($config, $subkey, $default);
    }

    public function all(string $file): array
    {
        return $this->load($file);
    }

    // -------------------------------------------------------------------------

    private function load(string $file): array
    {
        if (array_key_exists($file, $this->cache)) {
            return $this->cache[$file];
        }

        $path = $this->configDir . '/' . $file . '.php';

        if (!file_exists($path)) {
            return $this->cache[$file] = [];
        }

        $result = require $path;
        return $this->cache[$file] = is_array($result) ? $result : [];
    }

    private function nested(array $array, string $key, mixed $default): mixed
    {
        $parts = explode('.', $key, 2);

        if (!array_key_exists($parts[0], $array)) {
            return $default;
        }

        if (count($parts) === 1) {
            return $array[$parts[0]];
        }

        if (!is_array($array[$parts[0]])) {
            return $default;
        }

        return $this->nested($array[$parts[0]], $parts[1], $default);
    }
}
