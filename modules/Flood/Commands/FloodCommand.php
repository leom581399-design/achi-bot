<?php
declare(strict_types=1);

namespace Modules\Flood\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Flood\Services\FloodService;

/**
 * /flood — exibe as configurações atuais de anti-flood do grupo.
 */
class FloodCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'flood'; }
    public function getDescription(): string    { return 'Exibe as configurações de anti-flood'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $service  = $app->make(FloodService::class);
        $chatId   = $update->getChatId();

        $limit = $service->getLimit($chatId);
        if ($limit === 0) {
            $telegram->reply($update, $lang->trans('Flood.flood_status_off'));
        } else {
            $text = $lang->trans('Flood.flood_status_on', [
                ':limit'  => $limit,
                ':window' => $service->getWindow($chatId),
                ':action' => $service->getAction($chatId),
            ]);
            $telegram->reply($update, str_replace('\n', "\n", $text));
        }
    }
}
