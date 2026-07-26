<?php
declare(strict_types=1);

namespace App\Core\Database;

use PDO;
use PDOException;

/**
 * Manages a single PDO connection.
 *
 * - If DATABASE_URL env var is set  → PostgreSQL (production)
 * - Otherwise                       → SQLite at storage/database.sqlite (development)
 */
class Connection
{
    private static ?PDO $pdo = null;

    public static function get(string $storageDir = ''): PDO
    {
        if (self::$pdo !== null) {
            return self::$pdo;
        }

        $dsn = getenv('DATABASE_URL');

        if ($dsn) {
            self::$pdo = self::connectPostgres($dsn);
        } else {
            self::$pdo = self::connectSqlite($storageDir);
        }

        return self::$pdo;
    }

    private static function connectPostgres(string $databaseUrl): PDO
    {
        // Convert postgres://user:pass@host:port/db to PDO DSN
        $parsed = parse_url($databaseUrl);

        $host   = $parsed['host']     ?? 'localhost';
        $port   = $parsed['port']     ?? 5432;
        $dbname = ltrim($parsed['path'] ?? '/telegram', '/');
        $user   = $parsed['user']     ?? '';
        $pass   = $parsed['pass']     ?? '';

        $pdoDsn = "pgsql:host={$host};port={$port};dbname={$dbname}";

        $pdo = new PDO($pdoDsn, $user, $pass, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);

        return $pdo;
    }

    private static function connectSqlite(string $storageDir): PDO
    {
        if (empty($storageDir)) {
            $storageDir = __DIR__ . '/../../../storage';
        }

        if (!is_dir($storageDir)) {
            mkdir($storageDir, 0755, true);
        }

        $file = rtrim($storageDir, '/') . '/database.sqlite';

        $pdo = new PDO("sqlite:{$file}", '', '', [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);

        // Enable WAL mode and foreign keys for SQLite
        $pdo->exec('PRAGMA journal_mode=WAL');
        $pdo->exec('PRAGMA foreign_keys=ON');

        return $pdo;
    }

    public static function driver(): string
    {
        return self::get()->getAttribute(PDO::ATTR_DRIVER_NAME);
    }

    /** Reset the singleton (useful for testing). */
    public static function reset(): void
    {
        self::$pdo = null;
    }
}
