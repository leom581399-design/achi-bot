<?php
declare(strict_types=1);

namespace App\Core\Contracts;

use App\Core\Update;

/**
 * Middleware sits between the Router and a command handler.
 * Call $next($update) to pass control to the next layer.
 * Return without calling $next to short-circuit the pipeline.
 */
interface MiddlewareInterface
{
    public function handle(Update $update, callable $next): mixed;
}
