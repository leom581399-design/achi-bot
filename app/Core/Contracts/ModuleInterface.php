<?php
declare(strict_types=1);

namespace App\Core\Contracts;

use App\Core\Application;

/**
 * Every module MUST implement this interface.
 * The Core only ever calls these methods — it knows nothing else about modules.
 */
interface ModuleInterface
{
    /** Human-readable name used in logs and dependency resolution. */
    public function getName(): string;

    public function getVersion(): string;

    /**
     * List of module names this module depends on.
     * If any dependency is missing, this module is skipped.
     *
     * @return string[]
     */
    public function getDependencies(): array;

    /**
     * Called once during bootstrap, before register().
     * Ideal for loading language files, config, etc.
     */
    public function boot(Application $app): void;

    /**
     * Called after boot(). Bind anything into the container here.
     */
    public function register(Application $app): void;

    /**
     * Return the command instances this module provides.
     *
     * @return CommandInterface[]
     */
    public function getCommands(): array;

    /**
     * Return event listeners this module registers.
     * Format: ['event.name' => [callable, callable, ...]]
     *
     * @return array<string, list<callable>>
     */
    public function getEvents(): array;
}
