<?php
declare(strict_types=1);

namespace App\Core\Console\Commands;

use App\Core\Application;
use App\Core\Database\MigrationRunner;
use App\Core\Services\DatabaseService;

class MigrationStatusCommand
{
    public function __construct(private readonly Application $app) {}

    public function handle(array $args): int
    {
        $db      = $this->app->make(DatabaseService::class);
        $runner  = new MigrationRunner($db->pdo());
        $applied = $runner->getAppliedVersions();

        echo "📊 Migration status:\n\n";

        if (empty($applied)) {
            echo "  No migrations applied yet.\n";
        } else {
            foreach ($applied as $version) {
                echo "  ✅ {$version}\n";
            }
        }

        echo "\n";
        return 0;
    }
}
