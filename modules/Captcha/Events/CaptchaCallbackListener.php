<?php
declare(strict_types=1);

namespace Modules\Captcha\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Captcha\Services\CaptchaService;

/**
 * Ouve callback.received: verifica respostas de captcha do tipo button.
 *
 * callback_data: "captcha_ok:{userId}" ou "captcha_no:{userId}_{n}"
 */
class CaptchaCallbackListener
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
        if ($update === null || $update->callbackQuery === null) return;

        $cb     = $update->callbackQuery;
        $cbData = $cb['data'] ?? '';

        // Só processa callbacks de captcha
        if (!str_starts_with($cbData, 'captcha_')) return;

        $chatId       = $cb['message']['chat']['id'] ?? null;
        $clickerId    = $cb['from']['id'] ?? null;
        $clickerName  = htmlspecialchars($cb['from']['first_name'] ?? 'Usuário');
        $cbQueryId    = $cb['id'] ?? '';

        if ($chatId === null || $clickerId === null) return;

        $service = $this->app->make(CaptchaService::class);
        $lang    = $this->app->make(LanguageService::class);
        $client  = $this->app->make(TelegramClient::class);

        // Extrai o userId alvo do callback_data
        preg_match('/captcha_(?:ok|no):(\d+)/', $cbData, $m);
        $targetUserId = isset($m[1]) ? (int)$m[1] : null;

        // Apenas o usuário alvo pode clicar
        if ($targetUserId !== $clickerId) {
            try {
                $client->answerCallbackQuery($cbQueryId, ['text' => '❌', 'show_alert' => false]);
            } catch (\Throwable) {}
            return;
        }

        if (!$service->hasPending($chatId, $clickerId)) {
            try { $client->answerCallbackQuery($cbQueryId); } catch (\Throwable) {}
            return;
        }

        $isCorrect = str_starts_with($cbData, 'captcha_ok:');

        if ($isCorrect && !$service->isExpired($chatId, $clickerId)) {
            $service->pass($chatId, $clickerId);
            $text = $lang->trans('Captcha.captcha_passed', [':name' => $clickerName]);
            try { $client->answerCallbackQuery($cbQueryId, ['text' => '✅', 'show_alert' => false]); } catch (\Throwable) {}
        } else {
            $service->fail($chatId, $clickerId);
            $text = $service->isExpired($chatId, $clickerId)
                ? $lang->trans('Captcha.captcha_expired', [':name' => $clickerName])
                : $lang->trans('Captcha.captcha_failed',  [':name' => $clickerName]);
            try { $client->answerCallbackQuery($cbQueryId, ['text' => '❌', 'show_alert' => false]); } catch (\Throwable) {}
        }

        try { $client->sendMessage($chatId, $text, ['parse_mode' => 'HTML']); } catch (\Throwable) {}
    }
}
