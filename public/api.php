<?php
declare(strict_types=1);

/**
 * API REST — ACHI BOT
 * 
 * Este arquivo atua como o roteador principal para a API REST.
 * Autenticação via Header: Authorization: Bearer <seu_token>
 */

header('Content-Type: application/json');

// 1. Configuração e Segurança
require_once __DIR__ . '/dashboard/config.php';

function unauthorized() {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized', 'message' => 'Valid API Token required.']);
    exit;
}

// 2. Autenticação por Token
$authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
$token = '';
if (preg_match('/Bearer\s+(.*)$/i', $authHeader, $matches)) {
    $token = $matches[1];
}

$validToken = md5(DASHBOARD_PASSWORD_HASH);
if ($token !== $validToken) {
    unauthorized();
}

// 3. Funções de Banco de Dados
function getDb() {
    static $db = null;
    if ($db === null) {
        $path = SQLITE_PATH;
        $db = new PDO("sqlite:$path");
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    }
    return $db;
}

function dbQuery(string $sql, array $params = []): array {
    $stmt = getDb()->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll();
}

function dbScalar(string $sql, array $params = []) {
    $stmt = getDb()->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchColumn();
}

// 4. Roteamento
$method = $_SERVER['REQUEST_METHOD'];
$requestUri = $_SERVER['REQUEST_URI'];
$scriptName = $_SERVER['SCRIPT_NAME'];

// Extrair o endpoint após api.php
$endpoint = '';
if (strpos($requestUri, $scriptName) === 0) {
    $endpoint = substr($requestUri, strlen($scriptName));
} else {
    $basePath = dirname($scriptName);
    $endpoint = substr($requestUri, strlen($basePath));
    $endpoint = str_replace('/api.php', '', $endpoint);
}

$endpoint = explode('?', ltrim($endpoint, '/'))[0];

$response = ['status' => 'ok', 'timestamp' => time()];

try {
    switch ($endpoint) {
        case 'stats':
$response['data'] = [
    'total_groups' => (int)dbScalar("SELECT COUNT(*) FROM groups"),
    'total_users'  => (int)dbScalar("SELECT COUNT(DISTINCT user_id) FROM message_stats"),
    'total_messages' => (int)dbScalar("SELECT SUM(msg_count) FROM message_stats"),
    'top_groups' => dbQuery("SELECT g.id as chat_id, g.title, SUM(s.msg_count) as msgs FROM groups g JOIN message_stats s ON g.id = s.chat_id GROUP BY g.id ORDER BY msgs DESC LIMIT 10")
];
            break;

case 'bans':
    $search = $_GET['q'] ?? '';
    $where = $search ? "WHERE user_id LIKE ? OR reason LIKE ?" : "";
    $params = $search ? ["%$search%", "%$search%"] : [];
    $response['data'] = dbQuery("SELECT * FROM bans $where ORDER BY created_at DESC LIMIT 50", $params);
    break;

case 'groups':
    $response['data'] = dbQuery("SELECT id as chat_id, title, username, created_at FROM groups ORDER BY created_at DESC");
    break;

        case 'notes':
            $chatId = $_GET['chat_id'] ?? null;
            $where = $chatId ? "WHERE chat_id = ?" : "";
            $params = $chatId ? [$chatId] : [];
            $response['data'] = dbQuery("SELECT chat_id, name, content FROM notes $where", $params);
            break;
            
        case 'logs':
            $type = $_GET['type'] ?? 'telegram';
            $logFile = dirname(__DIR__) . "/logs/{$type}.log";
            if (is_file($logFile)) {
                $lines = file($logFile);
                $response['data'] = array_slice($lines, -100); // Últimas 100 linhas
            } else {
                $response['data'] = [];
            }
            break;

        default:
            http_response_code(404);
            $response = ['error' => 'Not Found', 'endpoint' => $endpoint];
            break;
    }
} catch (Exception $e) {
    http_response_code(500);
    $response = ['error' => 'Internal Server Error', 'message' => $e->getMessage()];
}

echo json_encode($response, JSON_PRETTY_PRINT);
