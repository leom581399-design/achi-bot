<?php
declare(strict_types=1);

namespace Modules\FedBan\Services;

use App\Core\Application;
use App\Core\Services\LoggerService;
use App\Core\Telegram\TelegramClient;
use Modules\FedBan\Repository\FedRepository;

class FedService
{
    public function __construct(private readonly Application $app) {}

    // -------------------------------------------------------------------------
    // Federation management
    // -------------------------------------------------------------------------

    public function create(string $name, int $ownerId): array
    {
        $repo  = $this->repo();
        $fedId = $this->generateFedId();

        $repo->createFed([
            'fed_id'   => $fedId,
            'name'     => $name,
            'owner_id' => $ownerId,
        ]);

        return $repo->findFedById($fedId);
    }

    public function findById(string $fedId): ?array
    {
        return $this->repo()->findFedById($fedId);
    }

    public function findByOwner(int $ownerId): ?array
    {
        return $this->repo()->findFedByOwner($ownerId);
    }

    public function delete(string $fedId): bool
    {
        return $this->repo()->deleteFed($fedId);
    }

    // -------------------------------------------------------------------------
    // Chat membership
    // -------------------------------------------------------------------------

    public function joinFed(string $fedId, int $chatId, int $joinedBy): bool
    {
        return $this->repo()->joinFed($fedId, $chatId, $joinedBy);
    }

    public function leaveFed(int $chatId): bool
    {
        return $this->repo()->leaveFed($chatId);
    }

    public function getFedForChat(int $chatId): ?array
    {
        return $this->repo()->findFedForChat($chatId);
    }

    public function listChats(string $fedId): array
    {
        return $this->repo()->listFedChats($fedId);
    }

    // -------------------------------------------------------------------------
    // Fedban operations
    // -------------------------------------------------------------------------

    /**
     * Bane um usuário na federação e aplica o ban em todos os chats membros.
     */
    public function fban(string $fedId, int $userId, int $bannedBy, ?string $reason): bool
    {
        $repo = $this->repo();

        $ok = $repo->fban([
            'fed_id'    => $fedId,
            'user_id'   => $userId,
            'reason'    => $reason,
            'banned_by' => $bannedBy,
        ]);

        // Propagar o ban a todos os chats da federação
        $chats  = $repo->listFedChats($fedId);
        $client = $this->app->make(TelegramClient::class);

        foreach ($chats as $chat) {
            try {
                $client->banChatMember((int)$chat['chat_id'], $userId);
            } catch (\Throwable $e) {
                $this->app->make(LoggerService::class)->warning(
                    "FedBan: ban failed in chat {$chat['chat_id']} for user {$userId}: " . $e->getMessage()
                );
            }
        }

        $this->app->make(LoggerService::class)->security(
            "FBAN fed={$fedId} user={$userId} by={$bannedBy} chats=" . count($chats)
        );

        return $ok;
    }

    /**
     * Remove o fedban e desbaneia em todos os chats da federação.
     */
    public function unfban(string $fedId, int $userId): bool
    {
        $repo = $this->repo();
        $ok   = $repo->unfban($fedId, $userId);

        $chats  = $repo->listFedChats($fedId);
        $client = $this->app->make(TelegramClient::class);

        foreach ($chats as $chat) {
            try {
                $client->unbanChatMember((int)$chat['chat_id'], $userId);
            } catch (\Throwable) {}
        }

        return $ok;
    }

    public function isFbanned(string $fedId, int $userId): ?array
    {
        return $this->repo()->isFbanned($fedId, $userId);
    }

    public function listFbans(string $fedId, int $limit = 50): array
    {
        return $this->repo()->listFbans($fedId, $limit);
    }

    public function countFbans(string $fedId): int
    {
        return $this->repo()->countFbans($fedId);
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private function repo(): FedRepository
    {
        return $this->app->make(FedRepository::class);
    }

    private function generateFedId(): string
    {
        return sprintf(
            '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            mt_rand(0, 0xffff), mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0x0fff) | 0x4000,
            mt_rand(0, 0x3fff) | 0x8000,
            mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
        );
    }
}
