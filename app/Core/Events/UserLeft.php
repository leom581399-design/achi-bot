<?php
declare(strict_types=1);

namespace App\Core\Events;

use App\Core\Contracts\EventInterface;
use App\Core\Update;

/** Emitted when a user leaves a group. Event name: 'user.left' */
class UserLeft implements EventInterface
{
    public function __construct(
        public readonly Update $update,
        public readonly array  $member
    ) {}

    public function getName(): string { return 'user.left'; }
    public function getData(): array  { return ['update' => $this->update, 'member' => $this->member]; }
}
