<?php
declare(strict_types=1);

namespace Modules\Flood\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Flood\Services\FloodService;

/**
 * /setfloodmode <action> — define a ação ao atingir o limite de flood.
 * Ações válidas: warn, mute, kick, ban, tban, tmute
 */
class SetfloodmodeCommand implements CommandInterface
{
    private const VALID_ACTIONS = ['warn', 'mute', 'kick', 'ban', 'tban', 'tmute'];

    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'setfloodmode'; }
    public function getDescription(): string    { return 'Flood limitiga yetganda bajariladigan amalni belgilaydi'; }
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
        $service  = $app->make(FloodService::class);
        $chatId   = $update->getChatId();
        $action   = strtolower(trim($update->getCommandArgs()));

        if (!in_array($action, self::VALID_ACTIONS, true)) {
            $telegram->reply($update, $lang->trans('Flood.floodmode_invalid'));
            return;
        }

        $service->setAction($chatId, $action);
        $telegram->reply($update, $lang->trans('Flood.floodmode_ok', [':action' => $action]));
    }
}
