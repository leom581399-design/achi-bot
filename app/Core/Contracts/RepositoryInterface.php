<?php
declare(strict_types=1);

namespace App\Core\Contracts;

/**
 * Base interface every repository must implement.
 * Repositories are the single point of data access — no SQL anywhere else.
 */
interface RepositoryInterface
{
    /** Find a record by its primary key. Returns null if not found. */
    public function find(int|string $id): ?array;

    /**
     * Find the first record matching the given conditions.
     *
     * @param array<string, mixed> $conditions  column => value pairs (AND)
     */
    public function findBy(array $conditions): ?array;

    /**
     * Find all records matching the given conditions.
     *
     * @param array<string, mixed> $conditions  column => value pairs (AND)
     * @return array<int, array>
     */
    public function findAllBy(array $conditions): array;

    /**
     * Insert or update a record.
     * If $data contains the primary key and the record exists, update; otherwise insert.
     */
    public function save(array $data): bool;

    /** Delete a record by its primary key. Returns true if a row was deleted. */
    public function delete(int|string $id): bool;

    /** Count records matching the given conditions. */
    public function count(array $conditions = []): int;
}
