<?php
declare(strict_types=1);

namespace Modules\Filters\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Filters\Services\FilterService;

/**
 * /filters — lista todos os filtros ativos no grupo.
 */
class FiltersCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'filters'; }
    public function getDescription(): string  { return 'Lista os filtros ativos'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $chatId   = $update->getChatId();

        $filters = $app->make(FilterService::class)->listAll($chatId);

        if (empty($filters)) {
            $telegram->reply($update, $lang->trans('Filters.no_filters'));
            return;
        }

        $list = implode("\n", array_map(
            fn($f) => "• <code>" . htmlspecialchars($f['keyword']) . "</code>",
            $filters
        ));

        $telegram->reply($update, $lang->trans('Filters.list', [':list' => $list]));
    }
}
