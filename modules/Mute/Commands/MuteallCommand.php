<?php
declare(strict_types=1);

namespace Modules\Mute\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * /muteall — Silencia todos os membros do grupo (altera permissões padrão).
 * Uso: /muteall           → silencia todos
 *      /muteall off       → restaura fala para todos
 */
class MuteallCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'muteall'; }
    public function getDescription(): string { return 'Butun guruhning ovozini o\'chiradi (/muteall off - qaytarish)'; }
    public function getPermission(): Permission { return Permission::Administrator; }

    public function getMiddleware(): array
    {
        return [
            new GroupOnlyMiddleware($this->app),
            new PermissionMiddleware($this->app, Permission::Administrator),
        ];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $client   = $app->make(TelegramClient::class);
        $chatId   = $update->getChatId();
        $args     = strtolower(trim($update->getCommandArgs()));

        $unmute = ($args === 'off' || $args === 'false' || $args === '0');

        $permissions = $unmute
            ? [
                'can_send_messages'         => true,
                'can_send_audios'           => true,
                'can_send_documents'        => true,
                'can_send_photos'           => true,
                'can_send_videos'           => true,
                'can_send_video_notes'      => true,
                'can_send_voice_notes'      => true,
                'can_send_polls'            => true,
                'can_send_other_messages'   => true,
                'can_add_web_page_previews' => true,
            ]
            : [
                'can_send_messages'         => false,
                'can_send_audios'           => false,
                'can_send_documents'        => false,
                'can_send_photos'           => false,
                'can_send_videos'           => false,
                'can_send_video_notes'      => false,
                'can_send_voice_notes'      => false,
                'can_send_polls'            => false,
                'can_send_other_messages'   => false,
                'can_add_web_page_previews' => false,
            ];

        try {
            $client->request('setChatPermissions', [
                'chat_id'     => $chatId,
                'permissions' => $permissions,
            ]);

            $msgKey = $unmute ? 'Mute.unmuted_all' : 'Mute.muteall_done';
            // Fallback para chaves que podem não existir no language file base
            $text = match($msgKey) {
                'Mute.unmuted_all' => '🔊 Todos os membros podem falar novamente.',
                default            => $lang->trans($msgKey),
            };

            $telegram->reply($update, $text);
        } catch (\Throwable) {
            $telegram->reply($update, $lang->trans('Mute.muteall_failed'));
        }
    }
}
