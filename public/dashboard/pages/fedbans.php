<?php
$fedId   = trim($_GET['fed'] ?? '');
$search  = trim($_GET['q'] ?? '');
$perPage = 20;
$curPage = max(1, (int)($_GET['p'] ?? 1));

if (!tableExists('federations')) {
    echo '<div class="empty"><div class="icon">⊗</div><p>Tabela <code>federations</code> não encontrada.</p></div>';
    return;
}

$feds = dbQuery(
    'SELECT f.id, f.name, f.owner_id, f.created_at,
            (SELECT COUNT(*) FROM fed_chats fc WHERE fc.fed_id = f.id) as chat_count,
            (SELECT COUNT(*) FROM fed_bans fb WHERE fb.fed_id = f.id) as ban_count
     FROM federations f
     ORDER BY f.name'
);

$conditions = [];
$params     = [];
if ($fedId !== '') {
    $conditions[] = 'fb.fed_id = ?';
    $params[]     = $fedId;
}
if ($search !== '') {
    $conditions[] = '(fb.user_id LIKE ? OR fb.reason LIKE ?)';
    $params[] = "%{$search}%";
    $params[] = "%{$search}%";
}
$where = $conditions ? 'WHERE ' . implode(' AND ', $conditions) : '';

$total = (int)dbScalar("SELECT COUNT(*) FROM fed_bans fb {$where}", $params);
['pages' => $pages, 'offset' => $offset] = paginate($total, $curPage, $perPage);

$rows = dbQuery(
    "SELECT fb.*, f.name as fed_name 
     FROM fed_bans fb 
     LEFT JOIN federations f ON f.id = fb.fed_id
     {$where}
     ORDER BY fb.created_at DESC
     LIMIT {$perPage} OFFSET {$offset}",
    $params
);
?>

<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;margin-bottom:24px">
  <?php foreach ($feds as $f): ?>
    <a href="<?= h(currentUrl(['fed' => $f['id'], 'p' => 1, 'q' => ''])) ?>"
       class="card <?= $fedId == $f['id'] ? 'accent' : '' ?>" style="text-decoration:none; padding:16px">
      <div style="font-size:14px;font-weight:700;color:#fff;margin-bottom:8px"><?= h($f['name']) ?></div>
      <div style="display:flex;gap:6px">
        <span class="badge-pill badge-red"><?= (int)$f['ban_count'] ?> bans</span>
        <span class="badge-pill badge-gray"><?= (int)$f['chat_count'] ?> grupos</span>
      </div>
      <div style="font-size:11px;color:var(--muted);margin-top:10px">
        Owner: <code><?= h($f['owner_id']) ?></code>
      </div>
    </a>
  <?php endforeach; ?>
</div>

<div class="table-wrap">
  <div class="table-header">
    <h3>Banimentos Globais <span class="badge-pill badge-red"><?= $total ?></span></h3>
    <form class="search-bar" method="get">
      <input type="hidden" name="page" value="fedbans">
      <?php if ($fedId): ?><input type="hidden" name="fed" value="<?= h($fedId) ?>"><?php endif; ?>
      <input type="text" name="q" placeholder="Buscar ID ou motivo…" value="<?= h($search) ?>">
      <button type="submit">Buscar</button>
      <?php if ($search || $fedId): ?><a href="?page=fedbans" style="color:var(--muted);font-size:12px;text-decoration:none">✕</a><?php endif; ?>
    </form>
  </div>

  <div class="table-container">
    <?php if (empty($rows)): ?>
      <div class="empty"><div class="icon">⊗</div><p>Nenhum banimento global encontrado.</p></div>
    <?php else: ?>
    <table>
      <thead>
        <tr>
          <th>User ID</th>
          <th>Federação</th>
          <th>Motivo</th>
          <th>Banido por</th>
          <th>Data</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($rows as $fb): ?>
        <tr>
          <td><code style="color:var(--danger)"><?= h($fb['user_id']) ?></code></td>
          <td><span class="badge-pill badge-blue"><?= h($fb['fed_name'] ?? $fb['fed_id']) ?></span></td>
          <td class="trunc"><?= h($fb['reason'] ?: '—') ?></td>
          <td><span class="badge-pill badge-gray"><?= h($fb['banned_by'] ?: '—') ?></span></td>
          <td style="font-size:12px"><?= is_numeric($fb['created_at']) ? date('d/m/Y H:i', (int)$fb['created_at']) : date('d/m/Y H:i', strtotime($fb['created_at'])) ?></td>
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
