<?php
declare(strict_types=1);

namespace App\Core\Services;

use App\Core\Application;

/**
 * Internationalisation / localisation service.
 *
 * Each module calls load() in its boot() to register its strings.
 * Commands call trans() to get localised text.
 *
 * Language files return a plain PHP array:
 *   return ['key' => 'Hello, :name!'];
 */
class LanguageService
{
    private string $locale;

    /** @var array<string, array<string, string>> module => [key => string] */
    private array $strings = [];

    public function __construct(
        Application $app,
        string $locale = ''
    ) {
        $config       = $app->make(ConfigService::class);
        $this->locale = $locale ?: ($config->get('app.locale', 'en_US'));
    }

    public function setLocale(string $locale): void
    {
        $this->locale = $locale;
    }

    public function getLocale(): string
    {
        return $this->locale;
    }

    /**
     * Register a module's language directory.
     *
     * @param string $module  Module name used as namespace prefix (e.g. 'Help')
     * @param string $langDir Absolute path to the Language/ directory
     */
    public function load(string $module, string $langDir): void
    {
        // Try requested locale, fall back to en_US
        $file = $langDir . '/' . $this->locale . '.php';
        if (!file_exists($file)) {
            $file = $langDir . '/en_US.php';
        }
        if (!file_exists($file)) return;

        $strings = require $file;
        if (is_array($strings)) {
            $this->strings[$module] = array_merge($this->strings[$module] ?? [], $strings);
        }
    }

    /**
     * Translate a key and interpolate :placeholders.
     *
     * @param string      $key          'ModuleName.key' or just 'key' (with $module set)
     * @param array       $replacements [':name' => 'John'] or ['name' => 'John']
     * @param string|null $module       Override module namespace
     */
    public function trans(string $key, array $replacements = [], ?string $module = null): string
    {
        $parts  = explode('.', $key, 2);
        $mod    = $module ?? ($parts[1] !== '' ? $parts[0] : null);
        $msgKey = isset($parts[1]) ? $parts[1] : $key;

        $string = ($mod !== null ? $this->strings[$mod][$msgKey] ?? null : null) ?? $key;

        foreach ($replacements as $placeholder => $value) {
            $ph     = str_starts_with((string)$placeholder, ':') ? $placeholder : ':' . $placeholder;
            $string = str_replace($ph, (string)$value, $string);
        }

        return $string;
    }
}
