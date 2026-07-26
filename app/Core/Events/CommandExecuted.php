<?php
declare(strict_types=1);

namespace App\Core\Events;

use App\Core\Contracts\EventInterface;
use App\Core\Update;

/** Emitted after a command handler runs successfully. Event name: 'command.executed' */
class CommandExecuted implements EventInterface
{
    public function __construct(
        public readonly string $command,
        public readonly Update $update
    ) {}

    public function getName(): string { return 'command.executed'; }
    public function getData(): array  { return ['command' => $this->command, 'update' => $this->update]; }
}
