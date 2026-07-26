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
 * /setrules <texto> — define as regras do grupo.
 * Também aceita reply: /setrules (usando o texto da mensagem citada).
 */
class SetrulesCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'setrules'; }
    public function getDescription(): string  { return 'Define as regras do grupo'; }
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
        $args     = trim($update->getCommandArgs());
        $reply    = $update->getReplyToMessage();

        $rulesText = '';
        if ($args !== '') {
            $rulesText = $args;
        } elseif ($reply !== null) {
            $rulesText = $reply['text'] ?? $reply['caption'] ?? '';
        }

        if ($rulesText === '') {
            $telegram->reply($update, $lang->trans('Rules.usage_set'));
            return;
        }

        $app->make(SettingsService::class)->set($chatId, 'Rules', 'text', $rulesText);
        $telegram->reply($update, $lang->trans('Rules.set_success'));
    }
}
