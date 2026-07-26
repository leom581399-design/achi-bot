<?php
declare(strict_types=1);

namespace App\Core\Telegram;

/**
 * Low-level Telegram Bot API client.
 *
 * This is the ONLY place that calls the Telegram API directly.
 * All modules must go through TelegramService (or this client via DI).
 * Never make raw cURL calls in a command or module.
 */
class TelegramClient
{
    private const API_BASE = 'https://api.telegram.org/bot';

    public function __construct(
        private readonly string $token
    ) {}

    // -------------------------------------------------------------------------
    // Polling
    // -------------------------------------------------------------------------

    public function getUpdates(int $offset = 0, int $limit = 100, int $timeout = 30): array
    {
        $result = $this->request('getUpdates', [
            'offset'  => $offset,
            'limit'   => $limit,
            'timeout' => $timeout,
        ]);
        return $result['result'] ?? [];
    }

    public function getMe(): array
    {
        return $this->request('getMe')['result'];
    }

    // -------------------------------------------------------------------------
    // Messaging
    // -------------------------------------------------------------------------

    public function sendMessage(int|string $chatId, string $text, array $options = []): array
    {
        return $this->request('sendMessage', array_merge([
            'chat_id'    => $chatId,
            'text'       => $text,
            'parse_mode' => 'HTML',
        ], $options));
    }

    public function editMessageText(int|string $chatId, int $messageId, string $text, array $options = []): array
    {
        return $this->request('editMessageText', array_merge([
            'chat_id'    => $chatId,
            'message_id' => $messageId,
            'text'       => $text,
            'parse_mode' => 'HTML',
        ], $options));
    }

    public function deleteMessage(int|string $chatId, int $messageId): array
    {
        return $this->request('deleteMessage', [
            'chat_id'    => $chatId,
            'message_id' => $messageId,
        ]);
    }

    public function forwardMessage(int|string $chatId, int|string $fromChatId, int $messageId): array
    {
        return $this->request('forwardMessage', [
            'chat_id'      => $chatId,
            'from_chat_id' => $fromChatId,
            'message_id'   => $messageId,
        ]);
    }

    public function sendDocument(int|string $chatId, string $document, array $options = []): array
    {
        return $this->request('sendDocument', array_merge([
            'chat_id'  => $chatId,
            'document' => $document,
        ], $options));
    }

    /**
     * Envia conteúdo em memória como documento (multipart/form-data).
     * Usado pelo módulo Backup para enviar o JSON sem gravar em disco.
     */
    public function sendDocumentContent(
        int|string $chatId,
        string $content,
        string $filename,
        string $caption = '',
        array $options  = []
    ): array {
        $url = self::API_BASE . $this->token . '/sendDocument';

        $params = array_merge([
            'chat_id'    => $chatId,
            'caption'    => $caption,
            'parse_mode' => 'HTML',
        ], $options);

        // Cria um CURLFile a partir do conteúdo em memória via stream temporário
        $tmp = tmpfile();
        fwrite($tmp, $content);
        $meta    = stream_get_meta_data($tmp);
        $tmpPath = $meta['uri'];

        $params['document'] = new \CURLFile($tmpPath, 'application/json', $filename);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $params,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 40,
        ]);

        $response = curl_exec($ch);
        $curlErr  = curl_error($ch);
        curl_close($ch);
        fclose($tmp);

        if ($curlErr) {
            throw new \RuntimeException("cURL error calling sendDocument: {$curlErr}");
        }

        $data = json_decode($response, true, 512, JSON_THROW_ON_ERROR);

        if (!($data['ok'] ?? false)) {
            $desc = $data['description'] ?? 'Unknown error';
            $code = $data['error_code']  ?? 0;
            throw new TelegramApiException("sendDocument failed [{$code}]: {$desc}", $code);
        }

        return $data;
    }

    // -------------------------------------------------------------------------
    // File download (para restore de backup)
    // -------------------------------------------------------------------------

    /**
     * Obtém informações de um arquivo pelo file_id.
     * Retorna o objeto File com file_path pronto para download.
     */
    public function getFile(string $fileId): array
    {
        return $this->request('getFile', ['file_id' => $fileId])['result'];
    }

    /**
     * Baixa o conteúdo de um arquivo do Telegram pelo file_path.
     * Retorna o conteúdo como string ou false em caso de erro.
     */
    public function downloadFile(string $filePath): string|false
    {
        $url = 'https://api.telegram.org/file/bot' . $this->token . '/' . $filePath;

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 30,
            CURLOPT_FOLLOWLOCATION => true,
        ]);

        $content = curl_exec($ch);
        $err     = curl_error($ch);
        curl_close($ch);

        if ($err || $content === false) {
            throw new \RuntimeException("Falha ao baixar arquivo do Telegram: {$err}");
        }

        return $content;
    }

    // -------------------------------------------------------------------------
    // Member management
    // -------------------------------------------------------------------------

    public function banChatMember(int|string $chatId, int $userId, array $options = []): array
    {
        return $this->request('banChatMember', array_merge([
            'chat_id' => $chatId,
            'user_id' => $userId,
        ], $options));
    }

    public function unbanChatMember(int|string $chatId, int $userId, bool $onlyIfBanned = true): array
    {
        return $this->request('unbanChatMember', [
            'chat_id'        => $chatId,
            'user_id'        => $userId,
            'only_if_banned' => $onlyIfBanned,
        ]);
    }

    public function restrictChatMember(int|string $chatId, int $userId, array $permissions, array $options = []): array
    {
        return $this->request('restrictChatMember', array_merge([
            'chat_id'     => $chatId,
            'user_id'     => $userId,
            'permissions' => $permissions,
        ], $options));
    }

    public function promoteChatMember(int|string $chatId, int $userId, array $options = []): array
    {
        return $this->request('promoteChatMember', array_merge([
            'chat_id' => $chatId,
            'user_id' => $userId,
        ], $options));
    }

    // -------------------------------------------------------------------------
    // Chat info
    // -------------------------------------------------------------------------

    public function getChat(int|string $chatId): array
    {
        return $this->request('getChat', ['chat_id' => $chatId])['result'];
    }

    public function getChatMember(int|string $chatId, int $userId): array
    {
        return $this->request('getChatMember', [
            'chat_id' => $chatId,
            'user_id' => $userId,
        ])['result'];
    }

    public function getChatAdministrators(int|string $chatId): array
    {
        return $this->request('getChatAdministrators', ['chat_id' => $chatId])['result'];
    }

    public function getChatMemberCount(int|string $chatId): int
    {
        return $this->request('getChatMemberCount', ['chat_id' => $chatId])['result'];
    }

    // -------------------------------------------------------------------------
    // Callbacks & Inline
    // -------------------------------------------------------------------------

    public function answerCallbackQuery(string $callbackQueryId, array $options = []): array
    {
        return $this->request('answerCallbackQuery', array_merge([
            'callback_query_id' => $callbackQueryId,
        ], $options));
    }

    public function answerInlineQuery(string $inlineQueryId, array $results, array $options = []): array
    {
        return $this->request('answerInlineQuery', array_merge([
            'inline_query_id' => $inlineQueryId,
            'results'         => $results,
        ], $options));
    }

    // -------------------------------------------------------------------------
    // Core HTTP
    // -------------------------------------------------------------------------

    public function request(string $method, array $params = []): array
    {
        $url = self::API_BASE . $this->token . '/' . $method;

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => json_encode($params, JSON_THROW_ON_ERROR),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_TIMEOUT        => 40,
        ]);

        $response = curl_exec($ch);
        $curlErr  = curl_error($ch);
        curl_close($ch);

        if ($curlErr) {
            throw new \RuntimeException("cURL error calling {$method}: {$curlErr}");
        }

        $data = json_decode($response, true, 512, JSON_THROW_ON_ERROR);

        if (!($data['ok'] ?? false)) {
            $desc = $data['description'] ?? 'Unknown error';
            $code = $data['error_code']  ?? 0;
            throw new TelegramApiException("{$method} failed [{$code}]: {$desc}", $code);
        }

        return $data;
    }
}
