<?php
declare(strict_types=1);

namespace Modules\AntiSpam\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\AntiSpam\Services\SpamDetector;

/**
 * /antispam on|off — ativa ou desativa o anti-spam no grupo.
 */
class AntispamCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'antispam'; }
    public function getDescription(): string    { return 'Anti-spamni yoqadi/o\'chiradi'; }
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
        $detector = $app->make(SpamDetector::class);
        $chatId   = $update->getChatId();
        $arg      = strtolower(trim($update->getCommandArgs()));

        if ($arg === '') {
            $key  = $detector->isEnabled($chatId) ? 'AntiSpam.status_on' : 'AntiSpam.status_off';
            $telegram->reply($update, $lang->trans($key));
            return;
        }

        if ($arg === 'on') {
            $detector->setEnabled($chatId, true);
            $telegram->reply($update, $lang->trans('AntiSpam.antispam_on'));
            return;
        }

        if ($arg === 'off') {
            $detector->setEnabled($chatId, false);
            $telegram->reply($update, $lang->trans('AntiSpam.antispam_off'));
            return;
        }

        $telegram->reply($update, $lang->trans('AntiSpam.antispam_invalid'));
    }
}
