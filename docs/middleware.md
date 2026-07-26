# Sistema de Middlewares

## Como funciona

O `Pipeline` executa uma cadeia de middlewares antes do handler do comando.
Cada middleware pode:
- **Passar adiante**: chamar `$next($update)` para continuar
- **Bloquear**: retornar `null` sem chamar `$next` para interromper

```
Requisição
    │
    ▼
[GroupOnlyMiddleware]   → passa? ──► [PermissionMiddleware]  → passa? ──► [FloodMiddleware] → passa? ──► handle()
       ↑ bloqueia                          ↑ bloqueia                        ↑ bloqueia
       └─ retorna null                     └─ retorna null                   └─ retorna null
```

---

## Middlewares disponíveis

### GroupOnlyMiddleware

Bloqueia se o comando não foi enviado em um grupo ou supergrupo.

```php
use App\Core\Middleware\GroupOnlyMiddleware;

new GroupOnlyMiddleware($this->app)
```

**Resposta automática:** `❌ This command can only be used inside a group.`

---

### PrivateOnlyMiddleware

Bloqueia se o comando não foi enviado em chat privado.

```php
use App\Core\Middleware\PrivateOnlyMiddleware;

new PrivateOnlyMiddleware($this->app)
```

**Resposta automática:** `❌ This command can only be used in a private chat with me.`

---

### PermissionMiddleware

Bloqueia se o usuário não tiver o nível mínimo de permissão.

```php
use App\Core\Middleware\PermissionMiddleware;
use App\Core\Permission;

new PermissionMiddleware($this->app, Permission::Administrator)
new PermissionMiddleware($this->app, Permission::Moderator)
```

**Resposta automática:** `⛔ Permission denied. You need at least ⚙️ Administrator...`

---

### FloodMiddleware

Rate-limiting por usuário por minuto. Descarta silenciosamente (sem responder).

```php
use App\Core\Middleware\FloodMiddleware;

new FloodMiddleware($this->app)          // padrão: 15 por minuto
new FloodMiddleware($this->app, 5)       // máximo 5 por minuto
new FloodMiddleware($this->app, 30)      // máximo 30 por minuto
```

---

## Criar um middleware customizado

```php
// app/Core/Middleware/MaintenanceMiddleware.php
<?php
declare(strict_types=1);

namespace App\Core\Middleware;

use App\Core\Application;
use App\Core\Contracts\MiddlewareInterface;
use App\Core\Permission;
use App\Core\Services\{CacheService, PermissionService, TelegramService};
use App\Core\Update;

class MaintenanceMiddleware implements MiddlewareInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function handle(Update $update, callable $next): mixed
    {
        $cache = $this->app->make(CacheService::class);

        if (!$cache->get('maintenance_mode')) {
            return $next($update);  // não está em manutenção, continua
        }

        $userId = $update->getUserId();
        $perm   = $this->app->make(PermissionService::class);

        // Owners podem usar durante manutenção
        if ($perm->isOwner($userId)) {
            return $next($update);
        }

        $this->app->make(TelegramService::class)->reply(
            $update,
            '🔧 Bot em manutenção. Tente novamente em breve.'
        );
        return null;
    }
}
```

---

## Usando middlewares em um comando

```php
public function getMiddleware(): array
{
    return [
        // Ordem importa — executados da esquerda para a direita
        new GroupOnlyMiddleware($this->app),                              // 1. só em grupos
        new PermissionMiddleware($this->app, Permission::Administrator),  // 2. só admins
        new FloodMiddleware($this->app, 3),                              // 3. max 3/min
    ];
}
```

---

## Pipeline — implementação interna

```php
// array_reduce cria a cadeia de forma reversa (onion model)
$pipeline = array_reduce(
    array_reverse($middlewares),
    fn($carry, $middleware) =>
        fn(Update $update) => $middleware->handle($update, $carry),
    $destination  // o handler final
);

$pipeline($update);
```

Trace de execução com `[A, B, C]`:
1. `A->handle($update, fn → B->handle(fn → C->handle(fn → handler)))`
2. A chama next → B chama next → C chama next → handler executa
