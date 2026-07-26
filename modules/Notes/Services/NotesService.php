<?php
declare(strict_types=1);

namespace Modules\Notes\Services;

use App\Core\Application;
use App\Core\EventDispatcher;
use App\Core\Services\{LoggerService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Notes\Repository\NotesRepository;

class NotesService
{
    public function __construct(private readonly Application $app) {}

    public function save(int $chatId, string $name, string $content, int $createdBy, bool $isMedia = false, ?string $fileId = null): void
    {
        $this->app->make(NotesRepository::class)->upsert([
            'chat_id'    => $chatId,
            'name'       => strtolower($name),
            'content'    => $content,
            'is_media'   => $isMedia ? 1 : 0,
            'file_id'    => $fileId,
            'created_by' => $createdBy,
        ]);

        $this->app->make(EventDispatcher::class)->emit('note.saved', [
            'chat_id' => $chatId,
            'name'    => $name,
            'user_id' => $createdBy,
        ]);
    }

    public function get(int $chatId, string $name): ?array
    {
        return $this->app->make(NotesRepository::class)->findByName($chatId, $name);
    }

    public function listAll(int $chatId): array
    {
        return $this->app->make(NotesRepository::class)->findAllForChat($chatId);
    }

    public function delete(int $chatId, string $name): bool
    {
        $deleted = $this->app->make(NotesRepository::class)->deleteByName($chatId, $name);

        if ($deleted) {
            $this->app->make(EventDispatcher::class)->emit('note.deleted', [
                'chat_id' => $chatId,
                'name'    => $name,
            ]);
        }

        return $deleted;
    }

    /**
     * Send a note to the chat. Handles both text and media notes.
     */
    public function sendNote(Update $update, array $note): void
    {
        $chatId  = $update->getChatId();
        $client  = $this->app->make(TelegramClient::class);
        $content = $note['content'];

        if ($note['is_media'] && $note['file_id']) {
            // Media note — send the file with the content as caption
            $client->request('sendDocument', [
                'chat_id'    => $chatId,
                'document'   => $note['file_id'],
                'caption'    => $content,
                'parse_mode' => 'HTML',
            ]);
        } else {
            $this->app->make(TelegramService::class)->reply($update, $content);
        }
    }
}
