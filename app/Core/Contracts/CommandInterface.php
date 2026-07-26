<?php
declare(strict_types=1);

namespace App\Core\Contracts;

use App\Core\Application;
use App\Core\Permission;
use App\Core\Update;

/**
 * Every command class MUST implement this interface.
 * Commands are never registered manually — the ModuleLoader does it automatically.
 */
interface CommandInterface
{
    /**
     * The command trigger without the slash, lowercase.
     * e.g. "ban", "mute", "help"
     */
    public function getCommand(): string;

    /** Short description shown in /help. */
    public function getDescription(): string;

    /**
     * Minimum permission level required to execute this command.
     * The PermissionMiddleware enforces this if included in getMiddleware().
     */
    public function getPermission(): Permission;

    /**
     * Middleware stack applied before handle() is called.
     * Return an empty array for no middleware.
     *
     * @return MiddlewareInterface[]
     */
    public function getMiddleware(): array;

    /** Execute the command. */
    public function handle(Update $update, Application $app): void;
}
