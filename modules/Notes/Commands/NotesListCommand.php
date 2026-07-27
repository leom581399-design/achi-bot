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
 * /notes — Lista todas as notas do grupo.
 */
class NotesListCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'notes'; }
    public function getDescription(): string { return 'Guruhdagi barcha eslatmalarni ro\'yxatlaydi'; }
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

        $notes = $service->listAll($chatId);

        if (empty($notes)) {
            $telegram->reply($update, $lang->trans('Notes.no_notes'));
            return;
        }

        $list = '';
        foreach ($notes as $note) {
            $list .= "• <code>#{$note['name']}</code>\n";
        }

        $text = str_replace('\n', "\n", $lang->trans('Notes.notes_list', [':list' => trim($list)]));
        $telegram->reply($update, $text);
    }
}
