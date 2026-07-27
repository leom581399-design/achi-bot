<?php
declare(strict_types=1);

namespace Modules\Captcha\Services;

use App\Core\Application;
use App\Core\Services\{CacheService, LoggerService, SettingsService};
use App\Core\Telegram\TelegramClient;

/**
 * CaptchaService — gerencia desafios de captcha para novos membros.
 *
 * Configurações por grupo (SettingsService, módulo 'Captcha'):
 *   enabled  bool   — padrão: false
 *   type     string — button|math|text (padrão: button)
 *   timeout  int    — segundos para responder (padrão: 90)
 *
 * Cache keys (prefixo captcha:{chatId}:{userId}):
 *   :answer   — resposta correta esperada (string)
 *   :msg_id   — ID da mensagem de captcha a deletar no sucesso
 *   :type     — tipo do captcha
 *   :expires  — timestamp de expiração
 */
class CaptchaService
{
    private const WORDS = ['olma','uzum','tog\'','osmon','kitob','eshik','mashina','suv','yer','quyosh'];

    public function __construct(private readonly Application $app) {}

    // -------------------------------------------------------------------------
    // Captcha lifecycle
    // -------------------------------------------------------------------------

    /**
     * Inicia o captcha para um novo membro: muta, envia desafio, registra no cache.
     */
    public function start(int $chatId, int $userId, array $user): void
    {
        $type    = $this->getType($chatId);
        $timeout = $this->getTimeout($chatId);
        $client  = $this->app->make(TelegramClient::class);

        // Muta o usuário até passar no captcha
        try {
            $client->restrictChatMember($chatId, $userId, ['can_send_messages' => false]);
        } catch (\Throwable) {}

        $name = htmlspecialchars($user['first_name'] ?? 'Foydalanuvchi');

        [$text, $answer, $extra] = match ($type) {
            'math'  => $this->buildMath($name, $timeout),
            'text'  => $this->buildText($name, $timeout),
            default => $this->buildButton($name, $timeout, $userId),
        };

        try {
            $result = $client->sendMessage($chatId, $text, array_merge(['parse_mode' => 'HTML'], $extra));
            $msgId  = $result['result']['message_id'] ?? null;
        } catch (\Throwable) {
            $msgId = null;
        }

        // Registra estado no cache
        $cache = $this->cache();
        $cache->set("captcha:{$chatId}:{$userId}:answer",  $answer,  $timeout + 30);
        $cache->set("captcha:{$chatId}:{$userId}:msg_id",  $msgId,   $timeout + 30);
        $cache->set("captcha:{$chatId}:{$userId}:type",    $type,    $timeout + 30);
        $cache->set("captcha:{$chatId}:{$userId}:expires", time() + $timeout, $timeout + 30);
    }

    /**
     * Verifica se existe captcha pendente para o usuário.
     */
    public function hasPending(int $chatId, int $userId): bool
    {
        return $this->cache()->has("captcha:{$chatId}:{$userId}:answer");
    }

    /**
     * Verifica se o captcha expirou.
     */
    public function isExpired(int $chatId, int $userId): bool
    {
        $expires = $this->cache()->get("captcha:{$chatId}:{$userId}:expires");
        if ($expires === null) return true; // já expirou e foi removido pelo cache TTL
        return time() > (int)$expires;
    }

    /**
     * Verifica a resposta do usuário. Retorna true se correta.
     */
    public function verify(int $chatId, int $userId, string $input): bool
    {
        $expected = $this->cache()->get("captcha:{$chatId}:{$userId}:answer");
        if ($expected === null) return false;
        return strtolower(trim($input)) === strtolower(trim($expected));
    }

    /**
     * Libera o usuário (captcha passou): remove restrição e limpa cache.
     */
    public function pass(int $chatId, int $userId): void
    {
        $this->deleteCaptchaMessage($chatId, $userId);
        $this->clearCache($chatId, $userId);

        try {
            // Restaura permissões padrão do grupo
            $this->app->make(TelegramClient::class)->restrictChatMember($chatId, $userId, [
                'can_send_messages'       => true,
                'can_send_audios'         => true,
                'can_send_documents'      => true,
                'can_send_photos'         => true,
                'can_send_videos'         => true,
                'can_send_video_notes'    => true,
                'can_send_voice_notes'    => true,
                'can_send_polls'          => true,
                'can_send_other_messages' => true,
                'can_add_web_page_previews' => true,
            ]);
        } catch (\Throwable) {}
    }

    /**
     * Reprovado (timeout ou resposta errada): expulsa e limpa cache.
     */
    public function fail(int $chatId, int $userId): void
    {
        $this->deleteCaptchaMessage($chatId, $userId);
        $this->clearCache($chatId, $userId);

        $client = $this->app->make(TelegramClient::class);
        try {
            $client->banChatMember($chatId, $userId);
            $client->unbanChatMember($chatId, $userId); // kick, não ban permanente
        } catch (\Throwable) {}

        $this->app->make(LoggerService::class)->security(
            "CAPTCHA_FAIL chat={$chatId} user={$userId}"
        );
    }

    // -------------------------------------------------------------------------
    // Settings accessors
    // -------------------------------------------------------------------------

    public function isEnabled(int $chatId): bool
    {
        return (bool) $this->setting($chatId, 'enabled', false);
    }

    public function getType(int $chatId): string
    {
        return $this->setting($chatId, 'type', 'button');
    }

    public function getTimeout(int $chatId): int
    {
        return max(30, (int) $this->setting($chatId, 'timeout', 90));
    }

    public function setEnabled(int $chatId, bool $value): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Captcha', 'enabled', $value);
    }

    public function setType(int $chatId, string $type): void
    {
        $this->app->make(SettingsService::class)->set($chatId, 'Captcha', 'type', $type);
    }

    /**
     * Registra o estado pendente do captcha no cache (chamado pelo evento após enviar a mensagem).
     */
    public function setPending(int $chatId, int $userId, string $answer, ?int $msgId, string $type, int $timeout): void
    {
        $cache = $this->cache();
        $cache->set("captcha:{$chatId}:{$userId}:answer",  $answer,          $timeout + 30);
        $cache->set("captcha:{$chatId}:{$userId}:msg_id",  $msgId ?? 0,      $timeout + 30);
        $cache->set("captcha:{$chatId}:{$userId}:type",    $type,            $timeout + 30);
        $cache->set("captcha:{$chatId}:{$userId}:expires", time() + $timeout, $timeout + 30);
    }

    /**
     * Retorna o tipo do captcha pendente do usuário, ou null se não houver.
     */
    public function getPendingType(int $chatId, int $userId): ?string
    {
        return $this->cache()->get("captcha:{$chatId}:{$userId}:type");
    }

    // -------------------------------------------------------------------------
    // Builders
    // -------------------------------------------------------------------------

    private function buildButton(string $name, int $timeout, int $userId): array
    {
        $text    = str_replace([':name', ':timeout'], [$name, $timeout],
            $this->lang('captcha_button'));
        $keyboard = [
            'inline_keyboard' => [[
                ['text' => $this->lang('btn_verify'), 'callback_data' => "captcha_ok:{$userId}"],
                ['text' => $this->lang('btn_wrong'),  'callback_data' => "captcha_no:{$userId}"],
                ['text' => $this->lang('btn_wrong'),  'callback_data' => "captcha_no:{$userId}"],
            ]],
        ];
        return [$text, 'button_ok', ['reply_markup' => $keyboard]];
    }

    private function buildMath(string $name, int $timeout): array
    {
        $a        = random_int(2, 20);
        $b        = random_int(2, 20);
        $op       = ['+', '-', '×'][random_int(0, 1)]; // apenas + e - para evitar decimais
        $answer   = match ($op) {
            '+'  => (string)($a + $b),
            '-'  => (string)($a - $b),
            default => (string)($a + $b),
        };
        $question = "{$a} {$op} {$b}";
        $text     = str_replace([':name', ':timeout', ':question'], [$name, $timeout, $question],
            $this->lang('captcha_math'));
        return [$text, $answer, []];
    }

    private function buildText(string $name, int $timeout): array
    {
        $word = self::WORDS[array_rand(self::WORDS)];
        $text = str_replace([':name', ':timeout', ':word'], [$name, $timeout, $word],
            $this->lang('captcha_text'));
        return [$text, $word, []];
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private function deleteCaptchaMessage(int $chatId, int $userId): void
    {
        $msgId = $this->cache()->get("captcha:{$chatId}:{$userId}:msg_id");
        if ($msgId) {
            try {
                $this->app->make(TelegramClient::class)->deleteMessage($chatId, (int)$msgId);
            } catch (\Throwable) {}
        }
    }

    private function clearCache(int $chatId, int $userId): void
    {
        $cache = $this->cache();
        $cache->delete("captcha:{$chatId}:{$userId}:answer");
        $cache->delete("captcha:{$chatId}:{$userId}:msg_id");
        $cache->delete("captcha:{$chatId}:{$userId}:type");
        $cache->delete("captcha:{$chatId}:{$userId}:expires");
    }

    private function cache(): CacheService
    {
        return $this->app->make(CacheService::class);
    }

    private function setting(int $chatId, string $key, mixed $default): mixed
    {
        if (!$this->app->has(SettingsService::class)) return $default;
        return $this->app->make(SettingsService::class)->get($chatId, 'Captcha', $key, $default);
    }

    private function lang(string $key): string
    {
        // Retorna string bruta do arquivo de linguagem (sem substituições)
        // Substituições são feitas pelo caller
        return $key; // fallback; o LanguageService é usado no evento/comando
    }
}
