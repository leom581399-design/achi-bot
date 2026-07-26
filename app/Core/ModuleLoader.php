<?php
declare(strict_types=1);

namespace App\Core;

use App\Core\Contracts\{CommandInterface, ModuleInterface};
use App\Core\Services\LoggerService;

/**
 * Automatically discovers and boots all modules in the modules/ directory.
 *
 * Rules:
 *  - A directory with a module.php file → directory-style module.
 *  - A single .php file                 → file-style module.
 *  - module.php must return an instance of ModuleInterface.
 *  - Modules whose dependencies are not yet loaded are skipped (with a log warning).
 *  - The Core is never touched to add a new module — just drop a folder in modules/.
 */
class ModuleLoader
{
    private array $loaded = [];
    private array $loadedModules = [];
    private array $sources = [];

    public function __construct(
        private readonly Application $app,
        private readonly string      $modulesPath = ''
    ) {}

    public function loadAll(): void
    {
        $path   = $this->resolvePath();
        $logger = $this->app->make(LoggerService::class);

        if (!is_dir($path)) {
            $logger->warning("Modules directory not found: {$path}");
            return;
        }

        $logger->info("Loading modules from: {$path}");

        foreach (new \DirectoryIterator($path) as $item) {
            if ($item->isDot()) continue;

            try {
                if ($item->isDir()) {
                    $this->loadDirectoryModule($item->getPathname(), $item->getFilename());
                } elseif ($item->isFile() && $item->getExtension() === 'php') {
                    $this->loadFileModule($item->getPathname(), $item->getBasename('.php'));
                }
            } catch (\Throwable $e) {
                $logger->error("Failed to load module [{$item->getFilename()}]: " . $e->getMessage());
            }
        }

        $this->loadComposerModules();

        $count = count($this->loaded);
        $logger->info("✅ {$count} module(s) loaded: " . implode(', ', $this->loaded));
    }

    // -------------------------------------------------------------------------
    // Internal
    // -------------------------------------------------------------------------

    private function loadDirectoryModule(string $dirPath, string $name): void
    {
        $moduleFile = $dirPath . '/module.php';
        if (!file_exists($moduleFile)) return;

        $module = require $moduleFile;
        $this->bootModule($module, $name);
    }

    private function loadFileModule(string $filePath, string $name): void
    {
        $module = require $filePath;
        $this->bootModule($module, $name);
    }

    private function bootModule(mixed $module, string $name): void
    {
        $logger = $this->app->make(LoggerService::class);

        if (!$module instanceof ModuleInterface) {
            $logger->warning("  [{$name}] does not implement ModuleInterface — skipped");
            return;
        }

        // Dependency check
        foreach ($module->getDependencies() as $dep) {
            if (!in_array($dep, $this->loaded, true)) {
                $logger->warning(
                    "  [{$module->getName()}] skipped: missing dependency [{$dep}]"
                );
                return;
            }
        }

        $module->boot($this->app);
        $module->register($this->app);

        // Register commands
        $registry = $this->app->make(CommandRegistry::class);
        foreach ($module->getCommands() as $command) {
            if ($command instanceof CommandInterface) {
                $registry->register($command);
                $logger->info("    /{$command->getCommand()} — registered");
            }
        }

        // Register event listeners
        $dispatcher = $this->app->make(EventDispatcher::class);
        foreach ($module->getEvents() as $event => $listeners) {
            foreach ($listeners as $listener) {
                $dispatcher->on($event, $listener);
            }
        }

        $this->loaded[] = $module->getName();
        $this->loadedModules[$module->getName()] = $module;
        $this->sources[$module->getName()] ??= 'local';
        $logger->info("  📦 {$module->getName()} v{$module->getVersion()}");
    }

    /**
     * Discover third-party modules from Composer package metadata.
     *
     * Supported package declarations:
     *   "type": "telegram-bot-module",
     *   "extra": { "telegram-bot-module": "Vendor\\Package\\Module" }
     *
     * A package may also use "extra.bot-module" for compatibility with
     * earlier plugin prototypes. Package code is never executed unless it
     * implements ModuleInterface and is autoloadable.
     */
    private function loadComposerModules(): void
    {
        $logger = $this->app->make(LoggerService::class);
        $installedFile = dirname(__DIR__, 2) . '/vendor/composer/installed.php';

        if (!is_file($installedFile)) {
            return;
        }

        try {
            $installed = require $installedFile;
            $versions = is_array($installed['versions'] ?? null)
                ? $installed['versions']
                : [];

            foreach ($versions as $packageName => $metadata) {
                $installPath = $metadata['install_path'] ?? null;
                if (!is_string($installPath) || !is_dir($installPath)) {
                    continue;
                }

                $composerFile = rtrim($installPath, '/') . '/composer.json';
                if (!is_file($composerFile)) {
                    continue;
                }

                $package = json_decode((string) file_get_contents($composerFile), true);
                if (!is_array($package)) {
                    continue;
                }

                $extra = is_array($package['extra'] ?? null) ? $package['extra'] : [];
                $moduleClass = $extra['telegram-bot-module'] ?? $extra['bot-module'] ?? null;
                $isPlugin = ($package['type'] ?? null) === 'telegram-bot-module';

                if (!$isPlugin && !is_string($moduleClass)) {
                    continue;
                }

                $classes = is_array($moduleClass) ? $moduleClass : [$moduleClass];
                foreach ($classes as $class) {
                    if (!is_string($class) || !class_exists($class)) {
                        $logger->warning("  [{$packageName}] plugin class not found: " . (string) $class);
                        continue;
                    }

                    $module = new $class();
                    if (!$module instanceof ModuleInterface) {
                        $logger->warning("  [{$packageName}] plugin does not implement ModuleInterface — skipped");
                        continue;
                    }

                    $this->sources[$module->getName()] = "composer:{$packageName}";
                    $this->bootModule($module, $module->getName());
                }
            }
        } catch (\Throwable $e) {
            $logger->error('Composer module discovery failed: ' . $e->getMessage());
        }
    }

    private function resolvePath(): string
    {
        if ($this->modulesPath !== '') {
            return $this->modulesPath;
        }
        return __DIR__ . '/../../modules';
    }

    public function getLoaded(): array
    {
        return $this->loaded;
    }

    /** @return array<string, ModuleInterface> */
    public function getLoadedModules(): array
    {
        return $this->loadedModules;
    }

    /** @return array<string, string> */
    public function getSources(): array
    {
        return $this->sources;
    }

    /**
     * Optional console command extension point for modules and plugins.
     *
     * A module may expose getConsoleCommands(): array<string, class-string>.
     *
     * @return array<string, class-string>
     */
    public function getConsoleCommands(): array
    {
        $commands = [];
        foreach ($this->loadedModules as $module) {
            if (!method_exists($module, 'getConsoleCommands')) {
                continue;
            }

            $provided = $module->getConsoleCommands();
            if (!is_array($provided)) {
                continue;
            }

            foreach ($provided as $name => $class) {
                if (is_string($name) && is_string($class) && class_exists($class)) {
                    $commands[$name] = $class;
                }
            }
        }

        return $commands;
    }
}
