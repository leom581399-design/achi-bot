<?php
declare(strict_types=1);

namespace Modules\Rules\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, SettingsService, TelegramService};
use App\Core\Update;

/**
 * /clearrules — remove as regras do grupo.
 */
class ClearrulesCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'clearrules'; }
    public function getDescription(): string  { return 'Guruh qoidalarini o\'chiradi'; }
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

        $app->make(SettingsService::class)->forget($chatId, 'Rules', 'text');
        $telegram->reply($update, $lang->trans('Rules.cleared'));
    }
}
