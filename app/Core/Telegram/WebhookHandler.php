<?php
declare(strict_types=1);

namespace App\Core\Telegram;

use App\Core\Application;
use App\Core\Router;
use App\Core\Update;

/**
 * Handles a single Telegram update delivered via webhook (HTTP POST).
 *
 * Usage (from public/webhook.php):
 *   $handler = new WebhookHandler($app);
 *   $handler->handle();
 */
class WebhookHandler
{
    /**
     * Telegram IP ranges (v4 and v6) for signature verification.
     * Source: https://core.telegram.org/bots/webhooks#the-short-version
     */
    private const TELEGRAM_IP_RANGES = [
        '149.154.160.0/20',
        '91.108.4.0/22',
    ];

    public function __construct(
        private readonly Application $app,
        private readonly bool $verifyIp = false
    ) {}

    /**
     * Read the incoming POST body, decode it as JSON, and dispatch the update.
     * Always responds with 200 OK — Telegram requires this.
     */
    public function handle(): void
    {
        http_response_code(200);
        header('Content-Type: text/plain');

        if ($this->verifyIp && !$this->isValidTelegramIp()) {
            echo 'forbidden';
            return;
        }

        $raw = $this->readBody();

        if ($raw === null) {
            echo 'no body';
            return;
        }

        try {
            $router = $this->app->make(Router::class);
            $router->dispatch(new Update($raw));
            echo 'ok';
        } catch (\Throwable $e) {
            // Log but never expose internals to Telegram
            error_log('[WebhookHandler] Error: ' . $e->getMessage());
            echo 'ok';
        }
    }

    // -------------------------------------------------------------------------
    // Internals
    // -------------------------------------------------------------------------

    private function readBody(): ?array
    {
        $json = file_get_contents('php://input');

        if (empty($json)) {
            return null;
        }

        $data = json_decode($json, true);

        if (!is_array($data) || !isset($data['update_id'])) {
            return null;
        }

        return $data;
    }

    private function isValidTelegramIp(): bool
    {
        $remoteIp = $_SERVER['REMOTE_ADDR'] ?? '';

        if (empty($remoteIp)) {
            return false;
        }

        foreach (self::TELEGRAM_IP_RANGES as $cidr) {
            if ($this->ipInCidr($remoteIp, $cidr)) {
                return true;
            }
        }

        return false;
    }

    private function ipInCidr(string $ip, string $cidr): bool
    {
        [$subnet, $prefix] = explode('/', $cidr);
        $ipLong     = ip2long($ip);
        $subnetLong = ip2long($subnet);

        if ($ipLong === false || $subnetLong === false) {
            return false;
        }

        $mask = ~((1 << (32 - (int)$prefix)) - 1);

        return ($ipLong & $mask) === ($subnetLong & $mask);
    }
}
