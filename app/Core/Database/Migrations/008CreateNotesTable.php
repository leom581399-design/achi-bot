<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateNotesTable implements Migration
{
    public function version(): int { return 8; }
    public function description(): string { return 'Create notes table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS notes (
                    id         SERIAL PRIMARY KEY,
                    chat_id    BIGINT NOT NULL,
                    name       VARCHAR(100) NOT NULL,
                    content    TEXT NOT NULL,
                    is_media   BOOLEAN DEFAULT FALSE,
                    file_id    TEXT,
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE (chat_id, name)
                )
            ");
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS notes (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id    INTEGER NOT NULL,
                    name       TEXT NOT NULL,
                    content    TEXT NOT NULL,
                    is_media   INTEGER DEFAULT 0,
                    file_id    TEXT,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (chat_id, name)
                )
            ");
        }

        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_notes_chat ON notes(chat_id)');
    }

    public function down(PDO $pdo): void { $pdo->exec('DROP TABLE IF EXISTS notes'); }
}
