<?php
declare(strict_types=1);

namespace App\Core;

use App\Core\Database\MigrationRunner;
use App\Core\Services\{
    LoggerService,
    ConfigService,
    TelegramService,
    PermissionService,
    CacheService,
    LanguageService,
    DatabaseService,
    SettingsService
};
use App\Core\Telegram\TelegramClient;

/**
 * The Kernel orchestrates bootstrap and the long-polling loop.
 * It never knows about specific commands — only about services and modules.
 */
class Kernel
{
    public function __construct(
        private readonly Application $app
    ) {}

    // -------------------------------------------------------------------------
    // Boot
    // -------------------------------------------------------------------------

    public function boot(): void
    {
        $this->registerCoreServices();
        $this->runMigrations();
        $this->app->make(ModuleLoader::class)->loadAll();
    }

    /**
     * Boot without starting the long-polling loop.
     * Used by the webhook handler and CLI commands.
     */
    public function bootOnly(): void
    {
        $this->boot();
    }

    private function registerCoreServices(): void
    {
        $base = __DIR__ . '/../../';

        // Infrastructure
        $this->app->singleton(EventDispatcher::class,  fn()      => new EventDispatcher());
        $this->app->singleton(CommandRegistry::class,  fn($app)  => new CommandRegistry($app));
        $this->app->singleton(Router::class,           fn($app)  => new Router($app));
        $this->app->singleton(ModuleLoader::class,     fn($app)  => new ModuleLoader($app));

        // Utility services
        $this->app->singleton(LoggerService::class, fn() => new LoggerService(
            rtrim($base, '/') . '/logs'
        ));
        $this->app->singleton(ConfigService::class, fn() => new ConfigService(
            rtrim($base, '/') . '/app/config'
        ));
        $this->app->singleton(CacheService::class, fn() => new CacheService(
            rtrim($base, '/') . '/storage/cache'
        ));
        $this->app->singleton(LanguageService::class, fn($app) => new LanguageService($app));

        // Database
        $storageDir = rtrim($base, '/') . '/storage';
        $this->app->singleton(DatabaseService::class, fn() => new DatabaseService($storageDir));
        $this->app->singleton(SettingsService::class, fn($app) => new SettingsService(
            $app->make(DatabaseService::class)
        ));

        // Telegram
        $token = getenv('TELEGRAM_BOT_TOKEN')
            ?: throw new \RuntimeException('TELEGRAM_BOT_TOKEN environment variable is not set');

        $this->app->singleton(TelegramClient::class,    fn()     => new TelegramClient($token));
        $this->app->singleton(TelegramService::class,   fn($app) => new TelegramService($app));
        $this->app->singleton(PermissionService::class, fn($app) => new PermissionService($app));
    }

    private function runMigrations(): void
    {
        try {
            $db     = $this->app->make(DatabaseService::class);
            $runner = new MigrationRunner($db->pdo());
            $runner->run(verbose: false);
        } catch (\Throwable $e) {
            $logger = $this->app->make(LoggerService::class);
            $logger->error('Migration failed: ' . $e->getMessage());
            // Do not crash the bot — log and continue
        }
    }

    // -------------------------------------------------------------------------
    // Run (long polling)
    // -------------------------------------------------------------------------

    public function run(): void
    {
        $this->boot();

        $router   = $this->app->make(Router::class);
        $telegram = $this->app->make(TelegramClient::class);
        $logger   = $this->app->make(LoggerService::class);

        // Verify token & announce
        try {
            $me = $telegram->getMe();
            $logger->info("✅ Bot started: @{$me['username']} (ID: {$me['id']})");
        } catch (\Throwable $e) {
            $logger->error('❌ Failed to contact Telegram API: ' . $e->getMessage());
            exit(1);
        }

        $logger->info('👂 Listening for updates (long polling)...');
        $offset = 0;

        while (true) {
            try {
                $updates = $telegram->getUpdates($offset, 100, 30);

                foreach ($updates as $raw) {
                    $offset = $raw['update_id'] + 1;
                    try {
                        $router->dispatch(new Update($raw));
                    } catch (\Throwable $e) {
                        $logger->error("Error processing update #{$raw['update_id']}: " . $e->getMessage());
                    }
                }
            } catch (\Throwable $e) {
                $logger->error('Error fetching updates: ' . $e->getMessage());
                sleep(5);
            }
        }
    }
}
