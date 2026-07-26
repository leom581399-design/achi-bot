<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateWarnsTable implements Migration
{
    public function version(): int { return 7; }
    public function description(): string { return 'Create warns table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS warns (
                    id         SERIAL PRIMARY KEY,
                    chat_id    BIGINT NOT NULL,
                    user_id    BIGINT NOT NULL,
                    reason     TEXT,
                    warned_by  BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS warns (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id    INTEGER NOT NULL,
                    user_id    INTEGER NOT NULL,
                    reason     TEXT,
                    warned_by  INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ");
        }

        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_warns_chat_user ON warns(chat_id, user_id)');
    }

    public function down(PDO $pdo): void { $pdo->exec('DROP TABLE IF EXISTS warns'); }
}
