<?php
declare(strict_types=1);

namespace Modules\Notes\Repository;

use App\Core\Repository\BaseRepository;

class NotesRepository extends BaseRepository
{
    protected string $table = 'notes';

    public function findByName(int $chatId, string $name): ?array
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('name', strtolower($name))
            ->first();
    }

    public function findAllForChat(int $chatId): array
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->orderBy('name', 'ASC')
            ->get();
    }

    public function upsert(array $data): bool
    {
        $data['name'] = strtolower($data['name']);
        $existing = $this->findByName((int)$data['chat_id'], $data['name']);

        if ($existing) {
            return $this->query()
                ->where('chat_id', $data['chat_id'])
                ->where('name', $data['name'])
                ->update(array_diff_key($data, ['chat_id' => 1, 'name' => 1])) >= 0;
        }

        return $this->db->table($this->table)->insert($data);
    }

    public function deleteByName(int $chatId, string $name): bool
    {
        return $this->query()
            ->where('chat_id', $chatId)
            ->where('name', strtolower($name))
            ->delete() > 0;
    }
}
