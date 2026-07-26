<?php
declare(strict_types=1);

namespace App\Core\Console;

use App\Core\Application;

/**
 * Minimal CLI dispatcher.
 *
 * Usage: php console.php <command> [args...]
 */
class Console
{
    /** @var array<string, string> command name → class FQCN */
    private array $commands = [];

    public function __construct(
        private readonly Application $app
    ) {}

    public function register(string $name, string $class): static
    {
        $this->commands[$name] = $class;
        return $this;
    }

    public function run(array $argv): int
    {
        $command = $argv[1] ?? 'help';
        $args    = array_slice($argv, 2);

        if ($command === 'help' || $command === '--help' || $command === '-h') {
            $this->printHelp();
            return 0;
        }

        if (!isset($this->commands[$command])) {
            echo "❌ Unknown command: {$command}\n";
            echo "Run `php console.php help` to see available commands.\n";
            return 1;
        }

        $class = $this->commands[$command];

        try {
            $handler = new $class($this->app);
            return (int) $handler->handle($args);
        } catch (\Throwable $e) {
            echo "❌ Error: {$e->getMessage()}\n";
            if (getenv('APP_DEBUG') === 'true') {
                echo $e->getTraceAsString() . "\n";
            }
            return 1;
        }
    }

    private function printHelp(): void
    {
        echo "Telegram Group Manager — CLI\n\n";
        echo "Usage: php console.php <command> [arguments]\n\n";
        echo "Available commands:\n";
        foreach ($this->commands as $name => $class) {
            echo "  {$name}\n";
        }
    }
}
