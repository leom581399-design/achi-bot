<?php
declare(strict_types=1);

namespace App\Core;

/**
 * Permission levels used across the entire framework.
 * All modules reuse this single enum — no custom permission integers anywhere.
 */
enum Permission: int
{
    case Owner         = 100;
    case Developer     = 90;
    case Administrator = 80;
    case Moderator     = 70;
    case VIP           = 60;
    case User          = 0;

    public function label(): string
    {
        return match($this) {
            self::Owner         => '👑 Owner',
            self::Developer     => '🛠️ Developer',
            self::Administrator => '⚙️ Administrator',
            self::Moderator     => '🛡️ Moderator',
            self::VIP           => '⭐ VIP',
            self::User          => '👤 User',
        };
    }

    /** Returns true if this level is equal to or higher than $required. */
    public function isAtLeast(self $required): bool
    {
        return $this->value >= $required->value;
    }
}
