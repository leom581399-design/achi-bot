<?php
declare(strict_types=1);

namespace App\Core\Console\Commands;

use App\Core\Application;
use App\Core\Telegram\TelegramClient;

class SetWebhookCommand
{
    public function __construct(private readonly Application $app) {}

    public function handle(array $args): int
    {
        $url = $args[0] ?? '';

        if (empty($url)) {
            echo "Usage: php console.php webhook:set <url>\n";
            echo "Example: php console.php webhook:set https://mydomain.com/webhook.php\n";
            return 1;
        }

        echo "🔧 Registering webhook: {$url}\n";

        $client = $this->app->make(TelegramClient::class);
        $result = $client->request('setWebhook', ['url' => $url]);

        if ($result['ok'] ?? false) {
            echo "✅ Webhook registered successfully.\n";
            return 0;
        }

        echo "❌ Failed: " . ($result['description'] ?? 'Unknown error') . "\n";
        return 1;
    }
}
