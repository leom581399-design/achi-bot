# Criando Módulos

## Estrutura de um módulo

Todo módulo segue esta estrutura:

```
modules/
└── NomeDoModulo/
    ├── module.php              # Obrigatório — retorna instância do módulo
    ├── NomeDoModuloModule.php  # Classe principal (implements ModuleInterface)
    ├── NomeCommand.php         # Um arquivo por comando
    ├── AnotherCommand.php
    ├── config.php              # Opcional — configurações padrão do módulo
    └── Language/               # Opcional — arquivos de idioma
        ├── en_US.php
        └── pt_BR.php
```

---

## Passo a passo: criar um módulo do zero

### 1. Criar a pasta

```
bot/modules/MeuModulo/
```

### 2. Criar a classe do módulo

```php
// bot/modules/MeuModulo/MeuModuloModule.php
<?php
declare(strict_types=1);

namespace Modules\MeuModulo;

use App\Core\Application;
use App\Core\Contracts\ModuleInterface;
use App\Core\Services\LanguageService;

class MeuModuloModule implements ModuleInterface
{
    private Application $app;

    public function getName(): string        { return 'MeuModulo'; }
    public function getVersion(): string     { return '1.0.0'; }
    public function getDependencies(): array { return []; }  // ou ['OutroModulo']

    public function boot(Application $app): void
    {
        $this->app = $app;

        // Carregar idiomas (se tiver Language/)
        $app->make(LanguageService::class)->load('MeuModulo', __DIR__ . '/Language');
    }

    public function register(Application $app): void
    {
        // Registrar serviços específicos do módulo no container (opcional)
        // $app->singleton(MeuRepository::class, fn() => new MeuRepository());
    }

    public function getCommands(): array
    {
        return [
            new MeuComandoCommand($this->app),
            // new OutroComandoCommand($this->app),
        ];
    }

    public function getEvents(): array
    {
        return [
            'user.joined' => [
                fn(array $data) => $this->onUserJoined($data),
            ],
        ];
    }

    private function onUserJoined(array $data): void
    {
        // Reagir ao evento de entrada de usuário
    }
}
```

### 3. Criar o entrypoint do módulo

```php
// bot/modules/MeuModulo/module.php
<?php
declare(strict_types=1);

return new \Modules\MeuModulo\MeuModuloModule();
```

### 4. Criar um comando

```php
// bot/modules/MeuModulo/MeuComandoCommand.php
<?php
declare(strict_types=1);

namespace Modules\MeuModulo;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Middleware\GroupOnlyMiddleware;
use App\Core\Middleware\PermissionMiddleware;
use App\Core\Permission;
use App\Core\Services\TelegramService;
use App\Core\Update;

class MeuComandoCommand implements CommandInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    // O texto após a barra: /meucomando
    public function getCommand(): string     { return 'meucomando'; }

    // Aparece no /help
    public function getDescription(): string { return 'Descrição do meu comando'; }

    // Permissão mínima para usar
    public function getPermission(): Permission { return Permission::User; }

    // Middlewares aplicados antes de handle()
    public function getMiddleware(): array
    {
        return [
            new GroupOnlyMiddleware($this->app),
            new PermissionMiddleware($this->app, Permission::Administrator),
        ];
    }

    public function handle(Update $update, Application $app): void
    {
        $telegram = $app->make(TelegramService::class);

        // Verificar se há resposta a uma mensagem
        $reply = $update->getReplyToMessage();
        if ($reply === null) {
            $telegram->reply($update, '❌ Responda a uma mensagem para usar este comando.');
            return;
        }

        // Obter argumentos: /meucomando argumento1 argumento2
        $args = $update->getCommandArgs(); // string com tudo após o comando

        // Fazer algo...
        $telegram->reply($update, "✅ Comando executado com args: {$args}");
    }
}
```

### 5. Criar arquivos de idioma (opcional)

```php
// bot/modules/MeuModulo/Language/pt_BR.php
<?php
return [
    'success'   => '✅ Operação realizada com sucesso.',
    'no_target' => '❌ Responda a uma mensagem ou mencione um usuário.',
    'no_perm'   => '⛔ Você não tem permissão para fazer isso.',
];
```

```php
// bot/modules/MeuModulo/Language/en_US.php
<?php
return [
    'success'   => '✅ Operation completed successfully.',
    'no_target' => '❌ Reply to a message or mention a user.',
    'no_perm'   => '⛔ You do not have permission to do this.',
];
```

**Usar no comando:**
```php
$lang = $app->make(LanguageService::class);
$telegram->reply($update, $lang->trans('MeuModulo.success'));
// ou com substituições:
$telegram->reply($update, $lang->trans('MeuModulo.banned_user', ['user' => $name]));
```

### 6. Reiniciar o bot

```bash
# O ModuleLoader detecta automaticamente na próxima inicialização
# No Replit: o workflow "Telegram Bot" reinicia automaticamente
```

---

## Regras de ouro para módulos

### ✅ Sempre fazer

```php
// Usar serviços via container
$telegram = $app->make(TelegramService::class);
$cache    = $app->make(CacheService::class);
$logger   = $app->make(LoggerService::class);

// Verificar se há resposta/alvo antes de agir
$reply = $update->getReplyToMessage();
if (!$reply) { /* avisar usuário */ return; }

// Usar o sistema de idiomas para todo texto
$lang->trans('MeuModulo.mensagem_de_sucesso');

// Comunicar entre módulos via eventos
$dispatcher->emit('meumodulo.algo_aconteceu', $dados);
```

### ❌ Nunca fazer

```php
// Nunca chamar API diretamente
$ch = curl_init('https://api.telegram.org/...');

// Nunca importar outro módulo diretamente
use Modules\Ban\BanModule;  // PROIBIDO

// Nunca SQL em um comando
$pdo->query("SELECT * FROM warns WHERE...");  // usar Repository

// Nunca texto fixo no código
$telegram->reply($update, 'Usuário banido!');  // usar Language/
```

---

## Dependências entre módulos

Se o módulo A precisa que o módulo B exista:

```php
// No MeuModuloModule.php
public function getDependencies(): array
{
    return ['Admin', 'Settings'];  // nomes de módulos obrigatórios
}
```

Se `Admin` ou `Settings` não estiverem carregados antes de `MeuModulo`,
o loader registra um aviso no log e pula o módulo.

**Importante:** A ordem de carregamento é a ordem do filesystem (alfabética por padrão).
Para garantir ordem, prefixe as pastas: `10_Admin/`, `20_Ban/`, etc. (futuro).

---

## Módulo com configuração própria

```php
// bot/modules/MeuModulo/config.php
<?php
return [
    'enabled'      => true,
    'max_warns'    => 3,
    'mute_time'    => 3600,  // 1 hora em segundos
    'notify_admins' => true,
];
```

Acessar no módulo:

```php
$config = $app->make(ConfigService::class);
$maxWarns = $config->get('MeuModulo.max_warns', 3);
```

*(O ConfigService carrega automaticamente de `app/config/`. Para configs de módulos, a convenção ainda está sendo definida — veja o roadmap.)*

---

## Estrutura completa de um módulo avançado (referência)

```
modules/Ban/
├── module.php              # return new BanModule()
├── BanModule.php           # implements ModuleInterface
│
├── Commands/               # subpasta para organizar (opcional)
│   ├── BanCommand.php      # /ban
│   ├── UnbanCommand.php    # /unban
│   ├── TbanCommand.php     # /tban (ban temporário)
│   └── KickCommand.php     # /kick
│
├── Services/
│   └── BanService.php      # lógica de negócio isolada
│
├── Repository/
│   └── BanRepository.php   # acesso ao banco de dados
│
├── config.php              # configurações padrão
│
└── Language/
    ├── en_US.php
    ├── pt_BR.php
    └── es_ES.php
```
