<?php
declare(strict_types=1);

namespace Modules\Welcome\Events;

use App\Core\Application;
use App\Core\Update;
use Modules\Welcome\Services\WelcomeService;

/**
 * Ouve user.joined e envia a mensagem de boas-vindas.
 */
class JoinListener
{
    public function __construct(private readonly Application $app) {}

    public function __invoke(mixed $data): void
    {
        $this->handle(is_array($data) ? $data : []);
    }

    public function handle(array $data): void
    {
        /** @var Update $update */
        $update = $data['update'] ?? null;
        $user   = $data['member'] ?? $data['user'] ?? null;

        if ($update === null || $user === null) return;

        // Ignora bots
        if ($user['is_bot'] ?? false) return;

        $chatId = $update->getChatId();
        if ($chatId === null) return;

        $this->app->make(WelcomeService::class)->sendWelcome($chatId, $user, $update);
    }
}
