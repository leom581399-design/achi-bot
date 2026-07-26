<?php
declare(strict_types=1);

namespace Modules\Warn\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Warn\Services\WarnService;

/**
 * /warn — Adverte um usuário. Ao atingir o limite, aplica a ação configurada.
 */
class WarnCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'warn'; }
    public function getDescription(): string { return 'Adverte um usuário'; }
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
        $service  = $app->make(WarnService::class);
        $chatId   = $update->getChatId();
        $args     = $update->getCommandArgs();

        $target = TargetResolver::resolve($update, $args);
        if ($target === null) {
            $telegram->reply($update, $lang->trans('Warn.no_target'));
            return;
        }

        $targetId = $target['id'];
        $name     = $target['name'];
        $reason   = trim($target['remaining_args']) ?: $lang->trans('Warn.no_reason');

        if ($telegram->isAdmin($chatId, $targetId)) {
            $telegram->reply($update, $lang->trans('Warn.cannot_warn_admin'));
            return;
        }

        $count    = $service->warn($chatId, $targetId, $update->getUserId(), $reason);
        $max      = $service->getMaxWarns($chatId);

        if ($count >= $max) {
            // Limite atingido — WarnService já aplicou a ação
            $text = $this->t($lang, 'Warn.warn_limit', [':name' => $name]);
        } else {
            $text = $this->t($lang, 'Warn.warned', [
                ':name'   => $name,
                ':count'  => $count,
                ':max'    => $max,
                ':reason' => $reason,
            ]);
        }

        $telegram->reply($update, $text);
    }

    private function t(LanguageService $lang, string $key, array $r = []): string
    {
        return str_replace('\n', "\n", $lang->trans($key, $r));
    }
}
