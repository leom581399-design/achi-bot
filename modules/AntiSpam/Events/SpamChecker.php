<?php
declare(strict_types=1);

namespace Modules\AntiSpam\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\AntiSpam\Services\SpamDetector;

/**
 * Ouve message.received: detecta spam por links excessivos ou mensagens repetidas.
 * Deleta a mensagem e notifica o grupo.
 */
class SpamChecker
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
        if ($update->isCommand()) return; // não interfere com comandos

        $chatId = $update->getChatId();
        $userId = $update->getUserId();
        if ($chatId === null || $userId === null) return;

        $detector = $this->app->make(SpamDetector::class);
        if (!$detector->isEnabled($chatId)) return;

        $telegram = $this->app->make(TelegramService::class);
        if ($telegram->isAdmin($chatId, $userId)) return; // admins são isentos

        $spamType = $detector->detectSpam($update, $chatId, $userId);
        if ($spamType === null) return;

        $detector->handleSpam($chatId, $userId, $update->getMessageId(), $spamType);

        $lang = $this->app->make(LanguageService::class);
        $name = $telegram->formatUser($update->message['from'] ?? []);

        $key  = match ($spamType) {
            'links'    => 'AntiSpam.spam_links',
            'repeated' => 'AntiSpam.spam_repeated',
            default    => 'AntiSpam.spam_repeated',
        };

        $text = $lang->trans($key, [':name' => $name]);

        try {
            $this->app->make(TelegramClient::class)
                ->sendMessage($chatId, $text, ['parse_mode' => 'HTML']);
        } catch (\Throwable) {}
    }
}
