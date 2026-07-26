<?php
declare(strict_types=1);

namespace Modules\Flood\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Flood\Services\FloodService;

/**
 * Ouve message.received e aplica ação quando o usuário ultrapassa o limite de flood.
 * Admins são isentos.
 */
class FloodChecker
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
        if ($update === null || !$update->isGroup()) return;

        $chatId = $update->getChatId();
        $userId = $update->getUserId();

        if ($chatId === null || $userId === null) return;

        $telegram = $this->app->make(TelegramService::class);

        // Admins e criadores são isentos
        if ($telegram->isAdmin($chatId, $userId)) return;

        $service = $this->app->make(FloodService::class);

        if (!$service->track($chatId, $userId)) return;

        // Limite atingido
        $service->reset($chatId, $userId);
        $service->applyAction($chatId, $userId);

        $lang   = $this->app->make(LanguageService::class);
        $action = $service->getAction($chatId);
        $name   = $telegram->formatUser($update->message['from'] ?? []);

        $actionLabel = $lang->trans('Flood.' . 'action_' . $action);
        $text        = $lang->trans('Flood.flooded', [':name' => $name, ':action' => $actionLabel]);

        try {
            $this->app->make(\App\Core\Telegram\TelegramClient::class)
                ->sendMessage($chatId, $text, ['parse_mode' => 'HTML']);
        } catch (\Throwable) {}
    }
}
