<?php
declare(strict_types=1);

namespace Modules\Warn\Commands;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Helper\TargetResolver;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Permission;
use App\Core\Services\{LanguageService, TelegramService};
use App\Core\Update;
use Modules\Warn\Services\WarnService;

/**
 * /warns — Lista as advertências de um usuário.
 */
class WarnsCommand implements CommandInterface
{
    public function __construct(private readonly Application $app) {}

    public function getCommand(): string     { return 'warns'; }
    public function getDescription(): string { return 'Lista as advertências de um usuário'; }
    public function getPermission(): Permission { return Permission::User; }

    public function getMiddleware(): array
    {
        return [new GroupOnlyMiddleware($this->app)];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);
        $lang     = $app->make(LanguageService::class);
        $service  = $app->make(WarnService::class);
        $chatId   = $update->getChatId();
        $args     = $update->getCommandArgs();

        // Se não houver alvo, mostra as próprias advertências
        $target = TargetResolver::resolve($update, $args);
        if ($target === null) {
            $userId = $update->getUserId();
            $user   = $update->getFrom();
            $name   = $user ? htmlspecialchars($user['first_name'] ?? 'Você') : 'Você';
            $target = ['id' => $userId, 'name' => $name];
        }

        $count = $service->getWarnCount($chatId, $target['id']);
        $max   = $service->getMaxWarns($chatId);
        $warns = $service->getWarns($chatId, $target['id']);

        if ($count === 0) {
            $text = $lang->trans('Warn.warns_none', [':name' => $target['name']]);
            $telegram->reply($update, $text);
            return;
        }

        $list = '';
        foreach ($warns as $i => $warn) {
            $reason = htmlspecialchars($warn['reason'] ?? $lang->trans('Warn.no_reason'));
            $date   = date('d/m/Y', strtotime($warn['created_at'] ?? 'now'));
            $list  .= $lang->trans('Warn.warn_entry', [
                ':n'      => $i + 1,
                ':reason' => $reason,
                ':date'   => $date,
            ]) . "\n";
        }

        $text = $lang->trans('Warn.warns_list', [
            ':name'  => $target['name'],
            ':count' => $count,
            ':max'   => $max,
            ':list'  => trim($list),
        ]);

        $telegram->reply($update, str_replace('\n', "\n", $text));
    }
}
