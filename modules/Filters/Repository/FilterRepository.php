<?php
declare(strict_types=1);

namespace Modules\Filters\Repository;

use App\Core\Repository\BaseRepository;

class FilterRepository extends BaseRepository
{
    protected string $table = 'filters';

    public function findByKeyword(int $chatId, string $keyword): ?array
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('keyword', strtolower($keyword))
            ->first();
    }

    public function findAllForChat(int $chatId): array
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->orderBy('keyword', 'ASC')
            ->get();
    }

    public function create(array $data): bool
    {
        return $this->db->table($this->table)->insert($data);
    }

    public function deleteByKeyword(int $chatId, string $keyword): int
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('keyword', strtolower($keyword))
            ->delete();
    }

    public function deleteAll(int $chatId): int
    {
        return $this->query()->where('chat_id', $chatId)->delete();
    }
}
