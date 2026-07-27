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
 * /clear <nome> — Remove uma nota do grupo.
 */
class ClearCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'clear'; }
    public function getDescription(): string { return 'Guruh eslatmasini o\'chiradi (/clear nom)'; }
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
        $name     = strtolower(trim($update->getCommandArgs()));

        if ($name === '') {
            $telegram->reply($update, $lang->trans('Notes.clear_usage'));
            return;
        }

        $deleted = $service->delete($chatId, $name);

        if (!$deleted) {
            $text = $lang->trans('Notes.clear_not_found', [':name' => $name]);
            $telegram->reply($update, $text);
            return;
        }

        $text = $lang->trans('Notes.cleared', [':name' => $name]);
        $telegram->reply($update, $text);
    }
}
