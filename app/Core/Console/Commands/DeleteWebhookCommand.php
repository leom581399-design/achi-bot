<?php
declare(strict_types=1);

namespace App\Core\Console\Commands;

use App\Core\Application;
use App\Core\Telegram\TelegramClient;

class DeleteWebhookCommand
{
    public function __construct(private readonly Application $app) {}

    public function handle(array $args): int
    {
        echo "🔧 Removing webhook (reverting to long polling)...\n";

        $dropPending = in_array('--drop-pending', $args, true);

        $client = $this->app->make(TelegramClient::class);
        $result = $client->request('deleteWebhook', [
            'drop_pending_updates' => $dropPending,
        ]);

        if ($result['ok'] ?? false) {
            echo "✅ Webhook deleted. Bot is back to long polling.\n";
            return 0;
        }

        echo "❌ Failed: " . ($result['description'] ?? 'Unknown error') . "\n";
        return 1;
    }
}
