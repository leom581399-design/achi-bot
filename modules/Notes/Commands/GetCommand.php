<?php
declare(strict_types=1);

namespace Modules\Notes\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Notes\Services\NotesService;

/**
 * /get <nome> — Recupera e exibe uma nota do grupo.
 */
class GetCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'get'; }
    public function getDescription(): string { return 'Exibe uma nota do grupo (/get nome)'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $service  = $app->make(NotesService::class);
        $chatId   = $update->getChatId();
        $name     = strtolower(trim($update->getCommandArgs()));

        if ($name === '') {
            $telegram->reply($update, $lang->trans('Notes.get_usage'));
            return;
        }

        $note = $service->get($chatId, $name);

        if ($note === null) {
            $text = $lang->trans('Notes.not_found', [':name' => $name]);
            $telegram->reply($update, $text);
            return;
        }

        $service->sendNote($update, $note);
    }
}
