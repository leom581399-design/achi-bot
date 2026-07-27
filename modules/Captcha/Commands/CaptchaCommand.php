<?php
declare(strict_types=1);

namespace Modules\Captcha\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Captcha\Services\CaptchaService;

/**
 * /captcha on|off|button|math|text — configura o captcha do grupo.
 */
class CaptchaCommand implements CommandInterface
{
    private const TYPES = ['button', 'math', 'text'];

    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'captcha'; }
    public function getDescription(): string    { return 'Yangi a\'zolar uchun captcha sozlaydi'; }
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
        $service  = $app->make(CaptchaService::class);
        $chatId   = $update->getChatId();
        $arg      = strtolower(trim($update->getCommandArgs()));

        if ($arg === '') {
            // Exibe status
            if ($service->isEnabled($chatId)) {
                $text = $lang->trans('Captcha.status_on', [
                    ':type'    => $service->getType($chatId),
                    ':timeout' => $service->getTimeout($chatId),
                ]);
            } else {
                $text = $lang->trans('Captcha.status_off');
            }
            $telegram->reply($update, $text);
            return;
        }

        if ($arg === 'off') {
            $service->setEnabled($chatId, false);
            $telegram->reply($update, $lang->trans('Captcha.captcha_off'));
            return;
        }

        if ($arg === 'on') {
            $service->setEnabled($chatId, true);
            $text = $lang->trans('Captcha.captcha_on', [':type' => $service->getType($chatId)]);
            $telegram->reply($update, $text);
            return;
        }

        if (in_array($arg, self::TYPES, true)) {
            $service->setEnabled($chatId, true);
            $service->setType($chatId, $arg);
            $text = $lang->trans('Captcha.captcha_on', [':type' => $arg]);
            $telegram->reply($update, $text);
            return;
        }

        $telegram->reply($update, $lang->trans('Captcha.captcha_invalid'));
    }
}
