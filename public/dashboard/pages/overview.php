<?php
// ─── Status do Sistema ────────────────────────────────────────────────────────
$botStatus = 'Online';
$dbType = getenv('DATABASE_URL') ? 'PostgreSQL' : 'SQLite';
$phpVersion = PHP_VERSION;
$systemVersion = '1.5.0-Pro';

// ─── Totais ───────────────────────────────────────────────────────────────────
$totalGroups   = tableExists('groups')        ? (int)dbScalar('SELECT COUNT(*) FROM groups')        : 0;
$totalBans     = tableExists('bans')          ? (int)dbScalar('SELECT COUNT(*) FROM bans') : 0;
$totalWarns    = tableExists('warns')         ? (int)dbScalar('SELECT COUNT(*) FROM warns')          : 0;
$totalNotes    = tableExists('notes')         ? (int)dbScalar('SELECT COUNT(*) FROM notes')          : 0;
$totalMessages = tableExists('message_stats') ? (int)dbScalar('SELECT SUM(msg_count) FROM message_stats') : 0;
$totalUsers    = tableExists('message_stats') ? (int)dbScalar('SELECT COUNT(DISTINCT user_id) FROM message_stats') : 0;

// ─── Banimentos recentes ──────────────────────────────────────────────────────
$recentBans = tableExists('bans') ? dbQuery(
    'SELECT b.user_id, b.reason, b.created_at as banned_at, g.title as chat_title
     FROM bans b
     LEFT JOIN groups g ON g.id = b.chat_id
     ORDER BY b.created_at DESC LIMIT 5'
) : [];

// ─── Top usuários ─────────────────────────────────────────────────────────────
$topUsers = tableExists('message_stats') ? dbQuery(
    'SELECT user_id, SUM(msg_count) as total
     FROM message_stats
     GROUP BY user_id
     ORDER BY total DESC
     LIMIT 5'
) : [];
?>

<div class="cards">
  <div class="card accent">
    <div class="label"><span>◉</span> Status do Bot</div>
    <div class="value" style="color:var(--success);font-size:24px"><?= $botStatus ?></div>
    <div class="sub">v<?= $systemVersion ?> • PHP <?= $phpVersion ?></div>
  </div>
  <div class="card">
    <div class="label"><span>▣</span> Grupos Ativos</div>
    <div class="value"><?= number_format($totalGroups) ?></div>
    <div class="sub">monitorados em tempo real</div>
  </div>
  <div class="card">
    <div class="label"><span>👤</span> Usuários</div>
    <div class="value"><?= number_format($totalUsers) ?></div>
    <div class="sub">interagindo com o bot</div>
  </div>
  <div class="card danger">
    <div class="label"><span>⊘</span> Bans Ativos</div>
    <div class="value"><?= number_format($totalBans) ?></div>
    <div class="sub">usuários restritos</div>
  </div>
  <div class="card success">
    <div class="label"><span>💬</span> Mensagens</div>
    <div class="value"><?= number_format($totalMessages) ?></div>
    <div class="sub">processadas pelo core</div>
  </div>
  <div class="card">
    <div class="label"><span>🗄️</span> Banco de Dados</div>
    <div class="value" style="font-size:24px"><?= $dbType ?></div>
    <div class="sub">armazenamento persistente</div>
  </div>
</div>

<div style="display:grid;grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));gap:24px;margin-bottom:32px">

  <!-- Bans recentes -->
  <div class="table-wrap">
    <div class="table-header">
      <h3>Banimentos Recentes</h3>
      <a href="?page=bans" class="badge-blue" style="text-decoration:none">Ver todos</a>
    </div>
    <div class="table-container">
      <?php if (empty($recentBans)): ?>
        <div class="empty"><p>Nenhum banimento registrado.</p></div>
      <?php else: ?>
      <table>
        <thead><tr><th>Usuário</th><th>Grupo</th><th>Data</th></tr></thead>
        <tbody>
          <?php foreach ($recentBans as $b): ?>
          <tr>
            <td><span class="badge-gray"><?= h($b['user_id']) ?></span></td>
            <td class="trunc"><?= h($b['chat_title'] ?? '—') ?></td>
            <td style="font-size:11px;color:var(--muted)"><?= date('d/m H:i', strtotime($b['banned_at'])) ?></td>
          </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
      <?php endif; ?>
    </div>
  </div>

  <!-- Top usuários -->
  <div class="table-wrap">
    <div class="table-header">
      <h3>Usuários Mais Ativos</h3>
      <span class="badge-pill badge-green">Top 5</span>
    </div>
    <div class="table-container">
      <?php if (empty($topUsers)): ?>
        <div class="empty"><p>Sem dados de mensagens.</p></div>
      <?php else: ?>
      <table>
        <thead><tr><th>Pos</th><th>User ID</th><th>Mensagens</th></tr></thead>
        <tbody>
          <?php $medals = ['🥇','🥈','🥉','4º','5º']; foreach ($topUsers as $i => $u): ?>
          <tr>
            <td style="font-size:18px"><?= $medals[$i] ?></td>
            <td><code style="color:var(--accent)"><?= h($u['user_id']) ?></code></td>
            <td><span class="badge-pill badge-blue"><?= number_format((int)$u['total']) ?></span></td>
          </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
      <?php endif; ?>
    </div>
  </div>

</div>
