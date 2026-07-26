<?php
declare(strict_types=1);

namespace App\Core\Middleware;

use App\Core\Application;
use App\Core\Contracts\MiddlewareInterface;
use App\Core\Update;
use App\Core\Services\TelegramService;

/**
 * Rejects the command if it was not sent in a private chat.
 */
class PrivateOnlyMiddleware implements MiddlewareInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function handle(Update $update, callable $next): mixed
    {
        if (!$update->isPrivate()) {
            $this->app->make(TelegramService::class)->reply(
                $update,
                '❌ This command can only be used in a private chat with me.'
            );
            return null;
        }

        return $next($update);
    }
}
