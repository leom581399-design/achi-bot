<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateMessageStatsTable implements Migration
{
    public function version(): int { return 11; }
    public function description(): string { return 'Create message_stats table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS message_stats (
                    id         SERIAL PRIMARY KEY,
                    chat_id    BIGINT NOT NULL,
                    user_id    BIGINT NOT NULL,
                    msg_count  INTEGER NOT NULL DEFAULT 1,
                    last_seen  TIMESTAMP DEFAULT NOW(),
                    UNIQUE (chat_id, user_id)
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS message_stats (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id   INTEGER NOT NULL,
                    user_id   INTEGER NOT NULL,
                    msg_count INTEGER NOT NULL DEFAULT 1,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (chat_id, user_id)
                )
            ");
        }

        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_msg_stats_chat ON message_stats(chat_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_msg_stats_count ON message_stats(chat_id, msg_count DESC)');
    }

    public function down(PDO $pdo): void
    {
        $pdo->exec('DROP TABLE IF EXISTS message_stats');
    }
}
