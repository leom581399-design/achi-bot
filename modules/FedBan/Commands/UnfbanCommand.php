<?php
declare(strict_types=1);

namespace Modules\FedBan\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\FedBan\Services\FedService;

/**
 * /unfban [reply|id] — Remove o fedban de um usuário.
 */
class UnfbanCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'unfban'; }
    public function getDescription(): string   { return 'Foydalanuvchini federatsiya banidan chiqaradi'; }
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
        $args     = $update->getCommandArgs();

        $fed = $service->getFedForChat($chatId);
        if ($fed === null) {
            $telegram->reply($update, $lang->trans('FedBan.not_in_fed'));
            return;
        }

        $target = TargetResolver::resolve($update, $args);
        if ($target === null) {
            $telegram->reply($update, $lang->trans('FedBan.no_target'));
            return;
        }

        $userId = $target['id'];
        $name   = $target['name'];
        $fedId  = $fed['fed_id'];

        if ($service->isFbanned($fedId, $userId) === null) {
            $telegram->reply($update, $lang->trans('FedBan.not_fbanned', [':name' => $name]));
            return;
        }

        $service->unfban($fedId, $userId);
        $telegram->reply($update, $lang->trans('FedBan.unfban_done', [
            ':name' => $name,
            ':fed'  => htmlspecialchars($fed['name']),
        ]));
    }
}
