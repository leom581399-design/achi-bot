<?php
declare(strict_types=1);

namespace Modules\Approval\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Approval\Services\ApprovalService;

/**
 * Ouve user.joined: se o modo de aprovação estiver ativo, muta o novo membro
 * e notifica os admins para aprovar ou negar via /approve / /deny.
 */
class NewMemberApproval
{
    public function __construct(private readonly Application $app) {}

    public function __invoke(mixed $data): void
    {
        $this->handle(is_array($data) ? $data : []);
    }

    public function handle(array $data): void
    {
        /** @var Update $update */
        $update = $data['update'] ?? null;
        $user   = $data['member'] ?? $data['user'] ?? null;

        if ($update === null || $user === null) return;
        if ($user['is_bot'] ?? false) return;

        $chatId = $update->getChatId();
        $userId = (int)($user['id'] ?? 0);
        if ($chatId === null || $userId === 0) return;

        $service = $this->app->make(ApprovalService::class);
        if (!$service->isEnabled($chatId)) return;

        // Muta o novo membro
        $service->restrict($chatId, $userId);

        $lang = $this->app->make(LanguageService::class);
        $name = htmlspecialchars($user['first_name'] ?? 'Usuário');
        $text = $lang->trans('Approval.pending_join', [':name' => $name]);
        $text = str_replace('\n', "\n", $text);

        try {
            $this->app->make(TelegramClient::class)
                ->sendMessage($chatId, $text, ['parse_mode' => 'HTML']);
        } catch (\Throwable) {}
    }
}
