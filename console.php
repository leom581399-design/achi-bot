<?php
declare(strict_types=1);

/**
 * CLI entry point.
 *
 * Usage:
 *   php console.php migrate                      — run pending migrations
 *   php console.php migrate:status               — show migration status
 *   php console.php webhook:set <url>            — register webhook with Telegram
 *   php console.php webhook:delete               — remove webhook (back to polling)
 *   php console.php cache:clear                  — flush filesystem cache
 *   php console.php modules:list                 — list loaded modules
 */

require_once __DIR__ . '/vendor/autoload.php';

$app = require __DIR__ . '/app/bootstrap/app.php';

use App\Core\Kernel;
use App\Core\Console\Console;
use App\Core\Console\Commands\{
    MigrateCommand,
    MigrationStatusCommand,
    SetWebhookCommand,
    DeleteWebhookCommand,
    ClearCacheCommand,
    ListModulesCommand
};

// Boot the framework (registers all services, runs migrations) without polling loop
$app->make(Kernel::class)->bootOnly();

$console = new Console($app);
$console
    ->register('migrate',          MigrateCommand::class)
    ->register('migrate:status',   MigrationStatusCommand::class)
    ->register('webhook:set',      SetWebhookCommand::class)
    ->register('webhook:delete',   DeleteWebhookCommand::class)
    ->register('cache:clear',      ClearCacheCommand::class)
    ->register('modules:list',     ListModulesCommand::class);

$moduleLoader = $app->make(\App\Core\ModuleLoader::class);
foreach ($moduleLoader->getConsoleCommands() as $name => $class) {
    $console->register($name, $class);
}

exit($console->run($argv));
