<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateSettingsTable implements Migration
{
    public function version(): int { return 4; }

    public function description(): string { return 'Create group_settings table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS group_settings (
                    id      SERIAL PRIMARY KEY,
                    chat_id BIGINT NOT NULL,
                    module  VARCHAR(50) NOT NULL,
                    key     VARCHAR(100) NOT NULL,
                    value   TEXT,
                    UNIQUE (chat_id, module, key)
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS group_settings (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    module  TEXT NOT NULL,
                    key     TEXT NOT NULL,
                    value   TEXT,
                    UNIQUE (chat_id, module, key)
                )
            ");
        }

        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_settings_chat ON group_settings(chat_id, module)');
    }

    public function down(PDO $pdo): void
    {
        $pdo->exec('DROP TABLE IF EXISTS group_settings');
    }
}
