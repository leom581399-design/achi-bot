<?php
declare(strict_types=1);

namespace Modules\AntiRaid\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\AntiRaid\Services\RaidDetectorService;

/**
 * /antiraid on|off|N — configura a detecção de raids.
 *   /antiraid on     — ativa com configurações atuais
 *   /antiraid off    — desativa (e encerra modo raid ativo, se houver)
 *   /antiraid N      — ativa e define o limite de entradas para disparar
 *   /antiraid status — exibe configurações atuais
 */
class AntiRaidCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'antiraid'; }
    public function getDescription(): string    { return 'Anti-reyd sozlamalarini boshqaradi'; }
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
        $service  = $app->make(RaidDetectorService::class);
        $chatId   = $update->getChatId();
        $arg      = strtolower(trim($update->getCommandArgs()));

        if ($arg === '' || $arg === 'status') {
            if ($service->isEnabled($chatId)) {
                $text = $lang->trans('AntiRaid.status_on', [
                    ':threshold' => $service->getThreshold($chatId),
                    ':window'    => $service->getWindow($chatId),
                    ':action'    => $service->getAction($chatId),
                ]);
                $text = str_replace('\n', "\n", $text);
            } else {
                $text = $lang->trans('AntiRaid.status_off');
            }
            if ($service->isRaidActive($chatId)) {
                $remaining = $service->getRemainingSeconds($chatId);
                $text .= "\n🚨 <b>Modo raid ativo.</b> Expira em: {$remaining}s";
            }
            $telegram->reply($update, $text);
            return;
        }

        if ($arg === 'off') {
            $service->setEnabled($chatId, false);
            $service->deactivateRaid($chatId);
            $telegram->reply($update, $lang->trans('AntiRaid.antiraid_off_cmd'));
            return;
        }

        if ($arg === 'on') {
            $service->setEnabled($chatId, true);
            $text = $lang->trans('AntiRaid.antiraid_on', [
                ':n'      => $service->getThreshold($chatId),
                ':window' => $service->getWindow($chatId),
            ]);
            $telegram->reply($update, $text);
            return;
        }

        if (ctype_digit($arg)) {
            $n = (int)$arg;
            if ($n < 2) {
                $telegram->reply($update, $lang->trans('AntiRaid.antiraid_invalid'));
                return;
            }
            $service->setEnabled($chatId, true);
            $service->setThreshold($chatId, $n);
            $text = $lang->trans('AntiRaid.antiraid_on', [
                ':n'      => $n,
                ':window' => $service->getWindow($chatId),
            ]);
            $telegram->reply($update, $text);
            return;
        }

        $telegram->reply($update, $lang->trans('AntiRaid.antiraid_invalid'));
    }
}
