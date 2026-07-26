<?php
declare(strict_types=1);

namespace App\Core;

/**
 * Simple service container / dependency injection container.
 * Acts as the backbone of the framework — all services are registered and resolved here.
 */
class Application
{
    private array $bindings  = [];
    private array $instances = [];
    private static ?self $instance = null;

    private function __construct() {}

    public static function getInstance(): static
    {
        if (static::$instance === null) {
            static::$instance = new static();
        }
        return static::$instance;
    }

    /**
     * Register a transient binding (new instance on every make()).
     */
    public function bind(string $abstract, \Closure $factory): void
    {
        $this->bindings[$abstract] = ['factory' => $factory, 'singleton' => false];
    }

    /**
     * Register a singleton binding (same instance returned on every make()).
     */
    public function singleton(string $abstract, \Closure $factory): void
    {
        $this->bindings[$abstract] = ['factory' => $factory, 'singleton' => true];
    }

    /**
     * Register an already-built instance as a singleton.
     */
    public function instance(string $abstract, mixed $value): void
    {
        $this->instances[$abstract] = $value;
        $this->bindings[$abstract]  = ['factory' => fn() => $value, 'singleton' => true];
    }

    /**
     * Resolve a binding.
     */
    public function make(string $abstract): mixed
    {
        if (isset($this->instances[$abstract])) {
            return $this->instances[$abstract];
        }

        if (!isset($this->bindings[$abstract])) {
            throw new \RuntimeException("No binding found for [{$abstract}]");
        }

        $binding  = $this->bindings[$abstract];
        $resolved = ($binding['factory'])($this);

        if ($binding['singleton']) {
            $this->instances[$abstract] = $resolved;
        }

        return $resolved;
    }

    public function has(string $abstract): bool
    {
        return isset($this->bindings[$abstract]) || isset($this->instances[$abstract]);
    }
}
