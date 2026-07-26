<?php
declare(strict_types=1);

namespace App\Core\Events;

use App\Core\Contracts\EventInterface;
use App\Core\Update;

/** Emitted for every incoming message update. Event name: 'message.received' */
class MessageReceived implements EventInterface
{
    public function __construct(public readonly Update $update) {}

    public function getName(): string { return 'message.received'; }
    public function getData(): array  { return ['update' => $this->update]; }
}
