<?php
declare(strict_types=1);

namespace Modules\Mute\Services;

use App\Core\Application;
use App\Core\EventDispatcher;
use App\Core\Services\LoggerService;
use App\Core\Telegram\TelegramClient;
use Modules\Mute\Repository\MuteRepository;

class MuteService
{
    /** Permissions that define a fully muted user */
    private const MUTED_PERMISSIONS = [
        'can_send_messages'       => false,
        'can_send_audios'         => false,
        'can_send_documents'      => false,
        'can_send_photos'         => false,
        'can_send_videos'         => false,
        'can_send_video_notes'    => false,
        'can_send_voice_notes'    => false,
        'can_send_polls'          => false,
        'can_send_other_messages' => false,
        'can_add_web_page_previews' => false,
    ];

    /** Permissions restored on unmute */
    private const RESTORED_PERMISSIONS = [
        'can_send_messages'       => true,
        'can_send_audios'         => true,
        'can_send_documents'      => true,
        'can_send_photos'         => true,
        'can_send_videos'         => true,
        'can_send_video_notes'    => true,
        'can_send_voice_notes'    => true,
        'can_send_polls'          => true,
        'can_send_other_messages' => true,
        'can_add_web_page_previews' => true,
    ];

    public function __construct(private readonly Application $app) {}

    public function mute(int $chatId, int $userId, int $mutedBy, ?string $reason, ?int $untilDate = null): void
    {
        $options = [];
        if ($untilDate !== null) {
            $options['until_date'] = $untilDate;
        }

        $this->app->make(TelegramClient::class)
            ->restrictChatMember($chatId, $userId, self::MUTED_PERMISSIONS, $options);

        $this->app->make(MuteRepository::class)->create([
            'chat_id'    => $chatId,
            'user_id'    => $userId,
            'reason'     => $reason,
            'muted_by'   => $mutedBy,
            'until_date' => $untilDate ? date('Y-m-d H:i:s', $untilDate) : null,
        ]);

        $this->app->make(LoggerService::class)->security(
            "MUTE chat={$chatId} user={$userId} by={$mutedBy} until={$untilDate}"
        );

        $this->app->make(EventDispatcher::class)->emit('member.muted', [
            'chat_id'    => $chatId,
            'user_id'    => $userId,
            'muted_by'   => $mutedBy,
            'reason'     => $reason,
            'until_date' => $untilDate,
        ]);
    }

    public function unmute(int $chatId, int $userId, int $unmutedBy): void
    {
        $this->app->make(TelegramClient::class)
            ->restrictChatMember($chatId, $userId, self::RESTORED_PERMISSIONS);

        $this->app->make(MuteRepository::class)->deleteForUser($chatId, $userId);

        $this->app->make(LoggerService::class)->security(
            "UNMUTE chat={$chatId} user={$userId} by={$unmutedBy}"
        );

        $this->app->make(EventDispatcher::class)->emit('member.unmuted', [
            'chat_id'      => $chatId,
            'user_id'      => $userId,
            'unmuted_by'   => $unmutedBy,
        ]);
    }
}
