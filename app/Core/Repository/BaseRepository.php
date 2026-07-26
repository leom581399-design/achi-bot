<?php
declare(strict_types=1);

namespace App\Core\Repository;

use App\Core\Contracts\RepositoryInterface;
use App\Core\Database\QueryBuilder;
use App\Core\Services\DatabaseService;

/**
 * Abstract base for all repositories.
 *
 * Concrete repositories only need to declare:
 *   - $table  — the database table name
 *   - $pk     — the primary key column (default: 'id')
 *
 * Example:
 *   class BanRepository extends BaseRepository
 *   {
 *       protected string $table = 'bans';
 *   }
 */
abstract class BaseRepository implements RepositoryInterface
{
    protected string $table = '';
    protected string $pk    = 'id';

    public function __construct(
        protected readonly DatabaseService $db
    ) {}

    // -------------------------------------------------------------------------
    // RepositoryInterface implementation
    // -------------------------------------------------------------------------

    public function find(int|string $id): ?array
    {
        return $this->db->table($this->table)
            ->where($this->pk, $id)
            ->first();
    }

    public function findBy(array $conditions): ?array
    {
        $qb = $this->db->table($this->table);
        foreach ($conditions as $column => $value) {
            $qb = $qb->where($column, $value);
        }
        return $qb->first();
    }

    public function findAllBy(array $conditions): array
    {
        $qb = $this->db->table($this->table);
        foreach ($conditions as $column => $value) {
            $qb = $qb->where($column, $value);
        }
        return $qb->get();
    }

    public function save(array $data): bool
    {
        if (isset($data[$this->pk]) && $this->find($data[$this->pk]) !== null) {
            $pk = $data[$this->pk];
            unset($data[$this->pk]);
            return $this->db->table($this->table)
                ->where($this->pk, $pk)
                ->update($data) >= 0;
        }

        return $this->db->table($this->table)->insert($data);
    }

    public function delete(int|string $id): bool
    {
        return $this->db->table($this->table)
            ->where($this->pk, $id)
            ->delete() > 0;
    }

    public function count(array $conditions = []): int
    {
        $qb = $this->db->table($this->table);
        foreach ($conditions as $column => $value) {
            $qb = $qb->where($column, $value);
        }
        return $qb->count();
    }

    // -------------------------------------------------------------------------
    // Helpers for subclasses
    // -------------------------------------------------------------------------

    /** Return a fresh QueryBuilder pointed at this repository's table. */
    protected function query(): QueryBuilder
    {
        return $this->db->table($this->table);
    }

    /** Return all rows in the table (use sparingly). */
    public function all(): array
    {
        return $this->db->table($this->table)->get();
    }
}
