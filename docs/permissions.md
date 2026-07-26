# Sistema de Permissões

## Hierarquia

```
Owner (100)          → dono do bot (definido via OWNER_IDS)
    ↓
Developer (90)       → desenvolvedores autorizados
    ↓
Administrator (80)   → admins do grupo no Telegram
    ↓
Moderator (70)       → moderadores designados (futuro)
    ↓
VIP (60)             → usuários com acesso especial (futuro)
    ↓
User (0)             → usuário comum
```

---

## O enum Permission

```php
use App\Core\Permission;

// Valores disponíveis
Permission::Owner         // 100
Permission::Developer     // 90
Permission::Administrator // 80
Permission::Moderator     // 70
Permission::VIP           // 60
Permission::User          // 0

// Verificar hierarquia
Permission::Administrator->isAtLeast(Permission::User);   // true
Permission::User->isAtLeast(Permission::Administrator);   // false

// Label formatado
Permission::Administrator->label();  // "⚙️ Administrator"
```

---

## Verificação via PermissionService

```php
use App\Core\Services\PermissionService;
$perm = $app->make(PermissionService::class);

// Obter nível de permissão
$level = $perm->getPermission($chatId, $userId);

// Verificar se tem acesso
if ($perm->can($chatId, $userId, Permission::Administrator)) {
    // pode executar ação de admin
}

// Verificar owner (não precisa de chatId)
if ($perm->isOwner($userId)) {
    // é owner do bot
}
```

---

## Verificação via Middleware (recomendado)

```php
public function getMiddleware(): array
{
    return [
        new GroupOnlyMiddleware($this->app),
        new PermissionMiddleware($this->app, Permission::Administrator),
    ];
}
```

Se o usuário não tiver permissão, o middleware envia mensagem automática e interrompe a pipeline.

---

## Como os níveis são resolvidos

O `PermissionService::getPermission()` resolve assim:

1. **Owner**: usuário está no `OWNER_IDS` → `Permission::Owner`
2. **Administrator**: status no chat é `creator` ou `administrator` → `Permission::Administrator`
3. **User**: qualquer outro status (`member`, `restricted`, etc.) → `Permission::User`

> **Nota:** Os níveis `Developer`, `Moderator` e `VIP` ainda não são resolvidos automaticamente.
> Serão implementados na Fase 1.5 (via banco de dados — tabela `user_roles`).

---

## Configuração de Owners

```bash
# .env / Replit Secret
OWNER_IDS=123456789,987654321
```

IDs separados por vírgula. O usuário com esse ID terá nível `Owner` em qualquer grupo.

---

## Exemplo completo em um comando

```php
public function handle(Update $update, Application $app): void
{
    $perm   = $app->make(PermissionService::class);
    $chatId = $update->getChatId();
    $userId = $update->getUserId();

    // Verificar alvo do comando (usuário respondido)
    $reply = $update->getReplyToMessage();
    if (!$reply) {
        $app->make(TelegramService::class)->reply($update, '❌ Responda a uma mensagem.');
        return;
    }

    $targetId = $reply['from']['id'];

    // Não pode executar ação em si mesmo
    if ($targetId === $userId) {
        $telegram->reply($update, '❌ Você não pode fazer isso em si mesmo.');
        return;
    }

    // Não pode executar ação em alguém com permissão maior
    $userPerm   = $perm->getPermission($chatId, $userId);
    $targetPerm = $perm->getPermission($chatId, $targetId);

    if ($targetPerm->isAtLeast($userPerm)) {
        $telegram->reply($update, '⛔ Você não pode fazer isso com este usuário.');
        return;
    }

    // Executar ação...
}
```
