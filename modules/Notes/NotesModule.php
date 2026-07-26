<?php
declare(strict_types=1);

namespace Modules\Notes;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\{DatabaseService, LanguageService};
use Modules\Notes\Repository\NotesRepository;
use Modules\Notes\Services\NotesService;

class NotesModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'Notes'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }

    public function boot(Application $app): void
    {
        $this->app = $app;
        $app->make(LanguageService::class)->load('Notes', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        $app->singleton(NotesRepository::class, fn($a) => new NotesRepository($a->make(DatabaseService::class)));
        $app->singleton(NotesService::class,    fn($a) => new NotesService($a));
    }

    public function getCommands(): array
    {
        return [
            new Commands\SaveCommand($this->app),
            new Commands\GetCommand($this->app),
            new Commands\ClearCommand($this->app),
            new Commands\NotesListCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'message.received' => [new Events\HashtagNoteListener($this->app)],
        ];
    }
}
