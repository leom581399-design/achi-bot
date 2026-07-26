<?php
declare(strict_types=1);

namespace Modules\Ban\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Ban\Services\BanService;

/**
 * /banme — O usuário se auto-bane do grupo.
 */
class BanmeCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'banme'; }
    public function getDescription(): string { return 'Se auto-bane do grupo'; }
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
        $userId   = $update->getUserId();
        $user     = $update->getFrom();
        $name     = $user ? htmlspecialchars($user['first_name'] ?? 'Usuário') : 'Usuário';

        // Não permite auto-ban de admins
        if ($telegram->isAdmin($chatId, $userId)) {
            $telegram->reply($update, $this->t($lang, 'Ban.cannot_ban_admin'));
            return;
        }

        try {
            $text = $this->t($lang, 'Ban.banme_bye', [':name' => $name]);
            $telegram->reply($update, $text);

            $app->make(BanService::class)->ban(
                $chatId,
                $userId,
                $userId,
                'Self-ban (/banme)'
            );
        } catch (\Throwable) {
            $telegram->reply($update, $this->t($lang, 'Ban.ban_failed'));
        }
    }

    private function t(LanguageService $lang, string $key, array $r = []): string
    {
        return str_replace('\n', "\n", $lang->trans($key, $r));
    }
}
