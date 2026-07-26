<?php
declare(strict_types=1);

namespace Modules\Warn\Repository;

use App\Core\Repository\BaseRepository;

class WarnRepository extends BaseRepository
{
    protected string $table = 'warns';

    public function create(array $data): bool
    {
        return $this->db->table($this->table)->insert($data);
    }

    public function countForUser(int $chatId, int $userId): int
    {
        return $this->count(['chat_id' => $chatId, 'user_id' => $userId]);
    }

    public function findAllForUser(int $chatId, int $userId): array
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('user_id', $userId)
            ->orderBy('created_at', 'ASC')
            ->get();
    }

    /** Delete the most recent warn for a user. Returns true if deleted. */
    public function deleteLatest(int $chatId, int $userId): bool
    {
        $row = $this->query()
            ->where('chat_id', $chatId)
            ->where('user_id', $userId)
            ->orderBy('created_at', 'DESC')
            ->first();

        if ($row === null) return false;

        return $this->delete($row['id']);
    }

    /** Delete all warns for a user in a chat. */
    public function resetForUser(int $chatId, int $userId): int
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('user_id', $userId)
            ->delete();
    }
}
