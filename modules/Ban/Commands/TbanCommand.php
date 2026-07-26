<?php
declare(strict_types=1);

namespace Modules\Ban\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\{DurationParser, TargetResolver};
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Ban\Services\BanService;

/**
 * /tban — Bane um usuário temporariamente.
 * Uso: responder com /tban <duração> [motivo]  ou  /tban <id> <duração> [motivo]
 * Exemplos: /tban 1d spam   /tban 2h30m flood
 */
class TbanCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'tban'; }
    public function getDescription(): string { return 'Bane um usuário temporariamente (ex: /tban 1d motivo)'; }
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

        // Extrai duração dos args restantes
        [$seconds, $remaining] = DurationParser::parse($target['remaining_args']);
        $reason    = trim($remaining) ?: $this->t($lang, 'Ban.no_reason');
        $untilDate = $seconds > 0 ? time() + $seconds : null;
        $duration  = DurationParser::format($seconds);

        if ($telegram->isAdmin($chatId, $targetId)) {
            $telegram->reply($update, $this->t($lang, 'Ban.cannot_ban_admin'));
            return;
        }

        try {
            $app->make(BanService::class)->ban(
                $chatId,
                $targetId,
                $update->getUserId(),
                $reason,
                $untilDate
            );

            if ($untilDate !== null) {
                $text = $this->t($lang, 'Ban.banned_temp', [
                    ':name'     => $name,
                    ':duration' => $duration,
                    ':reason'   => $reason,
                ]);
            } else {
                $text = $this->t($lang, 'Ban.banned', [':name' => $name, ':reason' => $reason]);
            }

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
