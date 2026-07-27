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
 * /fban [reply|id] [motivo] — Bane um usuário em toda a federação.
 */
class FbanCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'fban'; }
    public function getDescription(): string   { return 'Foydalanuvchini butun federatsiyada banlaydi'; }
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
        $reason = trim($target['remaining_args']) ?: $lang->trans('FedBan.no_reason');
        $fedId  = $fed['fed_id'];

        if ($service->isFbanned($fedId, $userId) !== null) {
            $telegram->reply($update, $lang->trans('FedBan.already_fbanned', [':name' => $name]));
            return;
        }

        $service->fban($fedId, $userId, $update->getUserId(), $reason);

        $chats = count($service->listChats($fedId));
        $telegram->reply($update, $lang->trans('FedBan.fban_done', [
            ':name'   => $name,
            ':fed'    => htmlspecialchars($fed['name']),
            ':reason' => htmlspecialchars($reason),
            ':chats'  => $chats,
        ]));
    }
}
