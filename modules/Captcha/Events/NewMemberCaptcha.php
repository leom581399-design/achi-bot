<?php
declare(strict_types=1);

namespace Modules\Captcha\Events;

use App\Core\Application;
use App\Core\Services\{LanguageService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Captcha\Services\CaptchaService;

/**
 * Ouve user.joined: se captcha estiver ativo, muta o novo membro e envia o desafio.
 */
class NewMemberCaptcha
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

        $service = $this->app->make(CaptchaService::class);
        if (!$service->isEnabled($chatId)) return;

        $type    = $service->getType($chatId);
        $timeout = $service->getTimeout($chatId);
        $lang    = $this->app->make(LanguageService::class);
        $client  = $this->app->make(TelegramClient::class);

        $name = htmlspecialchars($user['first_name'] ?? 'Usuário');

        // Muta o usuário
        try {
            $client->restrictChatMember($chatId, $userId, ['can_send_messages' => false]);
        } catch (\Throwable) {}

        // Gera desafio e envia a mensagem
        [$text, $answer, $extra] = $this->buildChallenge($type, $name, $timeout, $userId, $lang);

        $msgId = null;
        try {
            $result = $client->sendMessage($chatId, $text, array_merge(['parse_mode' => 'HTML'], $extra));
            $msgId  = $result['result']['message_id'] ?? null;
        } catch (\Throwable) {}

        // Registra no cache via service
        $service->setPending($chatId, $userId, $answer, $msgId, $type, $timeout);
    }

    private function buildChallenge(string $type, string $name, int $timeout, int $userId, LanguageService $lang): array
    {
        return match ($type) {
            'math'  => $this->buildMath($name, $timeout, $lang),
            'text'  => $this->buildText($name, $timeout, $lang),
            default => $this->buildButton($name, $timeout, $userId, $lang),
        };
    }

    private function buildButton(string $name, int $timeout, int $userId, LanguageService $lang): array
    {
        $text = $lang->trans('Captcha.captcha_button', [':name' => $name, ':timeout' => $timeout]);
        $keyboard = [
            'inline_keyboard' => [[
                ['text' => $lang->trans('Captcha.btn_verify'), 'callback_data' => "captcha_ok:{$userId}"],
                ['text' => $lang->trans('Captcha.btn_wrong'),  'callback_data' => "captcha_no:{$userId}_1"],
                ['text' => $lang->trans('Captcha.btn_wrong'),  'callback_data' => "captcha_no:{$userId}_2"],
            ]],
        ];
        return [str_replace('\n', "\n", $text), 'button_ok', ['reply_markup' => $keyboard]];
    }

    private function buildMath(string $name, int $timeout, LanguageService $lang): array
    {
        $a      = random_int(2, 20);
        $b      = random_int(1, 10);
        $ops    = ['+', '-'];
        $op     = $ops[array_rand($ops)];
        $answer = $op === '+' ? (string)($a + $b) : (string)($a - $b);
        $q      = "{$a} {$op} {$b}";
        $text   = $lang->trans('Captcha.captcha_math', [':name' => $name, ':timeout' => $timeout, ':question' => $q]);
        return [str_replace('\n', "\n", $text), $answer, []];
    }

    private function buildText(string $name, int $timeout, LanguageService $lang): array
    {
        $words = ['gato','casa','verde','azul','livro','porta','carro','agua','terra','sol'];
        $word  = $words[array_rand($words)];
        $text  = $lang->trans('Captcha.captcha_text', [':name' => $name, ':timeout' => $timeout, ':word' => $word]);
        return [str_replace('\n', "\n", $text), $word, []];
    }
}
