<?php
declare(strict_types=1);

namespace App\Core;

/**
 * Simple pub/sub event dispatcher.
 *
 * Modules register listeners with on(); the Router (and other modules)
 * emit events with emit(). Listeners are plain callables — no magic.
 *
 * Wildcard listeners registered under '*' receive ALL events:
 *   $dispatcher->on('*', fn(string $event, mixed $payload) => ...);
 */
class EventDispatcher
{
    /** @var array<string, list<callable>> */
    private array $listeners = [];

    public function on(string $event, callable $listener): void
    {
        $this->listeners[$event][] = $listener;
    }

    public function off(string $event, ?callable $listener = null): void
    {
        if ($listener === null) {
            unset($this->listeners[$event]);
            return;
        }
        $this->listeners[$event] = array_values(
            array_filter($this->listeners[$event] ?? [], fn($l) => $l !== $listener)
        );
    }

    public function emit(string $event, mixed $payload = null): void
    {
        foreach ($this->listeners[$event] ?? [] as $listener) {
            $listener($payload);
        }
        // Wildcard
        foreach ($this->listeners['*'] ?? [] as $listener) {
            $listener($event, $payload);
        }
    }

    public function hasListeners(string $event): bool
    {
        return !empty($this->listeners[$event]);
    }
}
