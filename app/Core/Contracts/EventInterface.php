<?php
declare(strict_types=1);

namespace App\Core\Contracts;

/**
 * Optional marker interface for typed event objects.
 * The EventDispatcher works with plain strings + any payload,
 * but modules may choose to create typed events for clarity.
 */
interface EventInterface
{
    /** The event name as emitted via EventDispatcher::emit(). */
    public function getName(): string;

    /** Serialisable payload for this event. */
    public function getData(): array;
}
