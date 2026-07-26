<?php
declare(strict_types=1);

namespace Modules\FedBan\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\FedBan\Services\FedService;

/**
 * /fedinfo — Exibe informações sobre a federação do grupo atual.
 */
class FedInfoCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'fedinfo'; }
    public function getDescription(): string   { return 'Informações da federação do grupo'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
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

        $fedId  = $fed['fed_id'];
        $chats  = count($service->listChats($fedId));
        $bans   = $service->countFbans($fedId);

        $telegram->reply($update, $lang->trans('FedBan.fedinfo', [
            ':name'    => htmlspecialchars($fed['name']),
            ':fed_id'  => $fed['fed_id'],
            ':owner'   => $fed['owner_id'],
            ':chats'   => $chats,
            ':bans'    => $bans,
            ':created' => date('d/m/Y', strtotime($fed['created_at'])),
        ]));
    }
}
