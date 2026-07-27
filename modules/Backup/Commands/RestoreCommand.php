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
 * /restore — Restaura as configurações de um grupo a partir de um arquivo JSON.
 *
 * Uso: Responda a uma mensagem com o arquivo .json e envie /restore
 * Permissão: Administrator+
 */
class RestoreCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string        { return 'restore'; }
    public function getDescription(): string   { return 'JSON zaxira nusxadan guruh sozlamalarini qayta tiklaydi'; }
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
        $client   = $app->make(TelegramClient::class);
        $chatId   = $update->getChatId();

        // Encontrar o documento — pode estar na mensagem atual ou na que foi respondida
        $document = $this->findDocument($update);

        if ($document === null) {
            $telegram->reply($update, $lang->trans('Backup.restore_no_file'));
            return;
        }

        // Validar extensão/mime grosseiramente
        $name = $document['file_name'] ?? '';
        if (!str_ends_with(strtolower($name), '.json')) {
            $telegram->reply($update, $lang->trans('Backup.restore_invalid_file'));
            return;
        }

        $telegram->reply($update, $lang->trans('Backup.restoring'));

        try {
            // Baixar o arquivo via Telegram
            $fileId   = $document['file_id'];
            $fileInfo = $client->getFile($fileId);
            $filePath = $fileInfo['file_path'] ?? null;

            if (!$filePath) {
                throw new \RuntimeException("Faylni Telegram'dan olib bo'lmadi.");
            }

            $json = $client->downloadFile($filePath);

            if ($json === false || $json === '') {
                throw new \RuntimeException("Fayl bo'sh yoki o'qib bo'lmaydi.");
            }

            $stats = $service->import($chatId, $json);

            $telegram->reply($update, $lang->trans('Backup.restore_done', [
                ':settings' => $stats['settings'],
                ':notes'    => $stats['notes'],
                ':filters'  => $stats['filters'],
                ':warns'    => $stats['warns'],
                ':bans'     => $stats['bans'],
                ':mutes'    => $stats['mutes'],
                ':rules'    => $stats['rules'],
            ]));
        } catch (\JsonException $e) {
            $telegram->reply($update, $lang->trans('Backup.restore_json_error'));
        } catch (\InvalidArgumentException $e) {
            $telegram->reply($update, $lang->trans('Backup.restore_invalid', [':msg' => $e->getMessage()]));
        } catch (\Throwable $e) {
            $telegram->reply($update, $lang->trans('Backup.error', [':msg' => $e->getMessage()]));
        }
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    /**
     * Procura um document na mensagem atual ou na mensagem respondida.
     */
    private function findDocument(Update $update): ?array
    {
        // Update::getRaw() mavjud emas — bevosita $update->data (public
        // readonly) ishlatiladi, u xuddi shu xom Telegram payloadini
        // saqlaydi.
        $raw = $update->data;

        // Mensagem atual
        $doc = $raw['message']['document'] ?? null;
        if ($doc !== null) return $doc;

        // Mensagem que foi respondida
        $doc = $raw['message']['reply_to_message']['document'] ?? null;
        if ($doc !== null) return $doc;

        return null;
    }
}
