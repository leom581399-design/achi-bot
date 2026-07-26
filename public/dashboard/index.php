<?php
declare(strict_types=1);

require_once __DIR__ . '/config.php';

// ─── Sessão ──────────────────────────────────────────────────────────────────
session_name('bot_dashboard');
session_start();

// Renovar TTL da sessão a cada request
if (isset($_SESSION['auth']) && $_SESSION['auth'] === true) {
    if (isset($_SESSION['last_activity']) && (time() - $_SESSION['last_activity']) > SESSION_LIFETIME) {
        session_unset();
        session_destroy();
        session_start();
    } else {
        $_SESSION['last_activity'] = time();
    }
}

// ─── Login / Logout ──────────────────────────────────────────────────────────
if (isset($_POST['action']) && $_POST['action'] === 'login') {
    $password = $_POST['password'] ?? '';
    if (password_verify($password, DASHBOARD_PASSWORD_HASH)) {
        $_SESSION['auth'] = true;
        $_SESSION['last_activity'] = time();
        header('Location: ' . strtok($_SERVER['REQUEST_URI'], '?'));
        exit;
    } else {
        $loginError = 'Senha incorreta.';
    }
}

if (isset($_GET['logout'])) {
    session_unset();
    session_destroy();
    header('Location: ' . strtok($_SERVER['REQUEST_URI'], '?'));
    exit;
}

// ─── Banco de dados ───────────────────────────────────────────────────────────
function getDb(): PDO {
    static $pdo = null;
    if ($pdo !== null) return $pdo;

    $dsn = getenv('DATABASE_URL');
    if ($dsn) {
        $parsed  = parse_url($dsn);
        $host    = $parsed['host'] ?? 'localhost';
        $port    = $parsed['port'] ?? 5432;
        $dbname  = ltrim($parsed['path'] ?? '/telegram', '/');
        $user    = $parsed['user'] ?? '';
        $pass    = $parsed['pass'] ?? '';
        $pdo = new PDO("pgsql:host={$host};port={$port};dbname={$dbname}", $user, $pass, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    } else {
        if (!file_exists(SQLITE_PATH)) {
            die('<div style="font:14px sans-serif;padding:40px;color:#c00">Banco de dados não encontrado em: ' . htmlspecialchars(SQLITE_PATH) . '<br>Execute <code>php console.php migrate</code> primeiro.</div>');
        }
        $pdo = new PDO('sqlite:' . SQLITE_PATH, '', '', [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
        $pdo->exec('PRAGMA journal_mode=WAL');
    }
    return $pdo;
}

function dbQuery(string $sql, array $params = []): array {
    $stmt = getDb()->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll();
}

function dbOne(string $sql, array $params = []): ?array {
    $rows = dbQuery($sql, $params);
    return $rows[0] ?? null;
}

function dbScalar(string $sql, array $params = []): mixed {
    $row = dbOne($sql, $params);
    return $row ? array_values($row)[0] : null;
}

function tableExists(string $table): bool {
    $db = getDb();
    $driver = $db->getAttribute(PDO::ATTR_DRIVER_NAME);
    if ($driver === 'sqlite') {
        $r = dbOne("SELECT name FROM sqlite_master WHERE type='table' AND name=?", [$table]);
    } else {
        $r = dbOne("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name=?", [$table]);
    }
    return $r !== null;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function h(mixed $v): string { return htmlspecialchars((string)$v, ENT_QUOTES, 'UTF-8'); }
function paginate(int $total, int $page, int $perPage): array {
    $pages = (int)ceil($total / $perPage);
    return ['pages' => max(1, $pages), 'offset' => ($page - 1) * $perPage];
}
function currentUrl(array $override = []): string {
    $params = array_merge($_GET, $override);
    unset($params['logout']);
    return '?' . http_build_query($params);
}

// ─── Roteamento ──────────────────────────────────────────────────────────────
$page    = preg_replace('/[^a-z_]/', '', strtolower($_GET['page'] ?? 'overview'));
$allowed = ['overview', 'groups', 'bans', 'warns', 'notes', 'stats', 'fedbans'];
if (!in_array($page, $allowed, true)) $page = 'overview';

$nav = [
    'overview' => ['icon' => '▣',  'label' => 'Visão Geral'],
    'groups'   => ['icon' => '◉',  'label' => 'Grupos'],
    'bans'     => ['icon' => '⊘',  'label' => 'Bans'],
    'warns'    => ['icon' => '⚠',  'label' => 'Advertências'],
    'notes'    => ['icon' => '◈',  'label' => 'Notas'],
    'stats'    => ['icon' => '◈',  'label' => 'Estatísticas'],
    'fedbans'  => ['icon' => '⊗',  'label' => 'FedBans'],
];

// ─── HTML: Login ─────────────────────────────────────────────────────────────
if (!isset($_SESSION['auth']) || $_SESSION['auth'] !== true):
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title><?= h(DASHBOARD_TITLE) ?> — Login</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f1117;color:#e2e8f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:#1a1d27;border:1px solid #2d3148;border-radius:12px;padding:40px;width:100%;max-width:380px}
h1{font-size:22px;font-weight:700;margin-bottom:8px;color:#fff}
p{font-size:13px;color:#7c8db5;margin-bottom:28px}
label{display:block;font-size:12px;font-weight:600;color:#7c8db5;margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em}
input[type=password]{width:100%;background:#0f1117;border:1px solid #2d3148;border-radius:8px;padding:10px 14px;color:#e2e8f0;font-size:15px;outline:none;transition:border .2s}
input[type=password]:focus{border-color:#5865f2}
button{width:100%;margin-top:16px;background:#5865f2;border:none;border-radius:8px;padding:11px;color:#fff;font-size:15px;font-weight:600;cursor:pointer;transition:background .2s}
button:hover{background:#4752c4}
.error{background:#3d1a1a;border:1px solid #7f2828;border-radius:8px;padding:10px 14px;color:#f87171;font-size:13px;margin-bottom:16px}
</style>
</head>
<body>
<div class="card">
  <h1>🤖 <?= h(DASHBOARD_TITLE) ?></h1>
  <p>Painel de gerenciamento do bot</p>
  <?php if (!empty($loginError)): ?>
    <div class="error"><?= h($loginError) ?></div>
  <?php endif; ?>
  <form method="post">
    <input type="hidden" name="action" value="login">
    <label>Senha</label>
    <input type="password" name="password" autofocus autocomplete="current-password">
    <button type="submit">Entrar</button>
  </form>
</div>
</body>
</html>
<?php
    exit;
endif;

// ─── HTML: Painel ─────────────────────────────────────────────────────────────
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title><?= h(DASHBOARD_TITLE) ?> — <?= h($nav[$page]['label']) ?></title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f1117;--surface:#1a1d27;--border:#2d3148;
  --text:#e2e8f0;--muted:#7c8db5;--accent:#5865f2;
  --danger:#ef4444;--warn:#f59e0b;--success:#22c55e;
}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;display:flex;min-height:100vh;font-size:14px}

/* Sidebar */
.sidebar{width:220px;min-height:100vh;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0;position:sticky;top:0;height:100vh;overflow-y:auto}
.sidebar-logo{padding:20px 18px 16px;border-bottom:1px solid var(--border)}
.sidebar-logo h2{font-size:15px;font-weight:700;color:#fff}
.sidebar-logo span{font-size:11px;color:var(--muted)}
nav{padding:12px 8px;flex:1}
nav a{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;color:var(--muted);text-decoration:none;font-size:13px;font-weight:500;transition:all .15s;margin-bottom:2px}
nav a:hover{background:rgba(88,101,242,.12);color:var(--text)}
nav a.active{background:rgba(88,101,242,.2);color:#818cf8}
nav a .icon{font-size:15px;width:20px;text-align:center}
.sidebar-footer{padding:12px 8px;border-top:1px solid var(--border)}
.sidebar-footer a{display:block;padding:8px 10px;color:var(--muted);text-decoration:none;font-size:12px;border-radius:6px}
.sidebar-footer a:hover{color:var(--danger)}

/* Main */
.main{flex:1;display:flex;flex-direction:column;min-width:0}
.topbar{padding:16px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:var(--surface)}
.topbar h1{font-size:17px;font-weight:700}
.topbar .badge{background:rgba(88,101,242,.2);color:#818cf8;border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600}
.content{padding:24px;flex:1}

/* Cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px;margin-bottom:24px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px}
.card .label{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}
.card .value{font-size:28px;font-weight:700;color:#fff}
.card .sub{font-size:12px;color:var(--muted);margin-top:4px}
.card.accent{border-color:rgba(88,101,242,.4)}
.card.danger{border-color:rgba(239,68,68,.3)}
.card.warn{border-color:rgba(245,158,11,.3)}
.card.success{border-color:rgba(34,197,94,.3)}

/* Table */
.table-wrap{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.table-header{padding:14px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.table-header h3{font-size:14px;font-weight:600}
table{width:100%;border-collapse:collapse}
thead th{padding:10px 16px;text-align:left;font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid var(--border);background:rgba(255,255,255,.02)}
tbody tr{border-bottom:1px solid var(--border);transition:background .1s}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:rgba(255,255,255,.02)}
td{padding:10px 16px;font-size:13px;vertical-align:middle}
.badge-red{background:rgba(239,68,68,.15);color:#f87171;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600}
.badge-yellow{background:rgba(245,158,11,.15);color:#fbbf24;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600}
.badge-green{background:rgba(34,197,94,.15);color:#4ade80;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600}
.badge-blue{background:rgba(88,101,242,.15);color:#818cf8;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600}
.badge-gray{background:rgba(255,255,255,.07);color:var(--muted);border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600}

/* Search / Filter */
.search-bar{display:flex;gap:8px;align-items:center}
.search-bar input,.search-bar select{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:6px 10px;color:var(--text);font-size:13px;outline:none}
.search-bar input:focus,.search-bar select:focus{border-color:var(--accent)}
.search-bar button{background:var(--accent);border:none;border-radius:6px;padding:6px 14px;color:#fff;font-size:13px;font-weight:600;cursor:pointer}

/* Pagination */
.pagination{display:flex;gap:6px;justify-content:center;margin-top:16px;flex-wrap:wrap}
.pagination a,.pagination span{display:inline-block;padding:5px 12px;border-radius:6px;font-size:13px;text-decoration:none;border:1px solid var(--border);color:var(--muted)}
.pagination a:hover{border-color:var(--accent);color:var(--accent)}
.pagination .current{background:var(--accent);border-color:var(--accent);color:#fff}

/* Empty state */
.empty{padding:48px 24px;text-align:center;color:var(--muted)}
.empty .icon{font-size:36px;margin-bottom:12px}
.empty p{font-size:13px}

/* Truncate */
.trunc{max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* Alert */
.alert-warn{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);border-radius:8px;padding:10px 14px;color:#fbbf24;font-size:13px;margin-bottom:16px}

@media(max-width:700px){
  .sidebar{display:none}
  .cards{grid-template-columns:1fr 1fr}
  td,th{padding:8px 10px}
}
</style>
</head>
<body>

<aside class="sidebar" id="sidebar">
  <div class="sidebar-logo">
    <div style="background:var(--accent);width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff">G</div>
    <div>
      <h2>GroupHelp</h2>
      <span>v1.5.0 Professional</span>
    </div>
  </div>
  <nav>
    <?php foreach ($nav as $key => $item): ?>
      <a href="?page=<?= $key ?>" class="<?= $page === $key ? 'active' : '' ?>">
        <span class="icon"><?= $item['icon'] ?></span>
        <?= h($item['label']) ?>
      </a>
    <?php endforeach; ?>
  </nav>
  <div class="sidebar-footer">
    <a href="?logout=1">
      <span style="font-size:16px">↩</span> Sair do Sistema
    </a>
  </div>
</aside>

<main class="main">
  <div class="topbar">
    <div style="display:flex;align-items:center;gap:12px">
      <button class="menu-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')">☰</button>
      <h1><?= h($nav[$page]['label']) ?></h1>
    </div>
    <div style="display:flex;align-items:center;gap:12px">
      <span class="badge">Online</span>
    </div>
  </div>
  <div class="content">
    <?php
    $pageFile = __DIR__ . '/pages/' . $page . '.php';
    if (file_exists($pageFile)) {
        include $pageFile;
    } else {
        echo '<div class="empty"><div class="icon">🚧</div><p>Página em construção.</p></div>';
    }
    ?>
  </div>
</main>

<script>
  // Fechar sidebar ao clicar fora em dispositivos móveis
  document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.menu-toggle');
    if (window.innerWidth <= 1024 && !sidebar.contains(event.target) && !toggle.contains(event.target)) {
      sidebar.classList.remove('open');
    }
  });
</script>

</body>
</html>
