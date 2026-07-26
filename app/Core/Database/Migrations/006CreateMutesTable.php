<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateMutesTable implements Migration
{
    public function version(): int { return 6; }
    public function description(): string { return 'Create mutes table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS mutes (
                    id         SERIAL PRIMARY KEY,
                    chat_id    BIGINT NOT NULL,
                    user_id    BIGINT NOT NULL,
                    reason     TEXT,
                    muted_by   BIGINT NOT NULL,
                    until_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS mutes (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id    INTEGER NOT NULL,
                    user_id    INTEGER NOT NULL,
                    reason     TEXT,
                    muted_by   INTEGER NOT NULL,
                    until_date TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ");
        }

        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_mutes_chat_user ON mutes(chat_id, user_id)');
    }

    public function down(PDO $pdo): void { $pdo->exec('DROP TABLE IF EXISTS mutes'); }
}
