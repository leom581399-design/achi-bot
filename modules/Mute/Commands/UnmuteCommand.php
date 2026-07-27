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
 * /unmute — Remove o silêncio de um usuário.
 */
class UnmuteCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'unmute'; }
    public function getDescription(): string { return 'Foydalanuvchining ovozini qaytaradi'; }
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

        try {
            $app->make(MuteService::class)->unmute(
                $chatId,
                $target['id'],
                $update->getUserId()
            );

            $text = $lang->trans('Mute.unmuted', [':name' => $target['name']]);
            $telegram->reply($update, $text);
        } catch (\Throwable) {
            $telegram->reply($update, $lang->trans('Mute.unmute_failed'));
        }
    }
}
