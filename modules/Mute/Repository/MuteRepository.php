<?php
declare(strict_types=1);

namespace Modules\Mute\Repository;

use App\Core\Repository\BaseRepository;

class MuteRepository extends BaseRepository
{
    protected string $table = 'mutes';

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

    public function findForUser(int $chatId, int $userId): ?array
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('user_id', $userId)
            ->orderBy('created_at', 'DESC')
            ->first();
    }
}
