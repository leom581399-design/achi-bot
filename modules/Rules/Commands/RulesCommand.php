<?php
declare(strict_types=1);

namespace Modules\Rules\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, SettingsService, TelegramService};
use App\Core\Update;

/**
 * /rules — exibe as regras do grupo.
 */
class RulesCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'rules'; }
    public function getDescription(): string  { return 'Exibe as regras do grupo'; }
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

        $rulesText = $app->make(SettingsService::class)->get($chatId, 'Rules', 'text');

        if ($rulesText === null || $rulesText === '') {
            $telegram->reply($update, $lang->trans('Rules.no_rules'));
            return;
        }

        $telegram->reply($update, $lang->trans('Rules.rules', [':rules' => $rulesText]));
    }
}
