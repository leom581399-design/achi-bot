<?php
declare(strict_types=1);

namespace Modules\Captcha\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Captcha\Services\CaptchaService;

/**
 * Ouve message.received: verifica respostas de captcha math/text.
 * Também expulsa usuários cujo captcha expirou.
 */
class CaptchaAnswerListener
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

        $service = $this->app->make(CaptchaService::class);
        if (!$service->isEnabled($chatId)) return;
        if (!$service->hasPending($chatId, $userId)) return;

        $lang   = $this->app->make(LanguageService::class);
        $client = $this->app->make(TelegramClient::class);
        $user   = $update->message['from'] ?? [];
        $name   = htmlspecialchars($user['first_name'] ?? 'Foydalanuvchi');

        // Verifica se expirou
        if ($service->isExpired($chatId, $userId)) {
            $msgId = $update->getMessageId();
            if ($msgId) {
                try { $client->deleteMessage($chatId, $msgId); } catch (\Throwable) {}
            }
            $service->fail($chatId, $userId);
            $text = $lang->trans('Captcha.captcha_expired', [':name' => $name]);
            try { $client->sendMessage($chatId, $text, ['parse_mode' => 'HTML']); } catch (\Throwable) {}
            return;
        }

        // Só processa captcha do tipo math ou text (button é tratado via callback)
        $type = $service->getPendingType($chatId, $userId);
        if ($type === 'button') return;

        $input = trim($update->getText() ?? '');
        if ($input === '') return;

        // Deleta a resposta do usuário independentemente do resultado
        $msgId = $update->getMessageId();
        if ($msgId) {
            try { $client->deleteMessage($chatId, $msgId); } catch (\Throwable) {}
        }

        if ($service->verify($chatId, $userId, $input)) {
            $service->pass($chatId, $userId);
            $text = $lang->trans('Captcha.captcha_passed', [':name' => $name]);
        } else {
            $service->fail($chatId, $userId);
            $text = $lang->trans('Captcha.captcha_failed', [':name' => $name]);
        }

        try { $client->sendMessage($chatId, $text, ['parse_mode' => 'HTML']); } catch (\Throwable) {}
    }
}
