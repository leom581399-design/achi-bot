<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateUsersTable implements Migration
{
    public function version(): int { return 2; }

    public function description(): string { return 'Create users table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS users (
                    id         BIGINT PRIMARY KEY,
                    first_name TEXT,
                    last_name  TEXT,
                    username   TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS users (
                    id         INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name  TEXT,
                    username   TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ");
        }
    }

    public function down(PDO $pdo): void
    {
        $pdo->exec('DROP TABLE IF EXISTS users');
    }
}
