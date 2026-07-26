<?php
declare(strict_types=1);

namespace App\Core\Console\Commands;

use App\Core\Application;

class ListModulesCommand
{
    public function __construct(private readonly Application $app) {}

    public function handle(array $args): int
    {
        if ($this->app->has(\App\Core\ModuleLoader::class)) {
            $loader = $this->app->make(\App\Core\ModuleLoader::class);
            $loaded = $loader->getLoaded();
            if ($loaded !== []) {
                echo sprintf("📦 Loaded %d module(s):\n\n", count($loaded));
                foreach ($loaded as $name) {
                    $source = $loader->getSources()[$name] ?? 'unknown';
                    $module = $loader->getLoadedModules()[$name] ?? null;
                    $version = $module?->getVersion() ?? 'unknown';
                    echo "  • {$name} v{$version} [{$source}]\n";
                }
                echo "\n";
                return 0;
            }
        }

        $modulesDir = __DIR__ . '/../../../../modules';

        if (!is_dir($modulesDir)) {
            echo "⚠️  No modules directory found.\n";
            return 0;
        }

        $dirs = array_filter(
            glob($modulesDir . '/*') ?: [],
            fn($d) => is_dir($d) && file_exists($d . '/module.php')
        );

        if (empty($dirs)) {
            echo "⚠️  No modules found.\n";
            return 0;
        }

        echo sprintf("📦 Found %d module(s):\n\n", count($dirs));

        foreach ($dirs as $dir) {
            $name = basename($dir);
            echo "  • {$name}\n";
        }

        echo "\n";
        return 0;
    }
}
