<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateFiltersTable implements Migration
{
    public function version(): int { return 9; }
    public function description(): string { return 'Create filters table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS filters (
                    id         SERIAL PRIMARY KEY,
                    chat_id    BIGINT NOT NULL,
                    keyword    VARCHAR(200) NOT NULL,
                    response   TEXT NOT NULL,
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE (chat_id, keyword)
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS filters (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id    INTEGER NOT NULL,
                    keyword    TEXT NOT NULL,
                    response   TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (chat_id, keyword)
                )
            ");
        }

        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_filters_chat ON filters(chat_id)');
    }

    public function down(PDO $pdo): void { $pdo->exec('DROP TABLE IF EXISTS filters'); }
}
