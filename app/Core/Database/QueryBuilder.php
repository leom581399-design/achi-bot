<?php
declare(strict_types=1);

namespace App\Core\Database;

use PDO;
use PDOStatement;

/**
 * Simple fluent query builder.
 *
 * Usage:
 *   $rows = (new QueryBuilder($pdo))->table('bans')
 *       ->where('chat_id', $chatId)
 *       ->where('user_id', $userId)
 *       ->get();
 */
class QueryBuilder
{
    private string  $table     = '';
    private array   $wheres    = [];
    private array   $bindings  = [];
    private ?int    $limitVal  = null;
    private ?int    $offsetVal = null;
    private array   $orders    = [];
    private array   $columns   = ['*'];

    public function __construct(private readonly PDO $pdo) {}

    // -------------------------------------------------------------------------
    // Table
    // -------------------------------------------------------------------------

    public function table(string $table): static
    {
        $clone        = clone $this;
        $clone->table = $table;
        return $clone;
    }

    // -------------------------------------------------------------------------
    // SELECT columns
    // -------------------------------------------------------------------------

    public function select(string ...$columns): static
    {
        $clone          = clone $this;
        $clone->columns = $columns;
        return $clone;
    }

    // -------------------------------------------------------------------------
    // WHERE
    // -------------------------------------------------------------------------

    public function where(string $column, mixed $value, string $operator = '='): static
    {
        $clone = clone $this;
        $placeholder = ':w_' . count($clone->wheres) . '_' . preg_replace('/\W/', '_', $column);
        $clone->wheres[]              = "{$column} {$operator} {$placeholder}";
        $clone->bindings[$placeholder] = $value;
        return $clone;
    }

    public function whereNull(string $column): static
    {
        $clone           = clone $this;
        $clone->wheres[] = "{$column} IS NULL";
        return $clone;
    }

    public function whereNotNull(string $column): static
    {
        $clone           = clone $this;
        $clone->wheres[] = "{$column} IS NOT NULL";
        return $clone;
    }

    // -------------------------------------------------------------------------
    // ORDER / LIMIT / OFFSET
    // -------------------------------------------------------------------------

    public function orderBy(string $column, string $direction = 'ASC'): static
    {
        $clone           = clone $this;
        $direction       = strtoupper($direction) === 'DESC' ? 'DESC' : 'ASC';
        $clone->orders[] = "{$column} {$direction}";
        return $clone;
    }

    public function limit(int $limit): static
    {
        $clone             = clone $this;
        $clone->limitVal   = $limit;
        return $clone;
    }

    public function offset(int $offset): static
    {
        $clone             = clone $this;
        $clone->offsetVal  = $offset;
        return $clone;
    }

    // -------------------------------------------------------------------------
    // Read
    // -------------------------------------------------------------------------

    public function get(): array
    {
        $sql  = $this->buildSelect();
        $stmt = $this->execute($sql, $this->bindings);
        return $stmt->fetchAll();
    }

    public function first(): ?array
    {
        $result = $this->limit(1)->get();
        return $result[0] ?? null;
    }

    public function count(): int
    {
        $clone          = clone $this;
        $clone->columns = ['COUNT(*) AS cnt'];
        $sql            = $clone->buildSelect();
        $stmt           = $this->execute($sql, $clone->bindings);
        $row            = $stmt->fetch();
        return (int)($row['cnt'] ?? 0);
    }

    public function exists(): bool
    {
        return $this->count() > 0;
    }

    // -------------------------------------------------------------------------
    // Write
    // -------------------------------------------------------------------------

    public function insert(array $data): bool
    {
        if (empty($data)) return false;

        $columns      = array_keys($data);
        $placeholders = array_map(fn($c) => ':' . $c, $columns);

        $sql  = sprintf(
            'INSERT INTO %s (%s) VALUES (%s)',
            $this->table,
            implode(', ', $columns),
            implode(', ', $placeholders)
        );

        $bindings = [];
        foreach ($data as $col => $val) {
            $bindings[':' . $col] = $val;
        }

        $this->execute($sql, $bindings);
        return true;
    }

    /**
     * Insert or ignore (duplicate key). Useful for upsert-like patterns.
     */
    public function insertOrIgnore(array $data): bool
    {
        if (empty($data)) return false;

        $driver  = $this->pdo->getAttribute(PDO::ATTR_DRIVER_NAME);
        $columns = array_keys($data);
        $placeholders = array_map(fn($c) => ':' . $c, $columns);

        $sql = match($driver) {
            'pgsql'  => sprintf(
                'INSERT INTO %s (%s) VALUES (%s) ON CONFLICT DO NOTHING',
                $this->table,
                implode(', ', $columns),
                implode(', ', $placeholders)
            ),
            default  => sprintf(
                'INSERT OR IGNORE INTO %s (%s) VALUES (%s)',
                $this->table,
                implode(', ', $columns),
                implode(', ', $placeholders)
            ),
        };

        $bindings = [];
        foreach ($data as $col => $val) {
            $bindings[':' . $col] = $val;
        }

        $this->execute($sql, $bindings);
        return true;
    }

    public function update(array $data): int
    {
        if (empty($data)) return 0;

        $setClauses = [];
        $bindings   = [];

        foreach ($data as $col => $val) {
            $ph              = ':set_' . $col;
            $setClauses[]    = "{$col} = {$ph}";
            $bindings[$ph]   = $val;
        }

        $sql = sprintf('UPDATE %s SET %s', $this->table, implode(', ', $setClauses));

        if (!empty($this->wheres)) {
            $sql .= ' WHERE ' . implode(' AND ', $this->wheres);
            $bindings = array_merge($bindings, $this->bindings);
        }

        $stmt = $this->execute($sql, $bindings);
        return $stmt->rowCount();
    }

    public function delete(): int
    {
        $sql = "DELETE FROM {$this->table}";

        if (!empty($this->wheres)) {
            $sql .= ' WHERE ' . implode(' AND ', $this->wheres);
        }

        $stmt = $this->execute($sql, $this->bindings);
        return $stmt->rowCount();
    }

    public function lastInsertId(): string|false
    {
        return $this->pdo->lastInsertId();
    }

    // -------------------------------------------------------------------------
    // Raw
    // -------------------------------------------------------------------------

    public function raw(string $sql, array $bindings = []): PDOStatement
    {
        return $this->execute($sql, $bindings);
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    private function buildSelect(): string
    {
        $sql = sprintf(
            'SELECT %s FROM %s',
            implode(', ', $this->columns),
            $this->table
        );

        if (!empty($this->wheres)) {
            $sql .= ' WHERE ' . implode(' AND ', $this->wheres);
        }

        if (!empty($this->orders)) {
            $sql .= ' ORDER BY ' . implode(', ', $this->orders);
        }

        if ($this->limitVal !== null) {
            $sql .= " LIMIT {$this->limitVal}";
        }

        if ($this->offsetVal !== null) {
            $sql .= " OFFSET {$this->offsetVal}";
        }

        return $sql;
    }

    private function execute(string $sql, array $bindings = []): PDOStatement
    {
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($bindings);
        return $stmt;
    }
}
