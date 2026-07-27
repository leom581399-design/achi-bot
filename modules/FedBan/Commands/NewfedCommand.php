<?php
declare(strict_types=1);

namespace Modules\FedBan\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\PrivateOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\FedBan\Services\FedService;

/**
 * /newfed <nome> — Cria uma nova federação. Uso em privado.
 */
class NewfedCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'newfed'; }
    public function getDescription(): string   { return 'Yangi federatsiya yaratadi'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new PrivateOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $service  = $app->make(FedService::class);
        $userId   = $update->getUserId();
        $name     = trim($update->getCommandArgs());

        if ($name === '') {
            $telegram->reply($update, $lang->trans('FedBan.newfed_usage'));
            return;
        }

        if ($service->findByOwner($userId) !== null) {
            $telegram->reply($update, $lang->trans('FedBan.already_owner'));
            return;
        }

        $fed = $service->create($name, $userId);
        $telegram->reply($update, $lang->trans('FedBan.newfed_done', [
            ':name'   => htmlspecialchars($fed['name']),
            ':fed_id' => $fed['fed_id'],
        ]));
    }
}
