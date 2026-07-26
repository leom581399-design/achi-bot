<?php
declare(strict_types=1);

namespace Modules\Stats\Events;

use App\Core\Application;
use App\Core\Update;
use Modules\Stats\Services\StatsService;

/**
 * Escuta o evento 'message.received' e incrementa as estatísticas do usuário.
 * Ignora bots e mensagens de sistema.
 */
class MessageStatsListener
{
    public function __construct(private readonly Application $app) {}

    public function __invoke(Update $update): void
    {
        try {
            $chatId = $update->getChatId();
            $userId = $update->getUserId();

            // Só grupos e supergrupos
            $chatType = $update->getRaw()['message']['chat']['type'] ?? '';
            if (!in_array($chatType, ['group', 'supergroup'], true)) return;

            // Ignorar bots
            $isBot = $update->getRaw()['message']['from']['is_bot'] ?? false;
            if ($isBot) return;

            // Usuário e chat válidos
            if ($chatId === 0 || $userId === 0) return;

            $this->app->make(StatsService::class)->record($chatId, $userId);
        } catch (\Throwable) {
            // Nunca deixar erros de stats interromper o processamento
        }
    }
}
