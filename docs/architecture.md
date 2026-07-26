# Arquitetura do Framework

## Visão Geral

O framework segue o padrão **Plugin Architecture** combinado com **IoC Container** e **Event-Driven Design**.

```
                    run.php
                       │
                  bootstrap/app.php
                       │
               Application (container)
                       │
                    Kernel
                       │
            ┌──────────┼──────────┐
            │          │          │
       Services    ModuleLoader  TelegramClient
            │          │
            │    ┌─────┴────────────────────┐
            │    │     modules/             │
            │    │  ┌─────┐ ┌─────┐ ┌────┐ │
            │    │  │Help │ │Start│ │Ban │ │
            │    │  └──┬──┘ └──┬──┘ └─┬──┘ │
            │    └─────┼───────┼───────┼────┘
            │          │       │       │
            │     Commands  Events  Commands
            │          │       │       │
            └──────────┼───────┼───────┘
                       │       │
                CommandRegistry  EventDispatcher
                       │       │
                    Router ────┘
                       │
                  (long polling)
                       │
                 Telegram Update
```

---

## Fluxo de Inicialização

```
run.php
 └─ require bootstrap/app.php
      └─ Application::getInstance()         # singleton do container
      └─ app->singleton(Kernel)
 └─ app->make(Kernel)->run()
      ├─ Kernel::boot()
      │    ├─ registerCoreServices()        # registra todos os serviços como singletons
      │    └─ ModuleLoader::loadAll()
      │         ├─ abre bot/modules/
      │         ├─ para cada pasta/arquivo:
      │         │    ├─ require module.php
      │         │    ├─ verifica ModuleInterface
      │         │    ├─ verifica dependências
      │         │    ├─ module->boot(app)
      │         │    ├─ module->register(app)
      │         │    ├─ registra comandos em CommandRegistry
      │         │    └─ registra eventos em EventDispatcher
      │         └─ log "N módulos carregados"
      └─ Kernel::run() — loop infinito
           ├─ telegram->getMe()             # valida token
           └─ while(true):
                ├─ telegram->getUpdates(offset)
                └─ para cada update:
                     └─ Router::dispatch(Update)
```

---

## Fluxo de um Update recebido

```
Telegram → getUpdates() → Update(array)
                              │
                         Router::dispatch()
                              │
               ┌──────────────┼──────────────────────┐
               │              │                       │
          'message'    'callback_query'         outros tipos
               │              │                       │
    emit('message.received')  emit('callback.received')  emit(...)
               │
    ┌──────────┼──────────────────────┐
    │          │                      │
isCommand?  isNewMember?         isLeftMember?
    │          │                      │
CommandRegistry  emit('user.joined')  emit('user.left')
    │
emit('command.before')
    │
CommandRegistry::dispatch()
    │
Pipeline (middlewares)
    │
    ├─ [GroupOnlyMiddleware]   → passa? continua
    ├─ [PermissionMiddleware]  → passa? continua
    ├─ [FloodMiddleware]       → passa? continua
    └─ CommandInterface::handle(Update, Application)
    │
emit('command.after')
emit('command.executed')
```

---

## Application (IoC Container)

O `Application` é um container de dependências simples. Todos os serviços são registrados nele e resolvidos sob demanda.

```php
// Registrar um singleton (mesma instância sempre)
$app->singleton(TelegramClient::class, fn($app) => new TelegramClient($token));

// Registrar um binding transiente (nova instância a cada chamada)
$app->bind(SomeClass::class, fn($app) => new SomeClass());

// Registrar uma instância pronta
$app->instance('config', $configArray);

// Resolver
$telegram = $app->make(TelegramClient::class);
```

**Por que não usar um container existente (Laravel/Symfony)?**
Para manter zero dependências externas no Core. O container é propositalmente simples.

---

## ModuleLoader — Auto-descoberta

O loader escaneia `bot/modules/` em busca de:

1. **Módulo em pasta** (preferido): diretório com `module.php`
2. **Módulo simples**: arquivo `.php` diretamente em `modules/`

```
modules/
├── Ban/           ← pasta → lê Ban/module.php
│   └── module.php
└── SimpleFeature.php  ← arquivo → lê diretamente
```

O `module.php` deve retornar uma instância de `ModuleInterface`:

```php
// modules/Ban/module.php
<?php
return new \Modules\Ban\BanModule();
```

O loader:
1. Verifica se o retorno implementa `ModuleInterface`
2. Verifica dependências declaradas (`getDependencies()`)
3. Chama `boot()` → `register()` na ordem
4. Registra comandos no `CommandRegistry`
5. Registra listeners no `EventDispatcher`

---

## EventDispatcher — Sistema de Eventos

Baseado no padrão Observer. Módulos se comunicam através de eventos — nunca importando uns aos outros.

```
Módulo A emite evento → EventDispatcher → Módulo B ouve evento
```

### Eventos emitidos pelo Core (Router)

| Evento | Payload | Quando |
|---|---|---|
| `message.received` | `Update` | Toda mensagem |
| `user.joined` | `['update' => Update, 'member' => array]` | Membro entrou |
| `user.left` | `['update' => Update, 'member' => array]` | Membro saiu |
| `callback.received` | `Update` | Botão inline clicado |
| `member.updated` | `Update` | Status de membro alterado |
| `command.before` | `['command' => string, 'update' => Update]` | Antes do handler |
| `command.after` | `['command' => string, 'update' => Update]` | Após o handler |
| `command.executed` | `['command' => string, 'update' => Update]` | Após pipeline completo |

### Eventos emitidos por módulos (exemplos futuros)

| Evento | Módulo | Quando |
|---|---|---|
| `member.banned` | Ban | Usuário banido |
| `member.muted` | Mute | Usuário mutado |
| `member.warned` | Warn | Usuário advertido |
| `note.saved` | Notes | Nota salva |
| `flood.detected` | Flood | Flood detectado |

---

## CommandRegistry

Mantém um mapa `string → CommandInterface`. O `Router` chama `dispatch()` quando detecta um comando no update.

O `CommandRegistry` monta o pipeline de middlewares do comando e executa a cadeia antes de chamar `handle()`.

---

## Pipeline de Middlewares

```
[MiddlewareA] → [MiddlewareB] → [MiddlewareC] → handle()
```

Implementado com `array_reduce` (onion model). Cada middleware recebe `$next` e decide se chama ou não, podendo curto-circuitar a pipeline.

```php
// Numa Command:
public function getMiddleware(): array {
    return [
        new GroupOnlyMiddleware($this->app),           // só em grupos
        new PermissionMiddleware($this->app, Permission::Administrator),  // só admins
        new FloodMiddleware($this->app, 5),            // max 5x/min
    ];
}
```

---

## TelegramClient — Única Porta para a API

**Regra de ouro:** Nenhum módulo, serviço ou comando chama a API do Telegram diretamente.
Tudo passa pelo `TelegramClient`, injetado via container.

```php
// ERRADO — nunca fazer isto em um módulo:
$ch = curl_init('https://api.telegram.org/bot.../sendMessage');

// CORRETO — usar o serviço:
$telegram = $app->make(TelegramService::class);
$telegram->reply($update, 'Olá!');
```

O `TelegramClient` centraliza:
- Autenticação (token)
- Tratamento de erros (lança `TelegramApiException`)
- Configuração de timeout e headers
- Serialização JSON

---

## Camada de Serviços

Nenhum módulo acessa recursos externos diretamente. Tudo via serviço:

```
Módulo/Comando
     │
     ├─ TelegramService    → envia mensagens, verifica admins
     ├─ PermissionService  → resolve nível de permissão
     ├─ CacheService       → lê/escreve cache
     ├─ LanguageService    → traduz strings
     ├─ ConfigService      → lê configurações
     └─ LoggerService      → registra logs
```

Todos os serviços são registrados como singletons no `Kernel` e resolvidos via `$app->make(ServiceClass::class)`.

---

## Hooks do Sistema (Eventos especiais)

Os seguintes hooks estão disponíveis para módulos modificarem comportamentos:

| Hook | Quando |
|---|---|
| `command.before` | Antes de qualquer comando ser executado |
| `command.after` | Após qualquer comando ser executado |
| `message.received` | Para cada mensagem (inclusive comandos) |

Exemplo — um módulo de logs pode ouvir todos os comandos:

```php
public function getEvents(): array {
    return [
        'command.executed' => [
            function(array $data) {
                $this->logger->info("Comando executado: /{$data['command']}");
            }
        ],
    ];
}
```
