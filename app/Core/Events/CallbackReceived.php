<?php
declare(strict_types=1);

namespace App\Core\Events;

use App\Core\Contracts\EventInterface;
use App\Core\Update;

/** Emitted on inline keyboard button presses. Event name: 'callback.received' */
class CallbackReceived implements EventInterface
{
    public function __construct(public readonly Update $update) {}

    public function getName(): string { return 'callback.received'; }
    public function getData(): array  { return ['update' => $this->update]; }
}
