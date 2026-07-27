<?php
declare(strict_types=1);

namespace Modules\Approval\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Approval\Services\ApprovalService;

/**
 * /deny [reply|@user|ID] — nega um membro (bane do grupo).
 */
class DenyCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'deny'; }
    public function getDescription(): string    { return 'Tasdiqlanishini kutayotgan a\'zoni rad etib chiqaradi'; }
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
        $service  = $app->make(ApprovalService::class);
        $chatId   = $update->getChatId();
        $args     = $update->getCommandArgs();

        $target = TargetResolver::resolve($update, $args);
        if ($target === null) {
            $telegram->reply($update, $lang->trans('Approval.no_target'));
            return;
        }

        $targetId = $target['id'];
        $name     = $target['name'];

        if ($service->deny($chatId, $targetId)) {
            $telegram->reply($update, $lang->trans('Approval.denied', [':name' => $name]));
        } else {
            $telegram->reply($update, $lang->trans('Approval.deny_failed'));
        }
    }
}
