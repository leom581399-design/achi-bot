<?php
declare(strict_types=1);

namespace Modules\FedBan\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\FedBan\Services\FedService;

/**
 * /joinfed <fed_id> — Vincula o grupo atual a uma federação.
 */
class JoinfedCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'joinfed'; }
    public function getDescription(): string   { return 'Guruhni federatsiyaga bog\'laydi'; }
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
        $service  = $app->make(FedService::class);
        $chatId   = $update->getChatId();
        $userId   = $update->getUserId();
        $fedId    = trim($update->getCommandArgs());

        if ($fedId === '') {
            $telegram->reply($update, $lang->trans('FedBan.joinfed_usage'));
            return;
        }

        // Verificar se o chat já pertence a uma fed
        if ($service->getFedForChat($chatId) !== null) {
            $telegram->reply($update, $lang->trans('FedBan.already_in_fed'));
            return;
        }

        $fed = $service->findById($fedId);
        if ($fed === null) {
            $telegram->reply($update, $lang->trans('FedBan.fed_not_found'));
            return;
        }

        // Apenas o dono da federação pode adicionar grupos
        if ((int)$fed['owner_id'] !== $userId) {
            $telegram->reply($update, $lang->trans('FedBan.not_fed_owner'));
            return;
        }

        $service->joinFed($fedId, $chatId, $userId);
        $telegram->reply($update, $lang->trans('FedBan.joinfed_done', [
            ':name' => htmlspecialchars($fed['name']),
        ]));
    }
}
