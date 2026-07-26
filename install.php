<?php
/**
 * Instalador Profissional — ACHI BOT
 * Suporta: Ubuntu, Termux, Hospedagem Compartilhada
 */

declare(strict_types=1);

define('MIN_PHP_VERSION', '8.2.0');
define('REQUIRED_EXTENSIONS', ['pdo', 'pdo_sqlite', 'mbstring', 'curl', 'json', 'openssl']);

$isCli = PHP_SAPI === 'cli';

function out(string $msg, string $type = 'info') {
    global $isCli;
    $colors = ['info' => "\033[36m", 'success' => "\033[32m", 'error' => "\033[31m", 'warn' => "\033[33m", 'reset' => "\033[0m"];
    if ($isCli) {
        echo $colors[$type] . $msg . $colors['reset'] . PHP_EOL;
    } else {
        $class = "msg-$type";
        echo "<div class='$class'>$msg</div>";
    }
}

if (!$isCli) {
    echo "<style>
        body { font-family: sans-serif; background: #f4f4f9; padding: 40px; line-height: 1.6; }
        .container { max-width: 600px; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: auto; }
        h1 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .msg-info { color: #007bff; }
        .msg-success { color: #28a745; font-weight: bold; }
        .msg-error { color: #dc3545; background: #fff5f5; padding: 10px; border-radius: 4px; }
        .msg-warn { color: #856404; background: #fff3cd; padding: 10px; border-radius: 4px; }
        form { margin-top: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #28a745; color: #fff; border: 0; padding: 12px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #218838; }
    </style>";
    echo "<div class='container'><h1>Instalador ACHI BOT</h1>";
}

// 1. Verificação de Requisitos
out("Verificando requisitos do sistema...");

if (version_compare(PHP_VERSION, MIN_PHP_VERSION, '<')) {
    out("Erro: Versão do PHP insuficiente. Necessário " . MIN_PHP_VERSION . " ou superior.", 'error');
    exit;
}

foreach (REQUIRED_EXTENSIONS as $ext) {
    if (!extension_loaded($ext)) {
        out("Erro: Extensão PHP '$ext' não encontrada.", 'error');
        exit;
    }
}

$writablePaths = ['storage/cache', 'storage', 'logs', 'app/config'];
foreach ($writablePaths as $path) {
    if (!is_dir(__DIR__ . '/' . $path)) {
        mkdir(__DIR__ . '/' . $path, 0777, true);
    }
    if (!is_writable(__DIR__ . '/' . $path)) {
        out("Aviso: Sem permissão de escrita em '$path'. Tente: chmod -R 777 $path", 'warn');
    }
}

out("Requisitos básicos verificados com sucesso!", 'success');

// 2. Coleta de Dados
if ($isCli && !isset($argv[1])) {
    out("\n--- Configuração Interativa ---");
    $botToken = readline("Token do Bot (BotFather): ");
    $ownerId = readline("Seu ID do Telegram (Owner): ");
    $dashPass = readline("Senha para o Painel/API: ");
} elseif (!$isCli && $_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo "<form method='POST'>
        <label>Token do Bot</label>
        <input type='text' name='bot_token' required placeholder='123456:ABC...'>
        <label>Seu ID do Telegram (Owner)</label>
        <input type='text' name='owner_id' required placeholder='987654321'>
        <label>Senha do Painel/API</label>
        <input type='password' name='dash_pass' required>
        <button type='submit'>Finalizar Instalação</button>
    </form></div>";
    exit;
} else {
    $botToken = $_POST['bot_token'] ?? '';
    $ownerId = $_POST['owner_id'] ?? '';
    $dashPass = $_POST['dash_pass'] ?? '';
}

// 3. Aplicação das Configurações
out("\nFinalizando instalação...");

// Criar app/config/app.php
$appConfig = "<?php
return [
    'owner_ids' => [{$ownerId}],
    'debug' => false,
    'timezone' => 'UTC',
];";
file_put_contents(__DIR__ . '/app/config/app.php', $appConfig);

// Criar app/config/telegram.php
$tgConfig = "<?php
return [
    'bot_token' => '{$botToken}',
    'parse_mode' => 'HTML',
];";
file_put_contents(__DIR__ . '/app/config/telegram.php', $tgConfig);

// Gerar Hash da Senha para o Dashboard e .env
$hash = password_hash($dashPass, PASSWORD_DEFAULT);
$envContent = "TELEGRAM_BOT_TOKEN='{$botToken}'\nDASHBOARD_PASSWORD_HASH='{$hash}'\n";
file_put_contents(__DIR__ . '/.env', $envContent);

// 4. Executar Migrations
try {
    out("Executando migrações do banco de dados...");
    putenv("TELEGRAM_BOT_TOKEN=$botToken");
    exec('php console.php migrate', $output, $return);
    if ($return === 0) {
        out("Banco de dados configurado!", 'success');
    } else {
        out("Aviso: Falha ao rodar migrações via CLI. Tente rodar manualmente: php console.php migrate", 'warn');
        foreach ($output as $line) out("  $line", 'warn');
    }
} catch (Exception $e) {
    out("Erro ao configurar banco: " . $e->getMessage(), 'error');
}

out("\nInstalação concluída com sucesso!", 'success');
out("Token da API (MD5 da senha): " . md5($hash), 'info');
out("Para iniciar o bot: php run.php", 'info');

if (!$isCli) echo "</div>";
