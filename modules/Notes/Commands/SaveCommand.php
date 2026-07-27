<?php
declare(strict_types=1);

namespace Modules\Notes\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Notes\Services\NotesService;

/**
 * /save — Salva uma nota para o grupo.
 * Uso: /save <nome> <conteúdo>  ou  responder a uma mensagem com /save <nome>
 */
class SaveCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'save'; }
    public function getDescription(): string { return 'Guruh eslatmasini saqlaydi (/save nom matn)'; }
    public function getPermission(): Permission { return Permission::Administrator; }

    public function getMiddleware(): array
    {
        return [
            new GroupOnlyMiddleware($this->app),
            new PermissionMiddleware($this->app, Permission::Administrator),
        ];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $service  = $app->make(NotesService::class);
        $chatId   = $update->getChatId();
        $args     = trim($update->getCommandArgs());
        $reply    = $update->getReplyToMessage();

        // Extrai o nome (primeiro token dos args)
        $parts = explode(' ', $args, 2);
        $name  = strtolower(trim($parts[0] ?? ''));

        if ($name === '') {
            $telegram->reply($update, $lang->trans('Notes.save_usage'));
            return;
        }

        // Conteúdo: restante dos args ou texto/caption da mensagem respondida
        $content = trim($parts[1] ?? '');

        if ($content === '' && $reply !== null) {
            $content = $reply['text'] ?? $reply['caption'] ?? '';

            // Nota de mídia (documento, foto, etc.)
            if ($content === '' || isset($reply['document'], $reply['photo'], $reply['video'])) {
                $fileId  = $reply['document']['file_id']
                    ?? ($reply['photo'] ? end($reply['photo'])['file_id'] : null)
                    ?? $reply['video']['file_id']
                    ?? null;

                if ($fileId !== null) {
                    $service->save($chatId, $name, $content ?: $name, $update->getUserId(), true, $fileId);
                    $text = $lang->trans('Notes.saved', [':name' => $name]);
                    $telegram->reply($update, $text);
                    return;
                }
            }
        }

        if ($content === '') {
            $telegram->reply($update, $lang->trans('Notes.save_usage'));
            return;
        }

        $service->save($chatId, $name, $content, $update->getUserId());
        $text = $lang->trans('Notes.saved', [':name' => $name]);
        $telegram->reply($update, $text);
    }
}
