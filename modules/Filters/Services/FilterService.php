<?php
declare(strict_types=1);

namespace Modules\Filters\Services;

use App\Core\Application;
use App\Core\EventDispatcher;
use App\Core\Services\LoggerService;
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Filters\Repository\FilterRepository;

class FilterService
{
    public function __construct(private readonly Application $app) {}

    /** Salva ou atualiza um filtro de palavra-chave. */
    public function save(int $chatId, string $keyword, string $response, int $createdBy): void
    {
        $keyword = strtolower(trim($keyword));
        $repo    = $this->app->make(FilterRepository::class);

        // Remove existente (upsert manual)
        $repo->deleteByKeyword($chatId, $keyword);
        $repo->create([
            'chat_id'    => $chatId,
            'keyword'    => $keyword,
            'response'   => $response,
            'created_by' => $createdBy,
        ]);

        $this->app->make(LoggerService::class)->info(
            "FILTER_SAVED chat={$chatId} keyword={$keyword} by={$createdBy}"
        );

        $this->app->make(EventDispatcher::class)->emit('filter.saved', [
            'chat_id' => $chatId,
            'keyword' => $keyword,
        ]);
    }

    /** Remove um filtro. Retorna true se existia. */
    public function delete(int $chatId, string $keyword): bool
    {
        $deleted = $this->app->make(FilterRepository::class)
            ->deleteByKeyword($chatId, strtolower($keyword));

        if ($deleted > 0) {
            $this->app->make(LoggerService::class)->info(
                "FILTER_DELETED chat={$chatId} keyword={$keyword}"
            );
            return true;
        }

        return false;
    }

    /** Retorna todos os filtros do chat. */
    public function listAll(int $chatId): array
    {
        return $this->app->make(FilterRepository::class)->findAllForChat($chatId);
    }

    /**
     * Verifica se o texto da mensagem ativa algum filtro e envia a resposta.
     * Retorna true se um filtro foi ativado.
     */
    public function checkAndRespond(Update $update): bool
    {
        $text = $update->getText() ?? $update->getCaption() ?? '';
        if ($text === '') return false;

        $chatId  = $update->getChatId();
        $filters = $this->app->make(FilterRepository::class)->findAllForChat($chatId);

        $textLower = strtolower($text);

        foreach ($filters as $filter) {
            $keyword = $filter['keyword'];

            // Verificação de palavra inteira (case-insensitive)
            if (str_contains($textLower, $keyword)) {
                try {
                    $this->app->make(TelegramClient::class)->sendMessage(
                        $chatId,
                        $filter['response'],
                        ['parse_mode' => 'HTML', 'reply_to_message_id' => $update->getMessageId()]
                    );
                } catch (\Throwable) {
                    // ignora erros de envio
                }
                return true;
            }
        }

        return false;
    }
}
