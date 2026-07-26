<?php
declare(strict_types=1);

namespace Modules\Approval\Services;

use App\Core\Application;
use App\Core\Services\{LoggerService, SettingsService};
use App\Core\Telegram\TelegramClient;

/**
 * ApprovalService — gerencia aprovação manual de novos membros.
 *
 * Quando o modo de aprovação está ativo, novos membros são silenciados
 * automaticamente ao entrar. Admins usam /approve ou /deny para liberar
 * ou remover o usuário.
 *
 * Configurações por grupo (SettingsService, módulo 'Approval'):
 *   enabled  bool — padrão: false
 */
class ApprovalService
{
    public function __construct(private readonly Application $app) {}

    /**
     * Silencia o novo membro aguardando aprovação.
     */
    public function restrict(int $chatId, int $userId): void
    {
        try {
            $this->app->make(TelegramClient::class)->restrictChatMember(
                $chatId, $userId, ['can_send_messages' => false]
            );
        } catch (\Throwable) {}
    }

    /**
     * Aprova o usuário — restaura as permissões padrão do grupo.
     */
    public function approve(int $chatId, int $userId): bool
    {
        try {
            $this->app->make(TelegramClient::class)->restrictChatMember($chatId, $userId, [
                'can_send_messages'        => true,
                'can_send_audios'          => true,
                'can_send_documents'       => true,
                'can_send_photos'          => true,
                'can_send_videos'          => true,
                'can_send_video_notes'     => true,
                'can_send_voice_notes'     => true,
                'can_send_polls'           => true,
                'can_send_other_messages'  => true,
                'can_add_web_page_previews'=> true,
            ]);

            $this->app->make(LoggerService::class)->security(
                "APPROVAL_APPROVE chat={$chatId} user={$userId}"
            );
            return true;
        } catch (\Throwable) {
            return false;
        }
    }

    /**
     * Nega o usuário — bane e desbane (kick permanente).
     */
    public function deny(int $chatId, int $userId): bool
    {
        $client = $this->app->make(TelegramClient::class);
        try {
            $client->banChatMember($chatId, $userId);

            $this->app->make(LoggerService::class)->security(
                "APPROVAL_DENY chat={$chatId} user={$userId}"
            );
            return true;
        } catch (\Throwable) {
            return false;
        }
    }

    // -------------------------------------------------------------------------
    // Settings
    // -------------------------------------------------------------------------

    public function isEnabled(int $chatId): bool
    {
        return (bool)$this->setting($chatId, 'enabled', false);
    }

    public function setEnabled(int $chatId, bool $value): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Approval', 'enabled', $value);
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private function setting(int $chatId, string $key, mixed $default): mixed
    {
        if (!$this->app->has(SettingsService::class)) return $default;
        return $this->app->make(SettingsService::class)->get($chatId, 'Approval', $key, $default);
    }
}
