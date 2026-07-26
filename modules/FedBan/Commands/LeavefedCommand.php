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
 * /leavefed — Desvincula o grupo atual da federação.
 */
class LeavefedCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'leavefed'; }
    public function getDescription(): string   { return 'Desvincula o grupo da federação atual'; }
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

        $fed = $service->getFedForChat($chatId);
        if ($fed === null) {
            $telegram->reply($update, $lang->trans('FedBan.not_in_fed'));
            return;
        }

        $service->leaveFed($chatId);
        $telegram->reply($update, $lang->trans('FedBan.leavefed_done', [
            ':name' => htmlspecialchars($fed['name']),
        ]));
    }
}
