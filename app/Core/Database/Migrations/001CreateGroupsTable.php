<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateGroupsTable implements Migration
{
    public function version(): int { return 1; }

    public function description(): string { return 'Create groups table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS groups (
                    id         BIGINT PRIMARY KEY,
                    title      TEXT,
                    username   TEXT,
                    settings   JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS groups (
                    id         INTEGER PRIMARY KEY,
                    title      TEXT,
                    username   TEXT,
                    settings   TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ");
        }
    }

    public function down(PDO $pdo): void
    {
        $pdo->exec('DROP TABLE IF EXISTS groups');
    }
}
