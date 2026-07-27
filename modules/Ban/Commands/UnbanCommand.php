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
 * /unban — Remove o ban de um usuário.
 * Uso: /unban <id>  (normalmente via ID pois o usuário não está mais no grupo)
 */
class UnbanCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'unban'; }
    public function getDescription(): string { return 'Foydalanuvchidan banni olib tashlaydi'; }
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

        try {
            $app->make(BanService::class)->unban(
                $chatId,
                $target['id'],
                $update->getUserId()
            );

            $text = $this->t($lang, 'Ban.unbanned', [':name' => $target['name']]);
            $telegram->reply($update, $text);
        } catch (\Throwable) {
            $telegram->reply($update, $this->t($lang, 'Ban.unban_failed'));
        }
    }

    private function t(LanguageService $lang, string $key, array $r = []): string
    {
        return str_replace('\n', "\n", $lang->trans($key, $r));
    }
}
