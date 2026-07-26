<?php
declare(strict_types=1);

namespace Modules\Stats\Repository;

use App\Core\Repository\BaseRepository;
use App\Core\Services\DatabaseService;

class StatsRepository extends BaseRepository
{
    protected string $table = 'message_stats';

    /**
     * Incrementa o contador de mensagens de um usuário em um chat.
     * Faz upsert — insere na primeira vez, incrementa nas demais.
     */
    public function increment(int $chatId, int $userId): void
    {
        $driver = $this->db->driver();

        if ($driver === 'pgsql') {
            $this->db->statement(
                "INSERT INTO message_stats (chat_id, user_id, msg_count, last_seen)
                 VALUES (:c, :u, 1, NOW())
                 ON CONFLICT (chat_id, user_id)
                 DO UPDATE SET msg_count = message_stats.msg_count + 1, last_seen = NOW()",
                [':c' => $chatId, ':u' => $userId]
            );
        } else {
            $this->db->statement(
                "INSERT INTO message_stats (chat_id, user_id, msg_count, last_seen)
                 VALUES (:c, :u, 1, CURRENT_TIMESTAMP)
                 ON CONFLICT (chat_id, user_id)
                 DO UPDATE SET msg_count = msg_count + 1, last_seen = CURRENT_TIMESTAMP",
                [':c' => $chatId, ':u' => $userId]
            );
        }
    }

    /**
     * Retorna os top N usuários de um chat por contagem de mensagens.
     */
    public function topUsers(int $chatId, int $limit = 10): array
    {
        return $this->db->table('message_stats')
            ->where('chat_id', $chatId)
            ->orderBy('msg_count', 'DESC')
            ->limit($limit)
            ->get();
    }

    /**
     * Total de mensagens registradas no chat.
     */
    public function totalMessages(int $chatId): int
    {
        $row = $this->db->select(
            'SELECT SUM(msg_count) as total FROM message_stats WHERE chat_id = :c',
            [':c' => $chatId]
        );
        return (int)($row[0]['total'] ?? 0);
    }

    /**
     * Total de usuários ativos (que enviaram ≥1 mensagem) no chat.
     */
    public function totalUsers(int $chatId): int
    {
        return $this->count(['chat_id' => $chatId]);
    }

    /**
     * Ranking de um usuário específico no chat.
     */
    public function userRank(int $chatId, int $userId): ?array
    {
        return $this->db->table('message_stats')
            ->where('chat_id', $chatId)
            ->where('user_id', $userId)
            ->first();
    }
}
