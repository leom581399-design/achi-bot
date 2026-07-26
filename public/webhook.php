<?php
declare(strict_types=1);

/**
 * Webhook entry point.
 *
 * Register with Telegram:
 *   php console.php webhook:set https://your-domain.com/webhook.php
 *
 * Or use the long-polling runner (run.php) for local development.
 */

require_once __DIR__ . '/../vendor/autoload.php';

$app = require __DIR__ . '/../app/bootstrap/app.php';

use App\Core\Kernel;
use App\Core\Telegram\WebhookHandler;

// Boot the framework without starting the polling loop
$app->make(Kernel::class)->bootOnly();

// Handle the incoming webhook request
$verifyIp = (bool)(getenv('WEBHOOK_VERIFY_IP') ?: false);
(new WebhookHandler($app, $verifyIp))->handle();
