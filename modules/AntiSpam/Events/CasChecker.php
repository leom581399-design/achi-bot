<?php
declare(strict_types=1);

namespace Modules\AntiSpam\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\AntiSpam\Services\SpamDetector;

/**
 * Ouve user.joined: verifica o novo membro no banco CAS.
 * Se banido, remove do grupo automaticamente.
 */
class CasChecker
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

        $detector = $this->app->make(SpamDetector::class);

        if (!$detector->isEnabled($chatId) || !$detector->isCasCheckEnabled($chatId)) return;

        if (!$detector->isCasBanned($userId)) return;

        $name = htmlspecialchars($user['first_name'] ?? 'Usuário');
        $lang = $this->app->make(LanguageService::class);

        $detector->banCasUser($chatId, $userId, $name);

        $text = $lang->trans('AntiSpam.cas_banned', [':name' => $name]);
        try {
            $this->app->make(TelegramClient::class)
                ->sendMessage($chatId, $text, ['parse_mode' => 'HTML']);
        } catch (\Throwable) {}
    }
}
