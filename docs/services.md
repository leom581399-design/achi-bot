# Referência de Serviços

Todos os serviços são registrados como **singletons** no container e acessíveis via:

```php
$service = $app->make(NomeDoServico::class);
```

---

## TelegramService

Operações de alto nível com o Telegram. **Use sempre este serviço nos módulos.**

```php
use App\Core\Services\TelegramService;
$telegram = $app->make(TelegramService::class);
```

### Métodos

```php
// Enviar mensagem para um chat (por ID)
$telegram->sendMessage(int|string $chatId, string $text, array $options = []);

// Responder à mensagem do update (com quote)
$telegram->reply(Update $update, string $text, array $options = []);

// Enviar sem quote
$telegram->send(Update $update, string $text, array $options = []);

// Verificar se usuário é admin do chat
$telegram->isAdmin(int|string $chatId, int $userId): bool;

// Verificar se usuário é criador do chat
$telegram->isCreator(int|string $chatId, int $userId): bool;

// Verificar se o bot é admin do chat
$telegram->isBotAdmin(int|string $chatId): bool;

// Formatar menção de usuário (link tg://user ou @username)
$telegram->mentionUser(array $user): string;

// Formatar nome de usuário com tag
$telegram->formatUser(array $user): string;
```

### Opções comuns

```php
$telegram->reply($update, 'Texto', [
    'parse_mode'                  => 'HTML',          // ou 'Markdown'
    'disable_web_page_preview'    => true,
    'disable_notification'        => true,
    'reply_markup'                => $keyboard,        // InlineKeyboard ou ReplyKeyboard
]);
```

---

## TelegramClient

Acesso direto à API do Telegram. Use apenas se o TelegramService não cobrir o que você precisa.

```php
use App\Core\Telegram\TelegramClient;
$client = $app->make(TelegramClient::class);
```

### Métodos disponíveis

```php
// Mensagens
$client->sendMessage(int|string $chatId, string $text, array $options = []);
$client->editMessageText(int|string $chatId, int $messageId, string $text, array $options = []);
$client->deleteMessage(int|string $chatId, int $messageId);
$client->forwardMessage(int|string $chatId, int|string $fromChatId, int $messageId);
$client->sendDocument(int|string $chatId, string $document, array $options = []);

// Membros
$client->banChatMember(int|string $chatId, int $userId, array $options = []);
$client->unbanChatMember(int|string $chatId, int $userId, bool $onlyIfBanned = true);
$client->restrictChatMember(int|string $chatId, int $userId, array $permissions, array $options = []);
$client->promoteChatMember(int|string $chatId, int $userId, array $options = []);

// Info
$client->getChat(int|string $chatId);
$client->getChatMember(int|string $chatId, int $userId);
$client->getChatAdministrators(int|string $chatId);
$client->getChatMemberCount(int|string $chatId);
$client->getMe();

// Callbacks / Inline
$client->answerCallbackQuery(string $callbackQueryId, array $options = []);
$client->answerInlineQuery(string $inlineQueryId, array $results, array $options = []);

// Chamada genérica (para métodos não cobertos)
$client->request(string $method, array $params = []);

// Enviar conteúdo em memória como documento (multipart — usado pelo Backup)
$client->sendDocumentContent(int|string $chatId, string $content, string $filename, string $caption = '', array $options = []);

// Obter metadados de arquivo pelo file_id (retorna file_path para download)
$client->getFile(string $fileId): array;

// Baixar conteúdo de arquivo do Telegram pelo file_path
$client->downloadFile(string $filePath): string|false;
```

### Erro

Se a API retornar erro, lança `TelegramApiException`:

```php
use App\Core\Telegram\TelegramApiException;

try {
    $client->banChatMember($chatId, $userId);
} catch (TelegramApiException $e) {
    $logger->error("Falha ao banir: " . $e->getMessage());
    // $e->getCode() → código de erro da API (ex: 400, 403)
}
```

---

## PermissionService

Resolve e verifica permissões de usuários.

```php
use App\Core\Services\PermissionService;
$perm = $app->make(PermissionService::class);
```

### Métodos

```php
// Resolver o nível de permissão de um usuário em um chat
$perm->getPermission(int|string $chatId, int $userId): Permission;

// Verificar se usuário tem ao menos uma permissão
$perm->can(int|string $chatId, int $userId, Permission $required): bool;

// Verificar se é owner do bot (OWNER_IDS)
$perm->isOwner(int $userId): bool;
```

### Exemplo

```php
$permission = $perm->getPermission($chatId, $userId);

if ($permission->isAtLeast(Permission::Administrator)) {
    // pode banir
}

// Ou direto:
if (!$perm->can($chatId, $userId, Permission::Moderator)) {
    $telegram->reply($update, '⛔ Sem permissão.');
    return;
}
```

---

## CacheService

Cache filesystem. Transparente — pode ser trocado por Redis sem mudar os módulos.

```php
use App\Core\Services\CacheService;
$cache = $app->make(CacheService::class);
```

### Métodos

```php
// Ler (null = não existe ou expirado)
$cache->get(string $key, mixed $default = null): mixed;

// Gravar (ttl em segundos, null = sem expiração)
$cache->set(string $key, mixed $value, ?int $ttl = null): void;

// Verificar existência
$cache->has(string $key): bool;

// Remover
$cache->delete(string $key): void;

// Incrementar contador
$cache->increment(string $key, int $by = 1, ?int $ttl = null): int;

// Limpar tudo
$cache->flush(): void;
```

### Convenções de chaves

```php
// Padrão: modulo:tipo:identificador:contexto
$cache->set("warn:count:{$userId}:{$chatId}", 3, 86400);
$cache->set("flood:{$userId}:" . date('Y-m-d-H-i'), $count, 70);
$cache->set("mute:{$userId}:{$chatId}", true, $duration);
$cache->get("settings:{$chatId}");
```

---

## LanguageService

Sistema de tradução por módulo.

```php
use App\Core\Services\LanguageService;
$lang = $app->make(LanguageService::class);
```

### Carregar strings (no boot() do módulo)

```php
$lang->load('MeuModulo', __DIR__ . '/Language');
// Carrega modules/MeuModulo/Language/pt_BR.php (ou en_US.php como fallback)
```

### Traduzir

```php
// Chave simples
$lang->trans('MeuModulo.success');

// Com substituições
$lang->trans('MeuModulo.banned', [
    'user' => $userName,
    'by'   => $adminName,
]);
// Se Language/pt_BR.php contém: 'banned' => ':user foi banido por :by'
// Resultado: "João foi banido por Admin"

// Especificando módulo separado da chave
$lang->trans('mensagem_key', ['user' => $name], module: 'MeuModulo');
```

### Mudar locale

```php
$lang->setLocale('pt_BR');
```

---

## ConfigService

Acessa arquivos PHP de configuração em `app/config/`.

```php
use App\Core\Services\ConfigService;
$config = $app->make(ConfigService::class);
```

### Métodos

```php
// Ler valor (dot notation: arquivo.chave.subchave)
$config->get('app.owner_ids');           // de app/config/app.php
$config->get('telegram.parse_mode');    // de app/config/telegram.php
$config->get('app.debug', false);       // com valor padrão

// Ler arquivo completo
$config->all('app');   // retorna array inteiro de app/config/app.php
```

### Criar config de módulo

```php
// app/config/ban.php
return [
    'delete_command_message' => true,
    'notify_channel'         => null,
];

// Acessar:
$config->get('ban.delete_command_message', true);
```

---

## LoggerService

Logger com saída no console e em arquivos.

```php
use App\Core\Services\LoggerService;
$logger = $app->make(LoggerService::class);
```

### Métodos

```php
$logger->debug('Mensagem debug', ['contexto' => $valor]);
$logger->info('Bot iniciado');
$logger->warning('Módulo sem dependência: Ban');
$logger->error('Falha na API: ' . $e->getMessage());
$logger->critical('Banco de dados inacessível!');
$logger->security('Tentativa de ban indevida', ['user' => $userId]);
```

### Arquivos de log

| Arquivo | Conteúdo |
|---|---|
| `logs/telegram.log` | debug, info, warning |
| `logs/error.log` | error, critical |
| `logs/security.log` | eventos de segurança |
