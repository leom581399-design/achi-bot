<?php
declare(strict_types=1);

namespace App\Core\Services;

use App\Core\Database\Connection;
use App\Core\Database\QueryBuilder;
use PDO;

/**
 * Primary database access service.
 *
 * All modules receive this via dependency injection — never instantiate PDO directly.
 *
 * Usage:
 *   $db  = $app->make(DatabaseService::class);
 *   $qb  = $db->table('bans');           // returns a QueryBuilder
 *   $pdo = $db->pdo();                   // raw PDO for edge cases
 */
class DatabaseService
{
    private PDO $pdo;

    public function __construct(string $storageDir = '')
    {
        $this->pdo = Connection::get($storageDir);
    }

    // -------------------------------------------------------------------------
    // Query builder factory
    // -------------------------------------------------------------------------

    public function table(string $table): QueryBuilder
    {
        return (new QueryBuilder($this->pdo))->table($table);
    }

    // -------------------------------------------------------------------------
    // Raw PDO (for migrations, transactions, etc.)
    // -------------------------------------------------------------------------

    public function pdo(): PDO
    {
        return $this->pdo;
    }

    // -------------------------------------------------------------------------
    // Transaction helpers
    // -------------------------------------------------------------------------

    public function transaction(callable $callback): mixed
    {
        $this->pdo->beginTransaction();
        try {
            $result = $callback($this);
            $this->pdo->commit();
            return $result;
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }
    }

    public function beginTransaction(): void
    {
        $this->pdo->beginTransaction();
    }

    public function commit(): void
    {
        $this->pdo->commit();
    }

    public function rollBack(): void
    {
        $this->pdo->rollBack();
    }

    // -------------------------------------------------------------------------
    // Utility
    // -------------------------------------------------------------------------

    public function lastInsertId(): string|false
    {
        return $this->pdo->lastInsertId();
    }

    public function driver(): string
    {
        return $this->pdo->getAttribute(PDO::ATTR_DRIVER_NAME);
    }

    /**
     * Execute raw SQL. Use sparingly — prefer table()->... for queries.
     */
    public function exec(string $sql): int|false
    {
        return $this->pdo->exec($sql);
    }

    /**
     * Prepare and execute a raw statement. Returns all rows.
     */
    public function select(string $sql, array $bindings = []): array
    {
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($bindings);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    /**
     * Prepare and execute a raw statement. Returns the first row or null.
     */
    public function selectOne(string $sql, array $bindings = []): ?array
    {
        $results = $this->select($sql, $bindings);
        return $results[0] ?? null;
    }

    /**
     * Prepare and execute an INSERT/UPDATE/DELETE. Returns affected rows.
     */
    public function statement(string $sql, array $bindings = []): int
    {
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($bindings);
        return $stmt->rowCount();
    }
}
