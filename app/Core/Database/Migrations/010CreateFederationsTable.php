<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateFederationsTable implements Migration
{
    public function version(): int { return 10; }
    public function description(): string { return 'Create federations, fed_chats and fed_bans tables'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS federations (
                    id         SERIAL PRIMARY KEY,
                    fed_id     VARCHAR(36) NOT NULL UNIQUE,
                    name       VARCHAR(255) NOT NULL,
                    owner_id   BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ");
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS fed_chats (
                    id         SERIAL PRIMARY KEY,
                    fed_id     VARCHAR(36) NOT NULL,
                    chat_id    BIGINT NOT NULL,
                    joined_by  BIGINT NOT NULL,
                    joined_at  TIMESTAMP DEFAULT NOW(),
                    UNIQUE (fed_id, chat_id)
                )
            ");
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS fed_bans (
                    id         SERIAL PRIMARY KEY,
                    fed_id     VARCHAR(36) NOT NULL,
                    user_id    BIGINT NOT NULL,
                    reason     TEXT,
                    banned_by  BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE (fed_id, user_id)
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS federations (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    fed_id     TEXT NOT NULL UNIQUE,
                    name       TEXT NOT NULL,
                    owner_id   INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ");
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS fed_chats (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    fed_id    TEXT NOT NULL,
                    chat_id   INTEGER NOT NULL,
                    joined_by INTEGER NOT NULL,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (fed_id, chat_id)
                )
            ");
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS fed_bans (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    fed_id     TEXT NOT NULL,
                    user_id    INTEGER NOT NULL,
                    reason     TEXT,
                    banned_by  INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (fed_id, user_id)
                )
            ");
        }

        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_federations_owner  ON federations(owner_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_fed_chats_fed       ON fed_chats(fed_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_fed_chats_chat      ON fed_chats(chat_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_fed_bans_fed        ON fed_bans(fed_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_fed_bans_user       ON fed_bans(user_id)');
    }

    public function down(PDO $pdo): void
    {
        $pdo->exec('DROP TABLE IF EXISTS fed_bans');
        $pdo->exec('DROP TABLE IF EXISTS fed_chats');
        $pdo->exec('DROP TABLE IF EXISTS federations');
    }
}
