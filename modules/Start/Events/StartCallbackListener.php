<?php
declare(strict_types=1);

namespace Modules\Start\Events;

use App\Core\Application;
use App\Core\CommandRegistry;
use App\Core\Services\TelegramService;
use App\Core\Telegram\TelegramClient;
use App\Core\Update;

/**
 * "callback.received" hodisasiga obuna - /start buyrug'idagi "📋
 * Buyruqlar ro'yxati" inline tugmasi bosilganda /help buyrug'ining
 * xuddi shu natijasini (buyruqlar ro'yxatini) ko'rsatadi.
 *
 * callback_data: "start_help"
 */
class StartCallbackListener
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
        if ($update === null || $update->callbackQuery === null) return;

        $cb     = $update->callbackQuery;
        $cbData = $cb['data'] ?? '';
        if ($cbData !== 'start_help') return;

        $cbQueryId = $cb['id'] ?? '';
        $client    = $this->app->make(TelegramClient::class);

        try {
            $client->answerCallbackQuery($cbQueryId);
        } catch (\Throwable) {}

        $registry = $this->app->make(CommandRegistry::class);
        $commands = $registry->all();

        $text = "<b>🤖 ACHI BOT — mavjud buyruqlar</b>\n\n";
        foreach ($commands as $cmd) {
            $text .= "/{$cmd->getCommand()} — {$cmd->getDescription()}\n";
        }
        $text .= "\n<i>Eslatma: moderatsiya buyruqlari ishlashi uchun meni guruhingizda admin qiling.</i>";

        try {
            $this->app->make(TelegramService::class)->send($update, $text);
        } catch (\Throwable) {}
    }
}
