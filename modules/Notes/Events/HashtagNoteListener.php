<?php
declare(strict_types=1);

namespace Modules\Notes\Events;

use App\Core\Application;
use App\Core\Update;
use Modules\Notes\Services\NotesService;

/**
 * Listener do evento message.received — detecta #nomeDaNota no texto.
 * Quando encontrado, envia a nota correspondente automaticamente.
 *
 * Registrado em NotesModule::getEvents() como callable via __invoke.
 */
class HashtagNoteListener
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
        if ($update === null) return;

        $text = $update->getText();
        if ($text === null || $text === '') return;

        // Detecta tokens #nomeDaNota no texto
        if (!preg_match_all('/#([a-zA-Z0-9_]+)/', $text, $matches)) {
            return;
        }

        $chatId  = $update->getChatId();
        $service = $this->app->make(NotesService::class);

        foreach ($matches[1] as $noteName) {
            $note = $service->get($chatId, strtolower($noteName));
            if ($note !== null) {
                $service->sendNote($update, $note);
                // Envia apenas a primeira nota encontrada para evitar spam
                return;
            }
        }
    }
}
