<?php
declare(strict_types=1);

namespace Modules\Mute\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Mute\Services\MuteService;

/**
 * /mute — Silencia um usuário permanentemente no grupo.
 */
class MuteCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'mute'; }
    public function getDescription(): string { return 'Silencia um usuário no grupo'; }
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
            $telegram->reply($update, $lang->trans('Mute.no_target'));
            return;
        }

        $targetId = $target['id'];
        $name     = $target['name'];
        $reason   = trim($target['remaining_args']) ?: $lang->trans('Mute.no_reason');

        if ($telegram->isAdmin($chatId, $targetId)) {
            $telegram->reply($update, $lang->trans('Mute.cannot_mute_admin'));
            return;
        }

        try {
            $app->make(MuteService::class)->mute(
                $chatId,
                $targetId,
                $update->getUserId(),
                $reason
            );

            $text = $this->t($lang, 'Mute.muted', [':name' => $name, ':reason' => $reason]);
            $telegram->reply($update, $text);
        } catch (\Throwable) {
            $telegram->reply($update, $lang->trans('Mute.mute_failed'));
        }
    }

    private function t(LanguageService $lang, string $key, array $r = []): string
    {
        return str_replace('\n', "\n", $lang->trans($key, $r));
    }
}
