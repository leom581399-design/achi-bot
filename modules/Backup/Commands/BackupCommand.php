<?php
declare(strict_types=1);

namespace Modules\Backup\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\{GroupOnlyMiddleware, PermissionMiddleware};
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Backup\Services\BackupService;

/**
 * /backup — Exporta toda a configuração do grupo em um arquivo JSON.
 *
 * Uso: /backup
 * Permissão: Administrator+
 */
class BackupCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'backup'; }
    public function getDescription(): string   { return 'Guruh sozlamalarini JSON formatida eksport qiladi'; }
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
        $service  = $app->make(BackupService::class);
        $chatId   = $update->getChatId();

        // Notifica que está gerando
        $telegram->reply($update, $lang->trans('Backup.generating'));

        try {
            $data     = $service->export($chatId);
            $json     = $service->toJson($data);
            $filename = 'backup_' . abs($chatId) . '_' . date('Ymd_His') . '.json';

            // Envia o arquivo como documento via TelegramClient
            $client  = $app->make(TelegramClient::class);
            $caption = $lang->trans('Backup.caption', [
                ':date'     => date('d/m/Y H:i'),
                ':notes'    => count($data['notes']),
                ':filters'  => count($data['filters']),
                ':warns'    => count($data['warns']),
                ':settings' => count($data['settings']),
            ]);

            $client->sendDocumentContent($chatId, $json, $filename, $caption);
        } catch (\Throwable $e) {
            $telegram->reply($update, $lang->trans('Backup.error', [':msg' => $e->getMessage()]));
        }
    }
}
