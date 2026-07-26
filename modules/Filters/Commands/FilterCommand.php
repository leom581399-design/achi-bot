<?php
declare(strict_types=1);

namespace Modules\Filters\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Filters\Services\FilterService;

/**
 * /filter <palavra> <resposta> — cria um filtro automático.
 * Também funciona respondendo a uma mensagem: /filter <palavra> (usa texto da mensagem como resposta).
 */
class FilterCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'filter'; }
    public function getDescription(): string  { return 'Cria um filtro automático de palavra-chave'; }
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
        $chatId   = $update->getChatId();
        $args     = $update->getCommandArgs();

        $parts   = explode(' ', $args, 2);
        $keyword = trim($parts[0] ?? '');
        $reply   = $update->getReplyToMessage();

        if ($keyword === '') {
            $telegram->reply($update, $lang->trans('Filters.usage'));
            return;
        }

        // Resposta pode vir do argumento ou da mensagem citada
        $response = '';
        if (isset($parts[1]) && trim($parts[1]) !== '') {
            $response = trim($parts[1]);
        } elseif ($reply !== null) {
            $response = $reply['text'] ?? $reply['caption'] ?? '';
        }

        if ($response === '') {
            $telegram->reply($update, $lang->trans('Filters.usage'));
            return;
        }

        $app->make(FilterService::class)->save($chatId, $keyword, $response, $update->getUserId());
        $telegram->reply($update, $lang->trans('Filters.saved', [':keyword' => htmlspecialchars($keyword)]));
    }
}
