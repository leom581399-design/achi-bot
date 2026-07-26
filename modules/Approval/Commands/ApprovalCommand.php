<?php
declare(strict_types=1);

namespace Modules\Approval\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Approval\Services\ApprovalService;

/**
 * /approval on|off — ativa ou desativa o modo de aprovação manual para novos membros.
 */
class ApprovalCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'approval'; }
    public function getDescription(): string    { return 'Ativa ou desativa o modo de aprovação'; }
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
        $arg      = strtolower(trim($update->getCommandArgs()));

        if ($arg === '') {
            $key = $service->isEnabled($chatId) ? 'Approval.status_on' : 'Approval.status_off';
            $telegram->reply($update, $lang->trans($key));
            return;
        }

        if ($arg === 'on') {
            $service->setEnabled($chatId, true);
            $telegram->reply($update, $lang->trans('Approval.approval_on'));
            return;
        }

        if ($arg === 'off') {
            $service->setEnabled($chatId, false);
            $telegram->reply($update, $lang->trans('Approval.approval_off'));
            return;
        }

        $telegram->reply($update, $lang->trans('Approval.approval_invalid'));
    }
}
