<?php
$search  = trim($_GET['q'] ?? '');
$chatId  = trim($_GET['chat'] ?? '');
$perPage = 20;
$curPage = max(1, (int)($_GET['p'] ?? 1));

if (!tableExists('warns')) {
    echo '<div class="empty"><div class="icon">⚠</div><p>Tabela <code>warns</code> não encontrada.</p></div>';
    return;
}

$conditions = [];
$params     = [];

if ($chatId !== '') {
    $conditions[] = 'w.chat_id = ?';
    $params[] = $chatId;
}
if ($search !== '') {
    $conditions[] = '(w.user_id LIKE ? OR w.reason LIKE ? OR g.title LIKE ?)';
    $params[] = "%{$search}%";
    $params[] = "%{$search}%";
    $params[] = "%{$search}%";
}

$where = $conditions ? 'WHERE ' . implode(' AND ', $conditions) : '';

$total = (int)dbScalar("SELECT COUNT(*) FROM warns w LEFT JOIN groups g ON g.id = w.chat_id {$where}", $params);
['pages' => $pages, 'offset' => $offset] = paginate($total, $curPage, $perPage);

$rows = dbQuery(
    "SELECT w.*, g.title as chat_title 
     FROM warns w 
     LEFT JOIN groups g ON g.id = w.chat_id
     {$where}
     ORDER BY w.created_at DESC
     LIMIT {$perPage} OFFSET {$offset}",
    $params
);

$warnCounts = tableExists('warns') ? dbQuery(
    'SELECT chat_id, user_id, COUNT(*) as total FROM warns GROUP BY chat_id, user_id HAVING total > 1 ORDER BY total DESC LIMIT 5'
) : [];
?>

<div style="display:grid;grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));gap:24px;margin-bottom:24px">
  <?php if (!empty($warnCounts)): ?>
  <div class="table-wrap">
    <div class="table-header"><h3>Múltiplas Advertências</h3></div>
    <div class="table-container">
      <table>
        <thead><tr><th>User ID</th><th>Grupo</th><th>Total</th><th></th></tr></thead>
        <tbody>
          <?php foreach ($warnCounts as $wc): ?>
          <tr>
            <td><code><?= h($wc['user_id']) ?></code></td>
            <td class="trunc"><?= h(dbScalar('SELECT title FROM groups WHERE id = ?', [$wc['chat_id']]) ?? $wc['chat_id']) ?></td>
            <td><span class="badge-pill badge-yellow"><?= (int)$wc['total'] ?>x</span></td>
            <td><a href="<?= h(currentUrl(['q' => $wc['user_id'], 'chat' => $wc['chat_id'], 'p' => 1])) ?>" class="badge-pill badge-blue" style="text-decoration:none">Ver</a></td>
          </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    </div>
  </div>
  <?php endif; ?>
</div>

<div class="table-wrap">
  <div class="table-header">
    <h3>Histórico de Advertências <span class="badge-pill badge-gray"><?= $total ?></span></h3>
    <form class="search-bar" method="get">
      <input type="hidden" name="page" value="warns">
      <input type="text" name="q" placeholder="Buscar ID, motivo ou grupo…" value="<?= h($search) ?>">
      <button type="submit">Buscar</button>
      <?php if ($search || $chatId): ?><a href="?page=warns" style="color:var(--muted);font-size:12px;text-decoration:none">✕</a><?php endif; ?>
    </form>
  </div>

  <div class="table-container">
    <?php if (empty($rows)): ?>
      <div class="empty"><div class="icon">⚠</div><p>Nenhuma advertência encontrada.</p></div>
    <?php else: ?>
    <table>
      <thead>
        <tr>
          <th>Usuário</th>
          <th>Grupo</th>
          <th>Motivo</th>
          <th>Por</th>
          <th>Data</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($rows as $w): ?>
        <tr>
          <td><code style="color:var(--accent)"><?= h($w['user_id']) ?></code></td>
          <td class="trunc"><?= h($w['chat_title'] ?: $w['chat_id']) ?></td>
          <td class="trunc"><?= h($w['reason'] ?: '—') ?></td>
          <td><span class="badge-pill badge-gray"><?= h($w['warned_by'] ?: '—') ?></span></td>
          <td style="font-size:12px"><?= is_numeric($w['created_at']) ? date('d/m/Y H:i', (int)$w['created_at']) : date('d/m/Y H:i', strtotime($w['created_at'])) ?></td>
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
