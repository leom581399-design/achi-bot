<?php
declare(strict_types=1);

namespace Modules\Ban\Repository;

use App\Core\Repository\BaseRepository;

class BanRepository extends BaseRepository
{
    protected string $table = 'bans';

    public function findActiveBan(int $chatId, int $userId): ?array
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('user_id', $userId)
            ->orderBy('created_at', 'DESC')
            ->first();
    }

    public function findAllForChat(int $chatId): array
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->orderBy('created_at', 'DESC')
            ->get();
    }

    public function countForUser(int $chatId, int $userId): int
    {
        return $this->count(['chat_id' => $chatId, 'user_id' => $userId]);
    }

    public function create(array $data): bool
    {
        return $this->db->table($this->table)->insert($data);
    }

    public function deleteForUser(int $chatId, int $userId): int
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('user_id', $userId)
            ->delete();
    }
}
