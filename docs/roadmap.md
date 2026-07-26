# Roadmap Completo — Telegram Group Manager PHP

> **Regra fundamental:** Toda a estrutura do framework deve estar sólida e funcional
> antes de iniciar qualquer módulo de feature. Módulos construídos sobre uma base
> incompleta resultam em retrabalho e acoplamento indesejado.

---

## Status Geral

```
Fase 1   ████████████████████ 100%  Framework base
Fase 1.5 ████████████████████ 100%  Complemento do framework
Fase 2   ████████████████████ 100%  Módulos de administração (19 commands)
Fase 3   ████████████████████ 100%  Gerenciamento de grupos (12 commands)
Fase 4   ████████████████████ 100%  Anti-abuso (11 commands)
Fase 5   ████████████░░░░░░░░  60%  Recursos avançados (Backup ✅, FedBan ✅, Stats ✅)
```

---

## ✅ Fase 1 — Framework Base (CONCLUÍDA)

### Core
- [x] `Application` — IoC container (singleton pattern, bind/singleton/instance/make)
- [x] `Kernel` — bootstrap + loop de long polling
- [x] `ModuleLoader` — auto-descoberta de módulos em `modules/`
- [x] `EventDispatcher` — pub/sub (on/emit/off, wildcard `*`)
- [x] `CommandRegistry` — registro e dispatch de comandos com pipeline
- [x] `Router` — roteamento de updates do Telegram → eventos e comandos
- [x] `Update` — wrapper tipado com acessores para todos os campos
- [x] `Permission` — enum com 6 níveis e método `isAtLeast()`

### Contratos (Interfaces)
- [x] `ModuleInterface` — `boot()`, `register()`, `getCommands()`, `getEvents()`
- [x] `CommandInterface` — `getCommand()`, `getPermission()`, `getMiddleware()`, `handle()`
- [x] `EventInterface` — `getName()`, `getData()`
- [x] `MiddlewareInterface` — `handle(Update, callable $next)`

### Telegram
- [x] `TelegramClient` — único ponto de acesso à API (cURL, throw on error)
- [x] `TelegramApiException` — exceção tipada para erros da API
- [x] Métodos: sendMessage, editMessageText, deleteMessage, forwardMessage
- [x] Métodos: banChatMember, unbanChatMember, restrictChatMember, promoteChatMember
- [x] Métodos: getChat, getChatMember, getChatAdministrators, getChatMemberCount
- [x] Métodos: answerCallbackQuery, answerInlineQuery, request (genérico)

### Serviços
- [x] `LoggerService` — console + arquivos (telegram.log, error.log, security.log)
- [x] `ConfigService` — dot notation, cache em memória
- [x] `CacheService` — filesystem (get/set/has/delete/increment/flush)
- [x] `LanguageService` — por módulo, fallback en_US, substituições `:placeholder`
- [x] `TelegramService` — reply/send/isAdmin/isCreator/isBotAdmin/mentionUser/formatUser
- [x] `PermissionService` — getPermission/can/isOwner

### Middleware
- [x] `Pipeline` — onion model via `array_reduce`
- [x] `PermissionMiddleware` — verifica nível mínimo
- [x] `FloodMiddleware` — rate limit por usuário/minuto
- [x] `GroupOnlyMiddleware` — bloqueia fora de grupos
- [x] `PrivateOnlyMiddleware` — bloqueia fora de privado

### Eventos do Core
- [x] `message.received` — toda mensagem
- [x] `user.joined` — membro entrou
- [x] `user.left` — membro saiu
- [x] `callback.received` — botão inline clicado
- [x] `member.updated` — status de membro alterado
- [x] `command.before` / `command.after` / `command.executed`

### Módulos iniciais
- [x] `Help` — /help lista todos os comandos registrados
- [x] `Start` — /start boas-vindas com descrição do bot
- [x] `Admin` — /adminlist, /pin, /unpin

### Infraestrutura
- [x] Composer PSR-4 autoloading
- [x] Long polling funcional
- [x] Workflow "Telegram Bot" configurado no Replit
- [x] Sistema de logs em arquivos
- [x] Cache filesystem em `storage/cache/`
- [x] Documentação completa em `docs/`

---

## ✅ Fase 1.5 — Complemento do Framework (CONCLUÍDA)

### 1.5.1 — DatabaseService e Banco de Dados ✅

```
app/Core/
├── Services/
│   └── DatabaseService.php      ✅
├── Database/
│   ├── Connection.php           ✅
│   ├── QueryBuilder.php         ✅
│   ├── Migration.php            ✅
│   ├── MigrationRunner.php      ✅
│   └── Migrations/
│       ├── 001CreateGroupsTable.php      ✅
│       ├── 002CreateUsersTable.php       ✅
│       ├── 003CreateUserRolesTable.php   ✅
│       ├── 004CreateSettingsTable.php    ✅
│       ├── 005CreateBansTable.php        ✅
│       ├── 006CreateMutesTable.php       ✅
│       ├── 007CreateWarnsTable.php       ✅
│       └── 008CreateNotesTable.php       ✅
└── Contracts/
    └── RepositoryInterface.php  ✅
```

- [x] `DatabaseService` com PDO (SQLite para dev, PostgreSQL para prod)
- [x] `QueryBuilder` fluent simples (select/insert/update/delete/where)
- [x] `MigrationRunner` que roda migrations na inicialização do Kernel
- [x] Migrations 001–008 (groups, users, user_roles, settings, bans, mutes, warns, notes)
- [x] `RepositoryInterface` com métodos base (find, findBy, save, delete)
- [x] `BaseRepository` abstract — `app/Core/Repository/BaseRepository.php`
- [x] `Kernel` atualizado para inicializar o banco antes dos módulos

### 1.5.2 — SettingsService ✅

- [x] `SettingsService` com cache em memória (evitar N+1 queries)
- [x] Migration da tabela `group_settings` (migration 004)
- [x] Registro no `Kernel`

### 1.5.3 — WebhookHandler ✅

- [x] `app/Core/Telegram/WebhookHandler.php`
- [x] `public/webhook.php` como entry point

### 1.5.4 — CLI ✅

```bash
php console.php migrate               # roda migrations pendentes
php console.php migrate:status        # status das migrations
php console.php webhook:set           # registra webhook
php console.php webhook:delete        # remove webhook
php console.php cache:clear           # limpa cache
php console.php modules:list          # lista módulos carregados
```

### 1.5.5 — Novos Middlewares ✅

- [x] `MaintenanceMiddleware` — bloqueia todos os updates durante manutenção
- [x] `BlacklistMiddleware` — bloqueia usuários globalmente banidos do bot

### 1.5.6 — Helpers ✅

- [x] `Helper/DurationParser` — converte "1d", "2h30m", "1w" em segundos
- [x] `Helper/TargetResolver` — resolve alvo (reply / @mention / ID numérico)

### 1.5.7 — Update melhorado ✅

- [x] Suporte a `voice`, `photo`, `video`, `sticker`, `document`, `audio`, `animation`
- [x] Suporte a `poll`, `location`, `contact`
- [x] `getEntities()` / `getCaptionEntities()` / `getCaption()`
- [x] `getMentionedUserIds()` / `getMentionedUsers()` / `getMentionedUsernames()`
- [x] `hasMedia()` / `isForward()`

---

## ✅ Fase 2 — Módulos de Administração (CONCLUÍDA)

### 2.1 — Ban ✅

```
modules/Ban/
├── BanModule.php               ✅
├── module.php                  ✅
├── Services/BanService.php     ✅  ban(), unban()
├── Repository/BanRepository.php ✅
├── Commands/
│   ├── BanCommand.php          ✅  /ban [reply|id] [motivo]
│   ├── TbanCommand.php         ✅  /tban [reply|id] <duração> [motivo]
│   ├── UnbanCommand.php        ✅  /unban [reply|id]
│   ├── SbanCommand.php         ✅  /sban [reply|id] [motivo] — ban silencioso
│   └── BanmeCommand.php        ✅  /banme — auto-ban
└── Language/ en_US.php, pt_BR.php ✅
```

**Banco:** migration `005CreateBansTable.php` ✅
**Eventos emitidos:** `member.banned`, `member.unbanned`

---

### 2.2 — Kick ✅

```
modules/Kick/
├── KickModule.php              ✅
├── module.php                  ✅
├── Commands/
│   ├── KickCommand.php         ✅  /kick [reply|id]
│   └── KickmeCommand.php       ✅  /kickme — auto-kick
└── Language/ en_US.php, pt_BR.php ✅
```

*(Kick não persiste no banco — ban + unban imediato)*

---

### 2.3 — Mute ✅

```
modules/Mute/
├── MuteModule.php              ✅
├── module.php                  ✅
├── Services/MuteService.php    ✅  mute(), unmute()
├── Repository/MuteRepository.php ✅
├── Commands/
│   ├── MuteCommand.php         ✅  /mute [reply|id] [motivo]
│   ├── TmuteCommand.php        ✅  /tmute [reply|id] <duração> [motivo]
│   ├── UnmuteCommand.php       ✅  /unmute [reply|id]
│   └── MuteallCommand.php      ✅  /muteall [off] — altera permissões padrão do grupo
└── Language/ en_US.php, pt_BR.php ✅
```

**Banco:** migration `006CreateMutesTable.php` ✅
**Eventos emitidos:** `member.muted`, `member.unmuted`

---

### 2.4 — Warn ✅

```
modules/Warn/
├── WarnModule.php              ✅
├── module.php                  ✅
├── Services/WarnService.php    ✅  warn(), unwarn(), resetWarns(), getWarns()
├── Repository/WarnRepository.php ✅
├── Commands/
│   ├── WarnCommand.php         ✅  /warn [reply|id] [motivo]
│   ├── UnwarnCommand.php       ✅  /unwarn [reply|id]
│   ├── ResetwarnCommand.php    ✅  /resetwarn [reply|id]
│   └── WarnsCommand.php        ✅  /warns [reply|id]
└── Language/ en_US.php, pt_BR.php ✅
```

**Banco:** migration `007CreateWarnsTable.php` ✅
**Settings por grupo:**
```
warn.max_warns       → 3 (padrão)
warn.warn_action     → 'ban' | 'kick' | 'mute' | 'tmute'
warn.warn_mute_time  → 3600 (se ação for tmute)
```
**Eventos emitidos:** `member.warned`, `member.warn_limit`

---

### 2.5 — Notes ✅

```
modules/Notes/
├── NotesModule.php             ✅
├── module.php                  ✅
├── Services/NotesService.php   ✅  save(), get(), listAll(), delete(), sendNote()
├── Repository/NotesRepository.php ✅
├── Events/HashtagNoteListener  ✅  detecta #nomeDaNota no texto
├── Commands/
│   ├── SaveCommand.php         ✅  /save <nome> <conteúdo>  ou reply
│   ├── GetCommand.php          ✅  /get <nome>
│   ├── ClearCommand.php        ✅  /clear <nome>
│   └── NotesListCommand.php    ✅  /notes
└── Language/ en_US.php, pt_BR.php ✅
```

**Banco:** migration `008CreateNotesTable.php` ✅
**Eventos emitidos:** `note.saved`, `note.deleted`
**Ouve eventos:** `message.received` (para detectar `#nomeDaNota` no texto)

---

### Resumo dos comandos da Fase 2

| Comando | Módulo | Permissão | Descrição |
|---|---|---|---|
| `/ban` | Ban | Admin | Bane permanentemente |
| `/tban` | Ban | Admin | Bane temporariamente (ex: `/tban 1d motivo`) |
| `/unban` | Ban | Admin | Remove o ban |
| `/sban` | Ban | Admin | Ban silencioso (sem notificação) |
| `/banme` | Ban | User | Auto-ban |
| `/kick` | Kick | Admin | Expulsa do grupo |
| `/kickme` | Kick | User | Auto-kick |
| `/mute` | Mute | Admin | Silencia permanentemente |
| `/tmute` | Mute | Admin | Silencia temporariamente (ex: `/tmute 2h motivo`) |
| `/unmute` | Mute | Admin | Remove o silêncio |
| `/muteall` | Mute | Admin | Silencia todos (`/muteall off` para desfazer) |
| `/warn` | Warn | Admin | Adverte usuário (limite → ação automática) |
| `/unwarn` | Warn | Admin | Remove última advertência |
| `/resetwarn` | Warn | Admin | Remove todas as advertências |
| `/warns` | Warn | User | Lista advertências |
| `/save` | Notes | Admin | Salva nota (`/save nome conteúdo` ou reply) |
| `/get` | Notes | User | Exibe nota |
| `/clear` | Notes | Admin | Remove nota |
| `/notes` | Notes | User | Lista todas as notas |

---

## ✅ Fase 3 — Gerenciamento de Grupos (CONCLUÍDA)

> **Pré-requisito:** Fase 2 ✅

### 3.1 — Locks ✅

```
modules/Locks/
├── LockModule.php              ✅
├── module.php                  ✅
├── Commands/
│   ├── LockCommand.php         ✅  /lock <tipo>
│   ├── UnlockCommand.php       ✅  /unlock <tipo> | /unlock all
│   └── LocksCommand.php        ✅  /locks — lista locks ativos
├── Events/
│   └── LockEnforcer.php        ✅  listener de message.received
├── Services/
│   └── LockService.php         ✅  lock(), unlock(), unlockAll(), isLocked()
└── Language/ en_US.php, pt_BR.php ✅
```

**Tipos de lock:** `text`, `media`, `sticker`, `gif`, `url`, `forward`, `poll`, `photo`, `video`, `voice`, `button`, `inline`, `contact`, `location`, `game`, `all`

**Armazenamento:** `SettingsService` — chave `Locks.locks` (array JSON por grupo)
**Ouve eventos:** `message.received` → detecta tipo → deleta se bloqueado
**Admins são isentos** dos locks automaticamente

---

### 3.2 — Filters ✅

```
modules/Filters/
├── FiltersModule.php             ✅
├── module.php                    ✅
├── Commands/
│   ├── FilterCommand.php         ✅  /filter <palavra> <resposta> | reply
│   ├── StopCommand.php           ✅  /stop <palavra>
│   └── FiltersCommand.php        ✅  /filters — lista filtros
├── Events/
│   └── FilterListener.php        ✅  listener de message.received
├── Services/
│   └── FilterService.php         ✅  save(), delete(), listAll(), checkAndRespond()
├── Repository/
│   └── FilterRepository.php      ✅
└── Language/ en_US.php, pt_BR.php ✅
```

**Banco:** migration `009CreateFiltersTable.php` ✅ — tabela `filters(chat_id, keyword, response, created_by)`
**Ouve eventos:** `message.received` → verifica se texto contém keyword → responde
**Ignora comandos** para evitar conflito com handlers de comando

---

### 3.3 — Reports ✅

```
modules/Reports/
├── ReportsModule.php             ✅
├── module.php                    ✅
├── Commands/
│   └── ReportCommand.php         ✅  /report [motivo] — reply obrigatório
└── Language/ en_US.php, pt_BR.php ✅
```

**Comportamento:**
- Exige reply a uma mensagem
- Não permite reportar bots ou admins
- Notifica cada admin via DM com link para a mensagem (em supergrupos)
- Informa quantos admins foram notificados com sucesso

---

### 3.4 — Rules ✅

```
modules/Rules/
├── RulesModule.php               ✅
├── module.php                    ✅
├── Commands/
│   ├── SetrulesCommand.php       ✅  /setrules <texto> | reply
│   ├── RulesCommand.php          ✅  /rules
│   └── ClearrulesCommand.php     ✅  /clearrules
└── Language/ en_US.php, pt_BR.php ✅
```

**Armazenamento:** `SettingsService` — chave `Rules.text` por grupo (sem tabela própria)

---

### 3.5 — Welcome / Goodbye ✅

```
modules/Welcome/
├── WelcomeModule.php             ✅
├── module.php                    ✅
├── Commands/
│   ├── WelcomeCommand.php        ✅  /welcome on|off|<mensagem>
│   ├── GoodbyeCommand.php        ✅  /goodbye on|off|<mensagem>
│   └── CleanwelcomeCommand.php   ✅  /cleanwelcome on|off
├── Events/
│   ├── JoinListener.php          ✅  ouve user.joined
│   └── LeaveListener.php         ✅  ouve user.left
├── Services/
│   └── WelcomeService.php        ✅  sendWelcome(), sendGoodbye(), getSettings()
└── Language/ en_US.php, pt_BR.php ✅
```

**Armazenamento:** `SettingsService` — chaves `Welcome.*` por grupo
**Variáveis de template:** `{first}`, `{last}`, `{full}`, `{username}`, `{mention}`, `{id}`, `{count}`, `{chatname}`
**CleanWelcome:** apaga a mensagem de boas-vindas anterior ao novo membro entrar
**Bots são ignorados** nos eventos joined/left

### Resumo dos comandos da Fase 3

| Comando | Módulo | Permissão | Descrição |
|---|---|---|---|
| `/lock <tipo>` | Locks | Admin | Ativa um lock de tipo de mensagem |
| `/unlock <tipo\|all>` | Locks | Admin | Remove lock(s) |
| `/locks` | Locks | User | Lista locks ativos |
| `/filter <palavra> <resp>` | Filters | Admin | Cria filtro automático |
| `/stop <palavra>` | Filters | Admin | Remove filtro |
| `/filters` | Filters | User | Lista filtros ativos |
| `/report [motivo]` | Reports | User | Reporta mensagem aos admins (reply) |
| `/setrules <texto>` | Rules | Admin | Define regras do grupo |
| `/rules` | Rules | User | Exibe regras |
| `/clearrules` | Rules | Admin | Remove regras |
| `/welcome on\|off\|msg` | Welcome | Admin | Configura boas-vindas |
| `/goodbye on\|off\|msg` | Welcome | Admin | Configura despedida |
| `/cleanwelcome on\|off` | Welcome | Admin | Apaga welcome anterior |

---

## ✅ Fase 4 — Anti-Abuso (CONCLUÍDA)

> **Pré-requisito:** Fase 3 ✅

### 4.1 — Flood ✅

```
modules/Flood/
├── FloodModule.php              ✅
├── module.php                   ✅
├── Commands/
│   ├── SetfloodCommand.php      ✅  /setflood N (0 = desativar)
│   ├── SetfloodmodeCommand.php  ✅  /setfloodmode warn|mute|kick|ban|tban|tmute
│   └── FloodCommand.php         ✅  /flood — status atual
├── Events/
│   └── FloodChecker.php         ✅  ouve message.received; admins isentos
└── Services/
    └── FloodService.php         ✅  janela deslizante via CacheService TTL
```

**Settings por grupo:** `limit` (0), `window` (10s), `action` (mute), `mute_time` (600s)
**Armazenamento:** CacheService — chave `flood:{chatId}:{userId}` com TTL = janela

---

### 4.2 — Captcha ✅

```
modules/Captcha/
├── CaptchaModule.php                    ✅
├── module.php                           ✅
├── Commands/
│   └── CaptchaCommand.php               ✅  /captcha on|off|button|math|text
├── Events/
│   ├── NewMemberCaptcha.php             ✅  ouve user.joined — muta + envia desafio
│   ├── CaptchaAnswerListener.php        ✅  ouve message.received — valida math/text
│   └── CaptchaCallbackListener.php      ✅  ouve callback.received — valida button
└── Services/
    └── CaptchaService.php               ✅  estado via CacheService (answer, msg_id, expires)
```

**Tipos:** `button` (teclado inline), `math` (conta aritmética), `text` (palavra aleatória)
**Timeout:** configável por grupo (padrão 90s); timeout → expulsa o usuário
**Armazenamento:** CacheService — prefixo `captcha:{chatId}:{userId}:`

---

### 4.3 — AntiSpam ✅

```
modules/AntiSpam/
├── AntiSpamModule.php                   ✅
├── module.php                           ✅
├── Commands/
│   └── AntispamCommand.php              ✅  /antispam on|off
├── Events/
│   ├── CasChecker.php                   ✅  ouve user.joined — checa CAS API
│   └── SpamChecker.php                  ✅  ouve message.received — links + repetição
└── Services/
    └── SpamDetector.php                 ✅  CAS cache 6h/24h; detecta links e repetição
```

**CAS:** `api.cas.chat` — bane automaticamente usuários listados no Combot Anti-Spam
**Spam:** excesso de links (> 3 por msg) ou mesma mensagem ≥ 3x em 30s → deleta

---

### 4.4 — AntiRaid ✅

```
modules/AntiRaid/
├── AntiRaidModule.php                   ✅
├── module.php                           ✅
├── Commands/
│   └── AntiRaidCommand.php              ✅  /antiraid on|off|N|status
├── Events/
│   └── RaidDetector.php                 ✅  ouve user.joined — detecta pico
└── Services/
    └── RaidDetectorService.php          ✅  contagem via CacheService; modo raid com TTL
```

**Modo Raid:** ativado quando N entradas ocorrem dentro da janela configurada
**Settings:** `threshold` (10), `window` (60s), `action` (ban), `duration` (15 min)
**Armazenamento:** CacheService — `raid:count:{chatId}`, `raid:active:{chatId}`

---

### 4.5 — Approval ✅

```
modules/Approval/
├── ApprovalModule.php                   ✅
├── module.php                           ✅
├── Commands/
│   ├── ApprovalCommand.php              ✅  /approval on|off
│   ├── ApproveCommand.php               ✅  /approve [reply|@user|ID]
│   └── DenyCommand.php                  ✅  /deny [reply|@user|ID]
├── Events/
│   └── NewMemberApproval.php            ✅  ouve user.joined — muta + notifica admins
└── Services/
    └── ApprovalService.php              ✅  restrict/approve/deny via TelegramClient
```

**Comportamento:** novo membro entra silenciado; admins usam /approve (libera) ou /deny (bane)

### Resumo dos comandos da Fase 4

| Comando | Módulo | Permissão | Descrição |
|---|---|---|---|
| `/setflood N` | Flood | Admin | Define limite (0 = desativar) |
| `/setfloodmode action` | Flood | Admin | Define ação (warn/mute/kick/ban/tban/tmute) |
| `/flood` | Flood | User | Exibe configurações atuais |
| `/captcha on\|off\|button\|math\|text` | Captcha | Admin | Configura captcha |
| `/antispam on\|off` | AntiSpam | Admin | Ativa/desativa anti-spam |
| `/antiraid on\|off\|N` | AntiRaid | Admin | Configura anti-raid |
| `/approval on\|off` | Approval | Admin | Ativa/desativa modo de aprovação |
| `/approve [alvo]` | Approval | Admin | Aprova membro silenciado |
| `/deny [alvo]` | Approval | Admin | Nega e remove membro |

---

## ⏳ Fase 5 — Recursos Avançados (EM ANDAMENTO)

> **Pré-requisito:** Fases 2, 3 e 4 completas

### ✅ 5.1 — Federação (FedBan)

```
modules/FedBan/
├── FedBanModule.php              ✅
├── module.php                    ✅
├── Commands/
│   ├── NewfedCommand.php         ✅  /newfed <nome>   (privado)
│   ├── JoinfedCommand.php        ✅  /joinfed <fed_id>
│   ├── LeavefedCommand.php       ✅  /leavefed
│   ├── FbanCommand.php           ✅  /fban — propaga ban a todos os grupos
│   ├── UnfbanCommand.php         ✅  /unfban
│   └── FedInfoCommand.php        ✅  /fedinfo
├── Repository/FedRepository.php  ✅
└── Services/FedService.php       ✅
```

**Banco:** migration `010CreateFederationsTable.php` — tabelas `federations`, `fed_chats`, `fed_bans`
**Comportamento:** `/fban` e `/unfban` propagam o ban/unban automaticamente a todos os grupos membros.

---

### ✅ 5.2 — Backup

```
modules/Backup/
├── BackupModule.php              ✅
├── module.php                    ✅
├── Commands/
│   ├── BackupCommand.php         ✅  /backup — exporta JSON como documento
│   └── RestoreCommand.php        ✅  /restore — restaura a partir de JSON (reply ao arquivo)
└── Services/BackupService.php    ✅
```

**O backup inclui:** settings de todos os módulos, notas, filtros, regras, warns, bans e mutes.
**TelegramClient:** adicionados `sendDocumentContent()`, `getFile()` e `downloadFile()`.

---

### ✅ 5.3 — Estatísticas

```
modules/Stats/
├── StatsModule.php               ✅
├── module.php                    ✅
├── Commands/
│   ├── StatsCommand.php          ✅  /stats — total de mensagens e usuários
│   └── TopCommand.php            ✅  /top — top 10 mais ativos (🥇🥈🥉)
├── Events/
│   └── MessageStatsListener.php  ✅  ouve message.received — incremento atômico
└── Repository/StatsRepository.php ✅
```

**Banco:** migration `011CreateMessageStatsTable.php` — tabela `message_stats`
**Upsert:** `INSERT OR REPLACE` (SQLite) / `ON CONFLICT DO UPDATE` (PostgreSQL)

---

### ✅ 5.4 — Painel Web

Interface web PHP pura para gerenciamento dos grupos. Sem build, sem Node.js — funciona em hospedagem compartilhada.

```
bot/public/dashboard/
├── index.php              ✅  Entrada + roteamento + layout + auth (sessão PHP)
├── config.php             ✅  Hash de senha e caminho do banco
├── .htaccess              ✅  Bloqueia acesso a config.php e pages/
└── pages/
    ├── overview.php       ✅  Visão geral — cards com totais + tabelas recentes
    ├── groups.php         ✅  Lista de grupos com contagem de bans/warns/notas
    ├── bans.php           ✅  Bans com filtro ativo/inativo/todos + busca
    ├── warns.php          ✅  Advertências + destaque de usuários com múltiplas
    ├── notes.php          ✅  Notas por grupo com busca e filtro rápido
    ├── stats.php          ✅  Ranking de mensagens com barra de progresso
    └── fedbans.php        ✅  Federações + grupos membros + lista de fedbans
```

**Acesso:** `https://seudominio.com/dashboard/`
**Autenticação:** senha única configurada em `config.php`
**Banco:** lê o mesmo `storage/database.sqlite` do bot (ou PostgreSQL via `DATABASE_URL`)

**Alterar senha:**
```bash
php -r "echo password_hash('nova_senha', PASSWORD_DEFAULT);"
# Cole o resultado em config.php → DASHBOARD_PASSWORD_HASH
```

---

### 5.5 — Plugins Externos (via Composer)

O `ModuleLoader` detecta pacotes do tipo `telegram-bot-module` automaticamente.

---

### 5.6 — API Pública

REST API com autenticação por token para integração com sistemas externos.

---

## Sequência de Desenvolvimento

```
✅ Fase 1    → Framework base
✅ Fase 1.5  → DatabaseService, SettingsService, CLI, WebhookHandler
✅ Fase 2    → Ban, Kick, Mute, Warn, Notes (19 commands + 5 módulos)
✅ Fase 3.1  → Locks
✅ Fase 3.2  → Filters
✅ Fase 3.3  → Reports
✅ Fase 3.4  → Rules
✅ Fase 3.5  → Welcome/Goodbye
✅ Fase 4.1  → Flood (setflood/setfloodmode/flood)
✅ Fase 4.2  → Captcha (button/math/text)
✅ Fase 4.3  → AntiSpam (CAS + links + repetição)
✅ Fase 4.4  → AntiRaid (modo raid automático)
✅ Fase 4.5  → Approval (approve/deny)
↓
✅ Fase 5.1  → FedBan (/newfed /joinfed /leavefed /fban /unfban /fedinfo)
✅ Fase 5.2  → Backup (/backup /restore)
✅ Fase 5.3  → Stats (/stats /top)
✅ Fase 5.4  → Painel Web (PHP puro em bot/public/dashboard/)
⏳ Fase 5.5  → Plugins Composer
⏳ Fase 5.6  → API Pública
```

---

## Convenções a seguir em todos os módulos

```
1. Namespace: Modules\NomeModulo\
2. module.php retorna apenas: return new \Modules\NomeModulo\NomeModuloModule();
3. Todo texto vem de Language/pt_BR.php e Language/en_US.php
4. Todo acesso a dados vai por Repository (nunca SQL direto em Command)
5. Toda lógica de negócio vai em Service (nunca em Command)
6. Commands são controllers: validam input, chamam Service, respondem
7. Comunicação entre módulos EXCLUSIVAMENTE via EventDispatcher
8. Nenhum módulo importa diretamente outro módulo
9. Configurações por grupo via SettingsService (nunca hardcoded)
10. Todas as ações administrativas são logadas em security.log
```
