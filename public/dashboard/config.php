<?php
/**
 * Painel Web — Configuração
 *
 * Configure DASHBOARD_PASSWORD_HASH como secret/env var:
 *   php -r "echo password_hash('sua_senha', PASSWORD_DEFAULT);"
 */

require_once __DIR__ . '/../../app/Core/Helper/EnvHelper.php';
\App\Core\Helper\EnvHelper::load(__DIR__ . '/../../.env');

$dashboardPasswordHash = getenv('DASHBOARD_PASSWORD_HASH') ?: '';
if ($dashboardPasswordHash === '') {
    http_response_code(503);
    exit('Dashboard authentication is not configured.');
}
define('DASHBOARD_PASSWORD_HASH', $dashboardPasswordHash);

// Caminho para o banco SQLite (relativo a este arquivo)
// Em produção com PostgreSQL, defina DATABASE_URL nas variáveis de ambiente
define('SQLITE_PATH', __DIR__ . '/../../storage/database.sqlite');

// Tempo de sessão em segundos (padrão: 4 horas)
define('SESSION_LIFETIME', 14400);

// Nome exibido no painel
define('DASHBOARD_TITLE', 'ACHI BOT');
