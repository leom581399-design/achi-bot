<?php
declare(strict_types=1);

namespace App\Core\Helper;

use App\Core\Update;

/**
 * Resolves the target user for admin commands (ban, kick, mute, warn, etc.).
 *
 * Resolution order:
 *  1. Reply to a message → use the replied-to user
 *  2. text_mention entity in the command message → use that user (no username needed)
 *  3. First argument is a numeric string → treat as user_id
 *
 * Note: @username resolution requires an API call and is NOT done here because
 * this is a pure helper with no dependencies. The calling command must resolve
 * @usernames via TelegramClient::getChatMember if needed.
 *
 * Returns:
 *  [
 *    'id'             => int,    // Telegram user_id
 *    'name'           => string, // formatted first name (HTML-escaped)
 *    'remaining_args' => string, // args string after the target token was consumed
 *  ]
 * or null if no target could be resolved.
 */
class TargetResolver
{
    public static function resolve(Update $update, string $args): ?array
    {
        // 1. Reply to a message
        $replyUser = $update->getReplyToUser();
        if ($replyUser !== null) {
            return [
                'id'             => (int)$replyUser['id'],
                'name'           => self::formatName($replyUser),
                'remaining_args' => trim($args),
            ];
        }

        // 2. text_mention entity (users without @username)
        $mentionedUsers = $update->getMentionedUsers();
        if (!empty($mentionedUsers)) {
            $user = $mentionedUsers[0];
            // Remove the mention token from args for remaining_args
            $remaining = self::stripFirstToken($args);
            return [
                'id'             => (int)$user['id'],
                'name'           => self::formatName($user),
                'remaining_args' => $remaining,
            ];
        }

        // 3. First arg is numeric user_id
        $parts = explode(' ', trim($args), 2);
        $first = $parts[0] ?? '';

        if ($first !== '' && ctype_digit($first)) {
            return [
                'id'             => (int)$first,
                'name'           => "<code>{$first}</code>",
                'remaining_args' => trim($parts[1] ?? ''),
            ];
        }

        return null;
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    public static function formatName(array $user): string
    {
        $name = htmlspecialchars($user['first_name'] ?? 'Unknown');
        if (!empty($user['last_name'])) {
            $name .= ' ' . htmlspecialchars($user['last_name']);
        }
        return $name;
    }

    public static function formatMention(array $user): string
    {
        $name = self::formatName($user);
        $id   = (int)$user['id'];
        return "<a href=\"tg://user?id={$id}\">{$name}</a>";
    }

    private static function stripFirstToken(string $args): string
    {
        $parts = explode(' ', trim($args), 2);
        return trim($parts[1] ?? '');
    }
}
