<?php
declare(strict_types=1);

namespace App\Core;

use App\Core\Contracts\CommandInterface;

/**
 * Holds all registered commands and dispatches incoming command updates
 * through the middleware pipeline before calling the handler.
 */
class CommandRegistry
{
    /** @var array<string, CommandInterface> */
    private array $commands = [];

    public function __construct(
        private readonly Application $app
    ) {}

    public function register(CommandInterface $command): void
    {
        $this->commands[$command->getCommand()] = $command;
    }

    public function has(string $command): bool
    {
        return isset($this->commands[$command]);
    }

    public function get(string $command): ?CommandInterface
    {
        return $this->commands[$command] ?? null;
    }

    /** @return array<string, CommandInterface> */
    public function all(): array
    {
        return $this->commands;
    }

    /**
     * Dispatch an update to its matching command through the middleware pipeline.
     */
    public function dispatch(Update $update): void
    {
        $command = $update->getCommand();
        if ($command === null || !$this->has($command)) return;

        $handler     = $this->commands[$command];
        $middlewares = $handler->getMiddleware();

        $pipeline = new Middleware\Pipeline($this->app);
        $pipeline
            ->through($middlewares)
            ->dispatch($update, function (Update $update) use ($handler): void {
                $handler->handle($update, $this->app);
            });
    }
}
