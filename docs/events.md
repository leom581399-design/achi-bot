# Sistema de Eventos

## Como funciona

O `EventDispatcher` implementa o padrão **Observer / Pub-Sub**. Módulos se comunicam exclusivamente via eventos — nunca importando uns aos outros diretamente.

```
Módulo Ban emite 'member.banned'
        ↓
    EventDispatcher
        ↓
Módulo Logs ouve 'member.banned' → salva no banco
Módulo Fed  ouve 'member.banned' → propaga para federação
```

---

## Registrar listeners (no getEvents() do módulo)

```php
public function getEvents(): array
{
    return [
        'user.joined' => [
            fn(array $data) => $this->handleUserJoined($data),
        ],
        'member.banned' => [
            fn(array $data) => $this->handleBanned($data),
            fn(array $data) => $this->logBan($data),  // múltiplos listeners
        ],
        '*' => [
            fn(string $event, mixed $data) => $this->logAll($event, $data),
        ],
    ];
}
```

---

## Emitir eventos (em comandos ou módulos)

```php
$dispatcher = $app->make(EventDispatcher::class);

// Emitir com payload array
$dispatcher->emit('member.banned', [
    'update'  => $update,
    'user_id' => $targetId,
    'reason'  => $reason,
    'admin'   => $update->getUserId(),
]);

// Emitir sem payload
$dispatcher->emit('maintenance.enabled');
```

---

## Eventos do Core (emitidos pelo Router)

### `message.received`
- **Payload:** `Update $update`
- **Quando:** Toda mensagem recebida (incluindo comandos)

```php
'message.received' => [
    function(Update $update) {
        // processar qualquer mensagem
    }
],
```

### `user.joined`
- **Payload:** `['update' => Update, 'member' => array]`
- **Quando:** Um ou mais usuários entraram no grupo

```php
'user.joined' => [
    function(array $data) {
        $update = $data['update'];
        $member = $data['member'];  // array com dados do usuário
        $userId = $member['id'];
        // ex: enviar captcha, welcome message, verificar se é banido
    }
],
```

### `user.left`
- **Payload:** `['update' => Update, 'member' => array]`
- **Quando:** Usuário saiu ou foi removido

```php
'user.left' => [
    function(array $data) {
        $member = $data['member'];
        // ex: mensagem de despedida
    }
],
```

### `callback.received`
- **Payload:** `Update $update`
- **Quando:** Botão de teclado inline foi clicado

```php
'callback.received' => [
    function(Update $update) {
        $callbackData = $update->callbackQuery['data'];
        // ex: processar ações de botões inline
    }
],
```

### `member.updated`
- **Payload:** `Update $update`
- **Quando:** Status de membro no chat foi alterado (promovido, restrito, etc.)

### `command.before`
- **Payload:** `['command' => string, 'update' => Update]`
- **Quando:** Imediatamente antes de qualquer comando ser processado

```php
'command.before' => [
    function(array $data) {
        // ex: logar todos os comandos, verificar manutenção
        if ($this->isInMaintenance() && $data['command'] !== 'maintenance') {
            // impedir execução
        }
    }
],
```

### `command.after`
- **Payload:** `['command' => string, 'update' => Update]`
- **Quando:** Após o handler do comando (mesmo se o middleware bloqueou)

### `command.executed`
- **Payload:** `['command' => string, 'update' => Update]`
- **Quando:** Após o pipeline completo ser executado

---

## Eventos de módulos (convenção para Fase 2+)

Estes eventos serão emitidos pelos módulos de features. Seguir esta convenção ao implementar:

| Evento | Payload esperado |
|---|---|
| `member.banned` | `['update', 'user_id', 'reason', 'until_date?', 'admin_id']` |
| `member.unbanned` | `['update', 'user_id', 'admin_id']` |
| `member.kicked` | `['update', 'user_id', 'reason?', 'admin_id']` |
| `member.muted` | `['update', 'user_id', 'until_date?', 'reason?', 'admin_id']` |
| `member.unmuted` | `['update', 'user_id', 'admin_id']` |
| `member.warned` | `['update', 'user_id', 'reason', 'warn_count', 'admin_id']` |
| `member.warn_limit` | `['update', 'user_id', 'action_taken']` |
| `note.saved` | `['chat_id', 'name', 'content']` |
| `note.deleted` | `['chat_id', 'name']` |
| `filter.triggered` | `['update', 'filter_name', 'action']` |
| `flood.detected` | `['update', 'user_id', 'count']` |
| `spam.detected` | `['update', 'user_id', 'type']` |
| `captcha.started` | `['update', 'user_id']` |
| `captcha.passed` | `['update', 'user_id']` |
| `captcha.failed` | `['update', 'user_id']` |

---

## Wildcard listener (ouvir todos os eventos)

```php
public function getEvents(): array
{
    return [
        '*' => [
            function(string $eventName, mixed $payload) {
                // Este listener recebe TODOS os eventos
                $this->logger->debug("Evento: {$eventName}");
            }
        ],
    ];
}
```

---

## Remover listener (uso avançado)

```php
$dispatcher = $app->make(EventDispatcher::class);

// Adicionar
$listener = fn($data) => $this->handle($data);
$dispatcher->on('user.joined', $listener);

// Remover
$dispatcher->off('user.joined', $listener);

// Remover todos de um evento
$dispatcher->off('user.joined');
```
