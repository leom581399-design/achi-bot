<?php
declare(strict_types=1);

namespace Modules\Mute\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\{DurationParser, TargetResolver};
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Mute\Services\MuteService;

/**
 * /tmute — Silencia um usuário temporariamente.
 * Uso: responder com /tmute <duração> [motivo]  ou  /tmute <id> <duração> [motivo]
 */
class TmuteCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'tmute'; }
    public function getDescription(): string { return 'Silencia temporariamente (ex: /tmute 1h motivo)'; }
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

        [$seconds, $remaining] = DurationParser::parse($target['remaining_args']);
        $reason    = trim($remaining) ?: $lang->trans('Mute.no_reason');
        $untilDate = $seconds > 0 ? time() + $seconds : null;
        $duration  = DurationParser::format($seconds);

        if ($telegram->isAdmin($chatId, $targetId)) {
            $telegram->reply($update, $lang->trans('Mute.cannot_mute_admin'));
            return;
        }

        try {
            $app->make(MuteService::class)->mute(
                $chatId,
                $targetId,
                $update->getUserId(),
                $reason,
                $untilDate
            );

            if ($untilDate !== null) {
                $text = $this->t($lang, 'Mute.muted_temp', [
                    ':name'     => $name,
                    ':duration' => $duration,
                    ':reason'   => $reason,
                ]);
            } else {
                $text = $this->t($lang, 'Mute.muted', [':name' => $name, ':reason' => $reason]);
            }

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
