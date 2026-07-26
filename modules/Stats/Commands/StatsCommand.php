<?php
declare(strict_types=1);

namespace Modules\Stats\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Stats\Services\StatsService;

/**
 * /stats — Exibe estatísticas gerais do grupo.
 */
class StatsCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'stats'; }
    public function getDescription(): string   { return 'Estatísticas do grupo'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $service  = $app->make(StatsService::class);
        $chatId   = $update->getChatId();

        $stats = $service->groupStats($chatId);

        $telegram->reply($update, $lang->trans('Stats.group_stats', [
            ':messages' => number_format($stats['total_messages']),
            ':users'    => number_format($stats['total_users']),
        ]));
    }
}
