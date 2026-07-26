<?php
declare(strict_types=1);

namespace Modules\FedBan\Repository;

use App\Core\Repository\BaseRepository;

class FedRepository extends BaseRepository
{
    protected string $table = 'federations';

    // -------------------------------------------------------------------------
    // Federations
    // -------------------------------------------------------------------------

    public function createFed(array $data): bool
    {
        return $this->db->table('federations')->insert($data);
    }

    public function findFedById(string $fedId): ?array
    {
        return $this->db->table('federations')->where('fed_id', $fedId)->first();
    }

    public function findFedByOwner(int $ownerId): ?array
    {
        return $this->db->table('federations')->where('owner_id', $ownerId)->first();
    }

    public function deleteFed(string $fedId): bool
    {
        $ok = $this->db->table('federations')->where('fed_id', $fedId)->delete() > 0;
        $this->db->table('fed_chats')->where('fed_id', $fedId)->delete();
        $this->db->table('fed_bans')->where('fed_id', $fedId)->delete();
        return $ok;
    }

    // -------------------------------------------------------------------------
    // Fed chats
    // -------------------------------------------------------------------------

    public function joinFed(string $fedId, int $chatId, int $joinedBy): bool
    {
        try {
            return $this->db->table('fed_chats')->insert([
                'fed_id'    => $fedId,
                'chat_id'   => $chatId,
                'joined_by' => $joinedBy,
            ]);
        } catch (\Throwable) {
            return false; // UNIQUE conflict — já membro
        }
    }

    public function leaveFed(int $chatId): bool
    {
        return $this->db->table('fed_chats')->where('chat_id', $chatId)->delete() > 0;
    }

    /** Retorna a federação à qual este chat pertence, ou null. */
    public function findFedForChat(int $chatId): ?array
    {
        $row = $this->db->table('fed_chats')->where('chat_id', $chatId)->first();
        if (!$row) return null;
        return $this->findFedById($row['fed_id']);
    }

    /** Lista todos os chats de uma federação. */
    public function listFedChats(string $fedId): array
    {
        return $this->db->table('fed_chats')->where('fed_id', $fedId)->get();
    }

    // -------------------------------------------------------------------------
    // Fed bans
    // -------------------------------------------------------------------------

    public function fban(array $data): bool
    {
        try {
            return $this->db->table('fed_bans')->insert($data);
        } catch (\Throwable) {
            // Já banido — atualiza motivo
            $this->db->table('fed_bans')
                ->where('fed_id', $data['fed_id'])
                ->where('user_id', $data['user_id'])
                ->update(['reason' => $data['reason'], 'banned_by' => $data['banned_by']]);
            return true;
        }
    }

    public function unfban(string $fedId, int $userId): bool
    {
        return $this->db->table('fed_bans')
            ->where('fed_id', $fedId)
            ->where('user_id', $userId)
            ->delete() > 0;
    }

    public function isFbanned(string $fedId, int $userId): ?array
    {
        return $this->db->table('fed_bans')
            ->where('fed_id', $fedId)
            ->where('user_id', $userId)
            ->first();
    }

    public function listFbans(string $fedId, int $limit = 50): array
    {
        return $this->db->table('fed_bans')
            ->where('fed_id', $fedId)
            ->orderBy('created_at', 'DESC')
            ->limit($limit)
            ->get();
    }

    public function countFbans(string $fedId): int
    {
        return (int)($this->db->table('fed_bans')
            ->where('fed_id', $fedId)
            ->count() ?: 0);
    }
}
