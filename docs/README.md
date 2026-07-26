# ACHI BOT — Documentação

> Framework PHP 8.4 modular para gerenciamento de grupos do Telegram.
> Arquitetura totalmente desacoplada e extensível por plugins.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Princípios do Projeto](#princípios)
3. [Status Atual](#status-atual)
4. [Estrutura de Arquivos](#estrutura-de-arquivos)
5. [Documentação Técnica](#documentação-técnica)
6. [Roadmap Completo](#roadmap)
7. [Como Continuar](#como-continuar)

---

## Visão Geral

Este framework é um **ecossistema de plugins** para bots do Telegram. O núcleo (`Core`) é fixo e nunca precisa ser modificado para adicionar novas funcionalidades. Qualquer recurso novo é implementado como um **módulo independente** que é detectado e carregado automaticamente.

```
Core (imutável)
│
├── Kernel          → inicialização + long polling
├── ModuleLoader    → descoberta automática
├── EventDispatcher → pub/sub de eventos
├── CommandRegistry → registro de comandos
├── Router          → roteamento de updates
│
└── modules/        → qualquer pasta aqui é um módulo
    ├── Help/   Start/   Admin/
    ├── Ban/    Kick/    Mute/    Warn/   Notes/
    ├── Locks/  Filters/ Reports/ Rules/  Welcome/
    ├── Flood/  Captcha/ AntiSpam/ AntiRaid/ Approval/
    └── (novos módulos da Fase 5)
```

**Total atual:** 21 módulos · 53 comandos · 12 listeners de eventos

---

## Princípios

| Princípio | Significado prático |
|---|---|
| **Zero alterações no Core** | Nunca edite `app/Core/` para adicionar comandos |
| **Módulos independentes** | Cada módulo não conhece outros módulos |
| **Descoberta automática** | Soltar uma pasta em `modules/` é suficiente |
| **Sistema de eventos** | Comunicação entre módulos via eventos, não imports |
| **Serviços centralizados** | Nenhum módulo acessa API externa diretamente |
| **Banco de dados isolado** | Nunca SQL dentro de comandos — usar Repository |
| **Sem texto fixo** | Todo texto vem de arquivos de idioma |

---

## Status Atual

```
Fase 1   ████████████████████ 100%  Framework base
Fase 1.5 ████████████████████ 100%  Complemento do framework
Fase 2   ████████████████████ 100%  Módulos de administração (19 commands)
Fase 3   ████████████████████ 100%  Gerenciamento de grupos (12 commands)
Fase 4   ████████████████████ 100%  Anti-abuso (11 commands)
Fase 5   ████████████████░░░░  80%  Recursos avançados (Backup ✅, FedBan ✅, Stats ✅, Painel Web ✅)
```

### ✅ Fase 1 — Framework Base (CONCLUÍDA)

| Componente | Arquivo |
|---|---|
| Application (IoC Container) | `app/Core/Application.php` |
| Kernel | `app/Core/Kernel.php` |
| ModuleLoader | `app/Core/ModuleLoader.php` |
| EventDispatcher | `app/Core/EventDispatcher.php` |
| CommandRegistry | `app/Core/CommandRegistry.php` |
| Router | `app/Core/Router.php` |
| Update (wrapper tipado) | `app/Core/Update.php` |
| Permission (enum 6 níveis) | `app/Core/Permission.php` |
| TelegramClient | `app/Core/Telegram/TelegramClient.php` |
| TelegramService | `app/Core/Services/TelegramService.php` |
| PermissionService | `app/Core/Services/PermissionService.php` |
| LoggerService | `app/Core/Services/LoggerService.php` |
| ConfigService | `app/Core/Services/ConfigService.php` |
| CacheService (filesystem) | `app/Core/Services/CacheService.php` |
| LanguageService (i18n) | `app/Core/Services/LanguageService.php` |
| Pipeline + 6 Middlewares | `app/Core/Middleware/` |
| Eventos tipados | `app/Core/Events/` |
| Módulos: Help, Start, Admin | `modules/Help/`, `modules/Start/`, `modules/Admin/` |

---

### ✅ Fase 1.5 — Complemento do Framework (CONCLUÍDA)

| Componente | Arquivo |
|---|---|
| DatabaseService (PDO) | `app/Core/Services/DatabaseService.php` |
| Connection + QueryBuilder | `app/Core/Database/` |
| MigrationRunner | `app/Core/Database/MigrationRunner.php` |
| Migrations 001–009 | `app/Core/Database/Migrations/` |
| RepositoryInterface | `app/Core/Contracts/RepositoryInterface.php` |
| BaseRepository (abstract) | `app/Core/Repository/BaseRepository.php` |
| SettingsService | `app/Core/Services/SettingsService.php` |
| WebhookHandler | `app/Core/Telegram/WebhookHandler.php` |
| CLI (6 comandos) | `console.php` + `app/Core/Console/` |
| MaintenanceMiddleware | `app/Core/Middleware/MaintenanceMiddleware.php` |
| BlacklistMiddleware | `app/Core/Middleware/BlacklistMiddleware.php` |
| DurationParser | `app/Core/Helper/DurationParser.php` |
| TargetResolver | `app/Core/Helper/TargetResolver.php` |
| Update melhorado (mídia, entities) | `app/Core/Update.php` |

---

### ✅ Fase 2 — Módulos de Administração (CONCLUÍDA)

| Módulo | Commands |
|---|---|
| **Ban** | `/ban` `/tban` `/unban` `/sban` `/banme` |
| **Kick** | `/kick` `/kickme` |
| **Mute** | `/mute` `/tmute` `/unmute` `/muteall` |
| **Warn** | `/warn` `/unwarn` `/resetwarn` `/warns` |
| **Notes** | `/save` `/get` `/clear` `/notes` |

**Total Fase 2:** 5 módulos · 19 commands · 5 services · 4 repositories · 5 migrations

---

### ✅ Fase 3 — Gerenciamento de Grupos (CONCLUÍDA)

| Módulo | Commands |
|---|---|
| **Locks** | `/lock <tipo>` `/unlock <tipo\|all>` `/locks` |
| **Filters** | `/filter <palavra> <resp>` `/stop <palavra>` `/filters` |
| **Reports** | `/report [motivo]` |
| **Rules** | `/setrules <texto>` `/rules` `/clearrules` |
| **Welcome** | `/welcome on\|off\|msg` `/goodbye on\|off\|msg` `/cleanwelcome on\|off` |

**Total Fase 3:** 5 módulos · 12 commands · 3 services · 1 repository · 1 migration

---

### ✅ Fase 4 — Anti-Abuso (CONCLUÍDA)

| Módulo | Commands | Automático |
|---|---|---|
| **Flood** | `/setflood N` `/setfloodmode action` `/flood` | `message.received` → conta msgs/usuário; aplica ação ao atingir limite |
| **Captcha** | `/captcha on\|off\|button\|math\|text` | `user.joined` → muta + envia desafio; `callback.received` / `message.received` → valida |
| **AntiSpam** | `/antispam on\|off` | `user.joined` → checa CAS; `message.received` → detecta links excessivos e repetição |
| **AntiRaid** | `/antiraid on\|off\|N` | `user.joined` → detecta pico; ativa modo raid automático com ban/kick/mute |
| **Approval** | `/approval on\|off` `/approve` `/deny` | `user.joined` → muta novo membro; admins aprovam/negam |

**Total Fase 4:** 5 módulos · 11 commands · 5 services · 8 event listeners · estado via CacheService

---

### ⏳ Fase 5 — Recursos Avançados (EM ANDAMENTO)

| Sub-fase | Conteúdo | Status |
|---|---|---|
| 5.1 | FedBan — `/newfed` `/joinfed` `/leavefed` `/fban` `/unfban` `/fedinfo` | ✅ |
| 5.2 | Backup — `/backup` `/restore` | ✅ |
| 5.3 | Stats — `/stats` `/top` | ✅ |
| 5.4 | Painel Web PHP puro em `bot/public/dashboard/` | ✅ |
| 5.5 | Plugins via Composer | ⏳ |
| 5.6 | API Pública com token | ✅ |

---

## Estrutura de Arquivos

```
bot/
├── run.php                            # Entry point — long polling
├── console.php                        # Entry point — CLI
├── composer.json
│
├── app/
│   ├── bootstrap/app.php
│   ├── config/app.php, telegram.php
│   └── Core/                          # ← NUNCA modificar para features
│       ├── Application.php, Kernel.php, ModuleLoader.php
│       ├── EventDispatcher.php, CommandRegistry.php, Router.php
│       ├── Update.php, Permission.php
│       ├── Contracts/, Services/, Database/
│       ├── Repository/, Helper/, Telegram/
│       ├── Middleware/, Events/, Console/
│
├── modules/
│   │
│   │  — Fase 1 —
│   ├── Help/      ✅ /help
│   ├── Start/     ✅ /start
│   ├── Admin/     ✅ /adminlist /pin /unpin
│   │
│   │  — Fase 2 —
│   ├── Ban/       ✅ /ban /tban /unban /sban /banme
│   ├── Kick/      ✅ /kick /kickme
│   ├── Mute/      ✅ /mute /tmute /unmute /muteall
│   ├── Warn/      ✅ /warn /unwarn /resetwarn /warns
│   ├── Notes/     ✅ /save /get /clear /notes + #hashtagListener
│   │
│   │  — Fase 3 —
│   ├── Locks/     ✅ /lock /unlock /locks
│   ├── Filters/   ✅ /filter /stop /filters
│   ├── Reports/   ✅ /report
│   ├── Rules/     ✅ /setrules /rules /clearrules
│   ├── Welcome/   ✅ /welcome /goodbye /cleanwelcome
│   │
│   │  — Fase 4 —
│   ├── Flood/     ✅ /setflood /setfloodmode /flood
│   ├── Captcha/   ✅ /captcha (button/math/text)
│   ├── AntiSpam/  ✅ /antispam (CAS + links + repetição)
│   ├── AntiRaid/  ✅ /antiraid (modo raid automático)
│   ├── Approval/  ✅ /approval /approve /deny
│   │
│   │  — Fase 5 —
│   ├── Backup/    ✅ /backup /restore
│   ├── FedBan/    ✅ /newfed /joinfed /leavefed /fban /unfban /fedinfo
│   └── Stats/     ✅ /stats /top
│
├── public/webhook.php
├── logs/ (telegram.log, error.log, security.log)
└── storage/cache/
```

---

## Documentação Técnica

- [Arquitetura](architecture.md)
- [Módulos](modules.md)
- [Serviços](services.md)
- [Eventos](events.md)
- [Permissões](permissions.md)
- [API REST](rest-api.md)
- [Roadmap completo](roadmap.md)

---

## Como Continuar

### Fase 5 — concluída

**Concluídos:** Backup ✅ · FedBan ✅ · Stats ✅ · Painel Web ✅ · Plugins Composer ✅ · API Pública ✅

- Dashboard React em `artifacts/dashboard/`, servido na raiz, com token bearer.
- API REST em `artifacts/api-server`, definida por OpenAPI em `lib/api-spec/openapi.yaml`.
- Descoberta de plugins Composer pelo `ModuleLoader`, incluindo comandos de console opcionais.
- Consulte [API Pública](public-api.md) para endpoints e configuração.

### Estrutura de um novo módulo

```
modules/NovoModulo/
├── module.php          → return new \Modules\NovoModulo\NovoModuloModule();
├── NovoModuloModule.php
├── Commands/
│   └── NovoComando.php
├── Services/
│   └── NovoService.php
├── Repository/
│   └── NovoRepository.php  → extends BaseRepository
└── Language/
    ├── en_US.php
    └── pt_BR.php
```

### Helpers disponíveis para Commands

```php
// Resolver alvo (reply / @mention / ID numérico)
$target = TargetResolver::resolve($update, $args);
// Retorna: ['id' => int, 'name' => string, 'remaining_args' => string] ou null

// Parsear duração ("1d", "2h30m", "1w")
[$seconds, $remaining] = DurationParser::parse($args);
$humanReadable = DurationParser::format($seconds); // "1d 2h"

// Verificar se é admin
$telegram->isAdmin($chatId, $userId); // bool

// Settings por grupo (com cache em memória)
$settings->get($chatId, 'Modulo', 'chave', default: valor);
$settings->set($chatId, 'Modulo', 'chave', valor);

// Cache (estado temporário, sem DB)
$cache->get($key);
$cache->set($key, $value, $ttl);
$cache->increment($key, 1, $ttl);
```
