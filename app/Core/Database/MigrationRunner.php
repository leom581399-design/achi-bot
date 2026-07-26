<?php
declare(strict_types=1);

namespace App\Core\Database;

use PDO;

/**
 * Discovers and runs pending migrations in order.
 *
 * - Keeps a `schema_migrations` table with the applied version numbers.
 * - Scans `app/Core/Database/Migrations/` for classes implementing Migration.
 * - Runs each pending migration in version order.
 */
class MigrationRunner
{
    private PDO $pdo;

    public function __construct(PDO $pdo)
    {
        $this->pdo = $pdo;
        $this->ensureMigrationsTable();
    }

    /**
     * Run all pending migrations.
     * Returns the list of versions that were actually applied.
     */
    public function run(bool $verbose = false): array
    {
        $applied  = $this->getAppliedVersions();
        $pending  = $this->getPendingMigrations($applied);
        $executed = [];

        foreach ($pending as $migration) {
            if ($verbose) {
                echo sprintf(
                    "[migrate] Applying %03d: %s\n",
                    $migration->version(),
                    $migration->description()
                );
            }

            $this->pdo->beginTransaction();
            try {
                $migration->up($this->pdo);
                $this->markApplied($migration->version(), $migration->description());
                $this->pdo->commit();
                $executed[] = $migration->version();
            } catch (\Throwable $e) {
                $this->pdo->rollBack();
                throw new \RuntimeException(
                    sprintf(
                        'Migration %03d (%s) failed: %s',
                        $migration->version(),
                        $migration->description(),
                        $e->getMessage()
                    ),
                    0,
                    $e
                );
            }
        }

        if ($verbose && empty($executed)) {
            echo "[migrate] Nothing to run — all migrations are up to date.\n";
        }

        return $executed;
    }

    /** Return the list of applied version numbers. */
    public function getAppliedVersions(): array
    {
        $stmt = $this->pdo->query('SELECT version FROM schema_migrations ORDER BY version');
        return $stmt->fetchAll(PDO::FETCH_COLUMN) ?: [];
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    private function ensureMigrationsTable(): void
    {
        $driver = $this->pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

        $sql = match($driver) {
            'pgsql' => "
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version     INTEGER PRIMARY KEY,
                    description TEXT,
                    applied_at  TIMESTAMP DEFAULT NOW()
                )
            ",
            default => "
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version     INTEGER PRIMARY KEY,
                    description TEXT,
                    applied_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ",
        };

        $this->pdo->exec($sql);
    }

    private function markApplied(int $version, string $description): void
    {
        $stmt = $this->pdo->prepare(
            'INSERT INTO schema_migrations (version, description) VALUES (:v, :d)'
        );
        $stmt->execute([':v' => $version, ':d' => $description]);
    }

    /**
     * Load migration class files from the Migrations/ subdirectory
     * and return instances of pending ones, sorted by version.
     */
    private function getPendingMigrations(array $applied): array
    {
        $dir   = __DIR__ . '/Migrations';
        $files = glob($dir . '/*.php') ?: [];
        sort($files);

        $migrations = [];

        foreach ($files as $file) {
            require_once $file;
        }

        // Find all classes implementing Migration in the current process
        foreach (get_declared_classes() as $class) {
            if (!is_a($class, Migration::class, true)) {
                continue;
            }

            $obj = new $class();

            if (!in_array($obj->version(), $applied, strict: true)) {
                $migrations[] = $obj;
            }
        }

        usort($migrations, fn($a, $b) => $a->version() <=> $b->version());

        return $migrations;
    }
}
