<?php
declare(strict_types=1);

namespace Modules\AntiRaid\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\AntiRaid\Services\RaidDetectorService;

/**
 * Ouve user.joined: detecta pico de entradas e ativa o modo de raid.
 */
class RaidDetector
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

        $service = $this->app->make(RaidDetectorService::class);

        $wasAlreadyActive = $service->isRaidActive($chatId);
        $raidTriggered    = $service->trackJoin($chatId);

        if (!$raidTriggered) return;

        // Aplica ação ao usuário recém-entrado
        $service->applyRaidAction($chatId, $userId);

        // Se o raid foi recém-ativado, envia alerta
        if (!$wasAlreadyActive) {
            $lang     = $this->app->make(LanguageService::class);
            $duration = $service->getDuration($chatId);
            $action   = $service->getAction($chatId);
            $text     = $lang->trans('AntiRaid.raid_detected', [
                ':duration' => $duration,
                ':action'   => $action,
            ]);
            $text = str_replace('\n', "\n", $text);
            try {
                $this->app->make(TelegramClient::class)
                    ->sendMessage($chatId, $text, ['parse_mode' => 'HTML']);
            } catch (\Throwable) {}
        }
    }
}
