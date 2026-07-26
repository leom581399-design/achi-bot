<?php
declare(strict_types=1);

namespace App\Core\Database\Migrations;

use App\Core\Database\Migration;
use PDO;

class CreateUserRolesTable implements Migration
{
    public function version(): int { return 3; }

    public function description(): string { return 'Create user_roles table'; }

    public function up(PDO $pdo): void
    {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        if ($driver === 'pgsql') {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS user_roles (
                    id         SERIAL PRIMARY KEY,
                    user_id    BIGINT NOT NULL,
                    chat_id    BIGINT NOT NULL DEFAULT 0,
                    role       VARCHAR(20) NOT NULL,
                    granted_by BIGINT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE (user_id, chat_id, role)
                )
            ");
            $pdo->exec('CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id)');
            $pdo->exec('CREATE INDEX IF NOT EXISTS idx_user_roles_chat ON user_roles(chat_id)');
        } else {
            $pdo->exec("
                CREATE TABLE IF NOT EXISTS user_roles (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER NOT NULL,
                    chat_id    INTEGER NOT NULL DEFAULT 0,
                    role       TEXT NOT NULL,
                    granted_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, chat_id, role)
                )
            ");
            $pdo->exec('CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id)');
            $pdo->exec('CREATE INDEX IF NOT EXISTS idx_user_roles_chat ON user_roles(chat_id)');
        }
    }

    public function down(PDO $pdo): void
    {
        $pdo->exec('DROP TABLE IF EXISTS user_roles');
    }
}
