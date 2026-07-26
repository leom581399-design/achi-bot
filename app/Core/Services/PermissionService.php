<?php
declare(strict_types=1);

namespace App\Core\Services;

use App\Core\Application;
use App\Core\Permission;
use App\Core\Telegram\TelegramClient;

/**
 * Single source of truth for permission resolution.
 *
 * Hierarchy (highest to lowest):
 *   Owner (env OWNER_IDS)
 *   Developer  ← stored in user_roles table (chat_id = 0 = global)
 *   Telegram creator / Administrator
 *   Moderator  ← stored in user_roles table per chat
 *   VIP        ← stored in user_roles table per chat
 *   User
 *
 * All modules use this service — no custom permission logic anywhere else.
 */
class PermissionService
{
    /** @var int[] */
    private array $ownerIds;
    private bool  $dbAvailable = false;

    public function __construct(
        private readonly Application $app
    ) {
        $config        = $app->make(ConfigService::class);
        $this->ownerIds = $config->get('app.owner_ids', []);
        $this->dbAvailable = $app->has(DatabaseService::class);
    }

    /**
     * Resolve the effective Permission level of a user in a chat.
     */
    public function getPermission(int|string $chatId, int $userId): Permission
    {
        // 1. Owner (env-configured)
        if (in_array($userId, $this->ownerIds, true)) {
            return Permission::Owner;
        }

        // 2. Developer (global role in DB)
        if ($this->dbAvailable && $this->hasRole($userId, 0, 'developer')) {
            return Permission::Developer;
        }

        // 3. Telegram-level (creator / admin)
        $telegramLevel = $this->resolveTelegramLevel($chatId, $userId);

        // 4. Moderator (per-chat role in DB) — only if Telegram says User
        if ($telegramLevel === Permission::User && $this->dbAvailable) {
            if ($this->hasRole($userId, (int)$chatId, 'moderator')) {
                return Permission::Moderator;
            }

            // 5. VIP
            if ($this->hasRole($userId, (int)$chatId, 'vip')) {
                return Permission::VIP;
            }
        }

        return $telegramLevel;
    }

    /**
     * Check whether a user has at least the required permission level.
     */
    public function can(int|string $chatId, int $userId, Permission $required): bool
    {
        return $this->getPermission($chatId, $userId)->isAtLeast($required);
    }

    public function isOwner(int $userId): bool
    {
        return in_array($userId, $this->ownerIds, true);
    }

    // -------------------------------------------------------------------------
    // Role management (Developer / Moderator / VIP)
    // -------------------------------------------------------------------------

    /**
     * Grant a role to a user. Pass chat_id = 0 for global (Developer).
     */
    public function grantRole(int $userId, int $chatId, string $role, ?int $grantedBy = null): void
    {
        if (!$this->dbAvailable) {
            throw new \RuntimeException('DatabaseService is not available — cannot grant roles.');
        }

        $db = $this->app->make(DatabaseService::class);
        $driver = $db->driver();

        if ($driver === 'pgsql') {
            $db->statement(
                "INSERT INTO user_roles (user_id, chat_id, role, granted_by)
                 VALUES (:u, :c, :r, :g)
                 ON CONFLICT (user_id, chat_id, role) DO NOTHING",
                [':u' => $userId, ':c' => $chatId, ':r' => $role, ':g' => $grantedBy]
            );
        } else {
            $db->statement(
                "INSERT OR IGNORE INTO user_roles (user_id, chat_id, role, granted_by)
                 VALUES (:u, :c, :r, :g)",
                [':u' => $userId, ':c' => $chatId, ':r' => $role, ':g' => $grantedBy]
            );
        }
    }

    /**
     * Revoke a role from a user.
     */
    public function revokeRole(int $userId, int $chatId, string $role): void
    {
        if (!$this->dbAvailable) {
            throw new \RuntimeException('DatabaseService is not available — cannot revoke roles.');
        }

        $this->app->make(DatabaseService::class)
            ->table('user_roles')
            ->where('user_id', $userId)
            ->where('chat_id', $chatId)
            ->where('role', $role)
            ->delete();
    }

    /**
     * List all role records for a user across all chats.
     */
    public function getRoles(int $userId): array
    {
        if (!$this->dbAvailable) return [];

        return $this->app->make(DatabaseService::class)
            ->table('user_roles')
            ->where('user_id', $userId)
            ->get();
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    private function resolveTelegramLevel(int|string $chatId, int $userId): Permission
    {
        try {
            $member = $this->app->make(TelegramClient::class)->getChatMember($chatId, $userId);

            return match($member['status']) {
                'creator'       => Permission::Administrator,
                'administrator' => Permission::Administrator,
                'member'        => Permission::User,
                'restricted'    => Permission::User,
                default         => Permission::User,
            };
        } catch (\Throwable) {
            return Permission::User;
        }
    }

    private function hasRole(int $userId, int $chatId, string $role): bool
    {
        try {
            $db = $this->app->make(DatabaseService::class);
            return $db->table('user_roles')
                ->where('user_id', $userId)
                ->where('chat_id', $chatId)
                ->where('role', $role)
                ->exists();
        } catch (\Throwable) {
            return false;
        }
    }
}
