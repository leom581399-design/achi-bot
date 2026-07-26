<?php
declare(strict_types=1);

namespace App\Core\Database;

use PDO;

/**
 * Interface every migration must implement.
 */
interface Migration
{
    /** Unique sequential version, e.g. 1, 2, 3 … */
    public function version(): int;

    /** Human-readable description logged when the migration runs. */
    public function description(): string;

    /** Apply the migration (CREATE TABLE, ALTER TABLE, etc.). */
    public function up(PDO $pdo): void;

    /** Rollback the migration (DROP TABLE, etc.). */
    public function down(PDO $pdo): void;
}
