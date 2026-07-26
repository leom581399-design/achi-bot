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
 * /top — Exibe o ranking dos usuários mais ativos do grupo.
 */
class TopCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'top'; }
    public function getDescription(): string   { return 'Ranking de usuários mais ativos'; }
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

        $top = $service->topUsers($chatId, 10);

        if (empty($top)) {
            $telegram->reply($update, $lang->trans('Stats.top_empty'));
            return;
        }

        $lines = [];
        foreach ($top as $i => $row) {
            $pos   = $i + 1;
            $medal = match($pos) {
                1 => '🥇', 2 => '🥈', 3 => '🥉', default => "<b>{$pos}.</b>",
            };
            $lines[] = "{$medal} <code>{$row['user_id']}</code> — <b>" . number_format((int)$row['msg_count']) . "</b> msgs";
        }

        $telegram->reply($update, $lang->trans('Stats.top_header') . "\n\n" . implode("\n", $lines));
    }
}
