<?php
declare(strict_types=1);

namespace Modules\Filters\Events;

use App\Core\Application;
use App\Core\Update;
use Modules\Filters\Services\FilterService;

/**
 * Ouve message.received e dispara filtros automáticos quando uma palavra-chave é detectada.
 */
class FilterListener
{
    public function __construct(private readonly Application $app) {}

    public function __invoke(mixed $data): void
    {
        $this->handle(is_array($data) ? $data : []);
    }

    public function handle(array $data): void
    {
        /** @var Update $update */
        $update = $data['update'] ?? null;
        if ($update === null) return;

        // Ignora comandos para não conflitar com handlers de comando
        if ($update->isCommand()) return;

        $this->app->make(FilterService::class)->checkAndRespond($update);
    }
}
