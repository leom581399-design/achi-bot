<?php
declare(strict_types=1);

namespace App\Core\Events;

use App\Core\Contracts\EventInterface;
use App\Core\Update;

/** Emitted when one or more users join a group. Event name: 'user.joined' */
class UserJoined implements EventInterface
{
    public function __construct(
        public readonly Update $update,
        public readonly array  $member   // The joining user array from Telegram
    ) {}

    public function getName(): string { return 'user.joined'; }
    public function getData(): array  { return ['update' => $this->update, 'member' => $this->member]; }
}
