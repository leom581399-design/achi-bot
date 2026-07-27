<?php
declare(strict_types=1);

namespace Modules\Ban\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Ban\Services\BanService;

/**
 * /ban — Bane um usuário permanentemente do grupo.
 * Uso: responder a uma mensagem ou /ban <id> [motivo]
 */
class BanCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'ban'; }
    public function getDescription(): string { return 'Foydalanuvchini abadiy banlaydi'; }
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
        $args     = $update->getCommandArgs();

        $target = TargetResolver::resolve($update, $args);
        if ($target === null) {
            $telegram->reply($update, $this->t($lang, 'Ban.no_target'));
            return;
        }

        $targetId = $target['id'];
        $name     = $target['name'];
        $reason   = trim($target['remaining_args']) ?: $this->t($lang, 'Ban.no_reason');

        // Não bane admins
        if ($telegram->isAdmin($chatId, $targetId)) {
            $telegram->reply($update, $this->t($lang, 'Ban.cannot_ban_admin'));
            return;
        }

        try {
            $app->make(BanService::class)->ban(
                $chatId,
                $targetId,
                $update->getUserId(),
                $reason
            );

            $text = $this->t($lang, 'Ban.banned', [':name' => $name, ':reason' => $reason]);
            $telegram->reply($update, $text);
        } catch (\Throwable) {
            $telegram->reply($update, $this->t($lang, 'Ban.ban_failed'));
        }
    }

    private function t(LanguageService $lang, string $key, array $r = []): string
    {
        return str_replace('\n', "\n", $lang->trans($key, $r));
    }
}
