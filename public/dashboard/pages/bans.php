<?php
$search  = trim($_GET['q'] ?? '');
$perPage = 20;
$curPage = max(1, (int)($_GET['p'] ?? 1));

if (!tableExists('bans')) {
    echo '<div class="empty"><div class="icon">⚠</div><p>Tabela <code>bans</code> não encontrada.</p></div>';
    return;
}

$conditions = [];
$params     = [];

if ($search !== '') {
    $conditions[] = '(b.user_id LIKE ? OR b.reason LIKE ? OR g.title LIKE ?)';
    $params[] = "%{$search}%";
    $params[] = "%{$search}%";
    $params[] = "%{$search}%";
}

$where = $conditions ? 'WHERE ' . implode(' AND ', $conditions) : '';

$total = (int)dbScalar("SELECT COUNT(*) FROM bans b LEFT JOIN groups g ON g.id = b.chat_id {$where}", $params);
['pages' => $pages, 'offset' => $offset] = paginate($total, $curPage, $perPage);

$rows = dbQuery(
    "SELECT b.*, g.title as chat_title 
     FROM bans b 
     LEFT JOIN groups g ON g.id = b.chat_id
     {$where}
     ORDER BY b.banned_at DESC
     LIMIT {$perPage} OFFSET {$offset}",
    $params
);

function banStatus(array $b): string {
    if ($b['until_date'] && strtotime($b['until_date']) > time()) {
        return '<span class="badge-pill badge-yellow">Temporário</span>';
    }
    return '<span class="badge-pill badge-red">Ativo</span>';
}
?>

<div class="table-wrap">
  <div class="table-header">
    <h3>Gestão de Banimentos <span class="badge-pill badge-gray"><?= $total ?></span></h3>
    <form class="search-bar" method="get">
      <input type="hidden" name="page" value="bans">
      <input type="text" name="q" placeholder="Buscar ID, motivo ou grupo…" value="<?= h($search) ?>">
      <button type="submit">Buscar</button>
      <?php if ($search): ?><a href="?page=bans" style="color:var(--muted);font-size:12px;text-decoration:none">✕</a><?php endif; ?>
    </form>
  </div>

  <div class="table-container">
    <?php if (empty($rows)): ?>
      <div class="empty"><div class="icon">⊘</div><p>Nenhum banimento encontrado.</p></div>
    <?php else: ?>
    <table>
      <thead>
        <tr>
          <th>User ID</th>
          <th>Grupo</th>
          <th>Motivo</th>
          <th>Banido por</th>
          <th>Data</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($rows as $b): ?>
        <tr>
          <td><code style="color:var(--accent)"><?= h($b['user_id']) ?></code></td>
          <td class="trunc"><?= h($b['chat_title'] ?? $b['chat_id']) ?></td>
          <td class="trunc"><?= h($b['reason'] ?: '—') ?></td>
          <td><span class="badge-pill badge-gray"><?= h($b['banned_by']) ?></span></td>
          <td style="font-size:12px"><?= date('d/m/Y H:i', strtotime($b['created_at'])) ?></td>
          <td><?= banStatus($b) ?></td>
        </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
    <?php endif; ?>
  </div>
</div>

<?php if ($pages > 1): ?>
<div class="pagination">
  <?php for ($i = 1; $i <= $pages; $i++): ?>
    <?php if ($i === $curPage): ?>
      <span class="current"><?= $i ?></span>
    <?php else: ?>
      <a href="<?= h(currentUrl(['p' => $i])) ?>"><?= $i ?></a>
    <?php endif; ?>
  <?php endfor; ?>
</div>
<?php endif; ?>
