<?php
declare(strict_types=1);

namespace Modules\Welcome\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Welcome\Services\WelcomeService;

/**
 * /cleanwelcome on|off — apaga a welcome anterior quando um novo membro entra.
 */
class CleanwelcomeCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'cleanwelcome'; }
    public function getDescription(): string  { return 'Yangi a\'zo qo\'shilganda oldingi xush kelibsiz xabarini o\'chiradi'; }
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
        $service  = $app->make(WelcomeService::class);
        $chatId   = $update->getChatId();
        $args     = strtolower(trim($update->getCommandArgs()));

        match($args) {
            'on'  => (function() use ($service, $chatId, $telegram, $update, $lang) {
                $service->setCleanwelcome($chatId, true);
                $telegram->reply($update, $lang->trans('Welcome.cleanwelcome_on'));
            })(),
            'off' => (function() use ($service, $chatId, $telegram, $update, $lang) {
                $service->setCleanwelcome($chatId, false);
                $telegram->reply($update, $lang->trans('Welcome.cleanwelcome_off'));
            })(),
            default => $telegram->reply($update, $lang->trans('Welcome.cleanwelcome_usage')),
        };
    }
}
