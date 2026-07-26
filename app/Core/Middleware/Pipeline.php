<?php
declare(strict_types=1);

namespace App\Core\Middleware;

use App\Core\Application;
use App\Core\Update;

/**
 * Runs an Update through an ordered stack of MiddlewareInterface instances
 * before calling the final destination (command handler).
 *
 * Any middleware can short-circuit the pipeline by not calling $next.
 */
class Pipeline
{
    private array $middlewares = [];

    public function __construct(
        private readonly Application $app
    ) {}

    /** @param \App\Core\Contracts\MiddlewareInterface[] $middlewares */
    public function through(array $middlewares): static
    {
        $this->middlewares = $middlewares;
        return $this;
    }

    public function dispatch(Update $update, callable $destination): mixed
    {
        $pipeline = array_reduce(
            array_reverse($this->middlewares),
            fn(callable $carry, $middleware): callable =>
                fn(Update $update): mixed => $middleware->handle($update, $carry),
            $destination
        );

        return $pipeline($update);
    }
}
