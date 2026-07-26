<?php
declare(strict_types=1);

namespace Modules\Reports\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * /report — notifica todos os admins sobre uma mensagem (deve ser usado em reply).
 */
class ReportCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string      { return 'report'; }
    public function getDescription(): string  { return 'Reporta uma mensagem para os admins'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $client   = $app->make(TelegramClient::class);
        $chatId   = $update->getChatId();

        $reply = $update->getReplyToMessage();
        if ($reply === null) {
            $telegram->reply($update, $lang->trans('Reports.need_reply'));
            return;
        }

        // Não permite reportar bots ou admins
        $reportedUser = $reply['from'] ?? null;
        if ($reportedUser === null) {
            $telegram->reply($update, $lang->trans('Reports.error'));
            return;
        }

        if ($reportedUser['is_bot'] ?? false) {
            $telegram->reply($update, $lang->trans('Reports.cannot_report_bot'));
            return;
        }

        if ($telegram->isAdmin($chatId, $reportedUser['id'])) {
            $telegram->reply($update, $lang->trans('Reports.cannot_report_admin'));
            return;
        }

        // Busca admins do grupo
        try {
            $admins = $client->getChatAdministrators($chatId);
        } catch (\Throwable) {
            $telegram->reply($update, $lang->trans('Reports.error'));
            return;
        }

        $reporter     = $update->getUser();
        $reporterName = $telegram->formatUser($reporter ?? ['first_name' => 'Usuário']);
        $reportedName = $telegram->formatUser($reportedUser);

        // Obtém link para a mensagem reportada (apenas em supergrupos)
        $messageLink = '';
        $chat        = null;
        try {
            $chat = $client->getChat($chatId);
            if (isset($chat['username'])) {
                $messageLink = "\n🔗 <a href=\"https://t.me/{$chat['username']}/{$reply['message_id']}\">Ver mensagem</a>";
            }
        } catch (\Throwable) {}

        $reason = trim($update->getCommandArgs());
        $reasonText = $reason !== '' ? "\n📝 Motivo: <i>" . htmlspecialchars($reason) . '</i>' : '';

        $msgToAdmins = $lang->trans('Reports.report_message', [
            ':reporter' => $reporterName,
            ':reported' => $reportedName,
            ':reason'   => $reasonText,
            ':link'     => $messageLink,
        ]);

        // Notifica cada admin via DM (ignora erros de privacidade)
        $notified = 0;
        foreach ($admins as $admin) {
            if ($admin['user']['is_bot'] ?? false) continue;
            try {
                $client->sendMessage($admin['user']['id'], $msgToAdmins);
                $notified++;
            } catch (\Throwable) {}
        }

        if ($notified === 0) {
            $telegram->reply($update, $lang->trans('Reports.no_admins_notified'));
        } else {
            $telegram->reply($update, $lang->trans('Reports.reported', [':count' => $notified]));
        }
    }
}
