<?php
declare(strict_types=1);

namespace App\Core\Helper;

/**
 * Parses human-readable duration strings into seconds.
 *
 * Supported units: d (days), h (hours), m (minutes), s (seconds)
 *
 * Examples:
 *   "1d"      → 86400
 *   "2h30m"   → 9000
 *   "30m"     → 1800
 *   "1d2h30m" → 95400
 *   "0"       → 0  (permanent / no expiry)
 *
 * Usage:
 *   [$seconds, $remainingArgs] = DurationParser::parse("1d reason text");
 *   // $seconds = 86400, $remainingArgs = "reason text"
 */
class DurationParser
{
    private const PATTERN = '/^(\d+d)?(\d+h)?(\d+m)?(\d+s)?$/i';

    /**
     * Try to extract a duration from the beginning of $args.
     *
     * Returns [int $seconds, string $remainingArgs]:
     *  - $seconds = 0 means no duration token found → treat as permanent
     *  - $remainingArgs is the rest of the string after the duration token
     */
    public static function parse(string $args): array
    {
        $parts     = explode(' ', trim($args), 2);
        $token     = $parts[0] ?? '';
        $remaining = trim($parts[1] ?? '');

        if ($token === '0') {
            return [0, $remaining];
        }

        if (!preg_match(self::PATTERN, $token) || $token === '') {
            // First token is not a duration string → return 0 and keep full args
            return [0, trim($args)];
        }

        $seconds = 0;

        if (preg_match('/(\d+)d/i', $token, $m)) $seconds += (int)$m[1] * 86400;
        if (preg_match('/(\d+)h/i', $token, $m)) $seconds += (int)$m[1] * 3600;
        if (preg_match('/(\d+)m/i', $token, $m)) $seconds += (int)$m[1] * 60;
        if (preg_match('/(\d+)s/i', $token, $m)) $seconds += (int)$m[1];

        return [$seconds, $remaining];
    }

    /**
     * Format seconds into a human-readable string.
     * e.g. 3661 → "1h 1m 1s"
     */
    public static function format(int $seconds): string
    {
        if ($seconds <= 0) return '∞';

        $parts = [];

        $d = intdiv($seconds, 86400);
        $h = intdiv($seconds % 86400, 3600);
        $m = intdiv($seconds % 3600, 60);
        $s = $seconds % 60;

        if ($d > 0) $parts[] = "{$d}d";
        if ($h > 0) $parts[] = "{$h}h";
        if ($m > 0) $parts[] = "{$m}m";
        if ($s > 0 && $d === 0) $parts[] = "{$s}s";

        return implode(' ', $parts);
    }
}
