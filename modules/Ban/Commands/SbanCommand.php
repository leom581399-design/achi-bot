<?php
declare(strict_types=1);

namespace Modules\Ban\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Ban\Services\BanService;

/**
 * /sban — Ban silencioso: bane sem enviar notificação no grupo.
 * Deleta a mensagem do comando antes de banir.
 */
class SbanCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'sban'; }
    public function getDescription(): string { return 'Sokin (bildirishnomasiz) banlaydi'; }
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
        $client   = $app->make(TelegramClient::class);
        $chatId   = $update->getChatId();
        $args     = $update->getCommandArgs();

        $target = TargetResolver::resolve($update, $args);
        if ($target === null) {
            $telegram->reply($update, $this->t($lang, 'Ban.no_target'));
            return;
        }

        $targetId = $target['id'];
        $reason   = trim($target['remaining_args']) ?: null;

        if ($telegram->isAdmin($chatId, $targetId)) {
            $telegram->reply($update, $this->t($lang, 'Ban.cannot_ban_admin'));
            return;
        }

        // Deleta a mensagem de comando para manter o silêncio
        try {
            $client->deleteMessage($chatId, $update->getMessageId());
        } catch (\Throwable) {
            // Ignora falha ao deletar (sem permissão)
        }

        try {
            $app->make(BanService::class)->ban(
                $chatId,
                $targetId,
                $update->getUserId(),
                $reason
            );
            // Sem mensagem de confirmação — é silencioso
        } catch (\Throwable) {
            // Silencioso — não notifica falha publicamente
        }
    }

    private function t(LanguageService $lang, string $key, array $r = []): string
    {
        return str_replace('\n', "\n", $lang->trans($key, $r));
    }
}
