<?php
declare(strict_types=1);

namespace App\Core\Services;

use App\Core\Application;

/**
 * Internationalisation / localisation service.
 *
 * ACHI BOT — asosiy til O'ZBEK (uz), qo'shimcha til RUS (ru). Har bir
 * modul boot() ichida load() chaqirib o'zining Language/ papkasidagi
 * BARCHA qo'llab-quvvatlanadigan tillarni (uz.php, ru.php) darrov
 * xotiraga yuklaydi — chunki til guruhdan-guruhga farq qilishi mumkin
 * (/til buyrug'i orqali), shu sabab faqat "joriy" tilni saqlab qolish
 * yetarli emas.
 *
 * Har bir chaqiruvda Router (yoki chaqiruvchi kod) setLocale() orqali
 * "joriy so'rov uchun qaysi til" ekanini belgilaydi (guruhning
 * SettingsService'da saqlangan tanlovi asosida).
 *
 * Language fayllari oddiy PHP massiv qaytaradi:
 *   return ['key' => "Salom, :name!"];
 */
class LanguageService
{
    /** Qo'llab-quvvatlanadigan barcha tillar (fayl nomlari bilan mos). */
    public const SUPPORTED_LOCALES = ['uz', 'ru'];

    /** Hech qanday tarjima topilmasa, oxirgi chora sifatida shu tilga qaraladi. */
    public const FALLBACK_LOCALE = 'uz';

    private string $locale;

    /** @var array<string, array<string, array<string, string>>> locale => module => [key => string] */
    private array $strings = [];

    public function __construct(
        Application $app,
        string $locale = ''
    ) {
        $config       = $app->make(ConfigService::class);
        $this->locale = $locale ?: ($config->get('app.locale', self::FALLBACK_LOCALE));
    }

    public function setLocale(string $locale): void
    {
        $this->locale = in_array($locale, self::SUPPORTED_LOCALES, true) ? $locale : self::FALLBACK_LOCALE;
    }

    public function getLocale(): string
    {
        return $this->locale;
    }

    /**
     * Modulning Language/ papkasidagi BARCHA qo'llab-quvvatlanadigan til
     * fayllarini (uz.php, ru.php) darrov yuklab, xotiraga oladi.
     *
     * @param string $module  Modul nomi (masalan 'Ban') — kalitlar shu
     *                        nom ostida saqlanadi ('Ban.banned' kabi).
     * @param string $langDir Language/ papkasiga to'liq yo'l
     */
    public function load(string $module, string $langDir): void
    {
        foreach (self::SUPPORTED_LOCALES as $locale) {
            $file = $langDir . '/' . $locale . '.php';
            if (!file_exists($file)) {
                continue;
            }

            $strings = require $file;
            if (is_array($strings)) {
                $this->strings[$locale][$module] = array_merge(
                    $this->strings[$locale][$module] ?? [],
                    $strings
                );
            }
        }
    }

    /**
     * Kalitni tarjima qilib, :placeholder'larni almashtiradi.
     *
     * @param string      $key          'ModuleName.key' yoki faqat 'key' ($module berilgan bo'lsa)
     * @param array       $replacements [':name' => 'Aziz'] yoki ['name' => 'Aziz']
     * @param string|null $module       Modul nomini majburan belgilash
     */
    public function trans(string $key, array $replacements = [], ?string $module = null): string
    {
        $parts  = explode('.', $key, 2);
        $mod    = $module ?? (isset($parts[1]) ? $parts[0] : null);
        $msgKey = isset($parts[1]) ? $parts[1] : $key;

        $string = $this->lookup($this->locale, $mod, $msgKey)
            ?? $this->lookup(self::FALLBACK_LOCALE, $mod, $msgKey)
            ?? $key;

        foreach ($replacements as $placeholder => $value) {
            $ph     = str_starts_with((string)$placeholder, ':') ? $placeholder : ':' . $placeholder;
            $string = str_replace($ph, (string)$value, $string);
        }

        return $string;
    }

    private function lookup(string $locale, ?string $module, string $key): ?string
    {
        if ($module === null) {
            return null;
        }
        return $this->strings[$locale][$module][$key] ?? null;
    }
}
