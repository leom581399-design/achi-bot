<?php
declare(strict_types=1);

namespace App\Core\Console\Commands;

use App\Core\Application;
use App\Core\Database\MigrationRunner;
use App\Core\Services\DatabaseService;

class MigrateCommand
{
    public function __construct(private readonly Application $app) {}

    public function handle(array $args): int
    {
        echo "🔧 Running database migrations...\n";

        $db     = $this->app->make(DatabaseService::class);
        $runner = new MigrationRunner($db->pdo());

        $applied = $runner->run(verbose: true);

        if (empty($applied)) {
            echo "✅ Nothing to migrate — already up to date.\n";
        } else {
            echo sprintf("✅ Applied %d migration(s): %s\n", count($applied), implode(', ', $applied));
        }

        return 0;
    }
}
