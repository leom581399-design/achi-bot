<?php
$search  = trim($_GET['q'] ?? '');
$chatId  = trim($_GET['chat'] ?? '');
$perPage = 20;
$curPage = max(1, (int)($_GET['p'] ?? 1));

if (!tableExists('notes')) {
    echo '<div class="empty"><div class="icon">⚠</div><p>Tabela <code>notes</code> não encontrada.</p></div>';
    return;
}

$conditions = [];
$params     = [];

if ($chatId !== '') {
    $conditions[] = 'n.chat_id = ?';
    $params[]     = $chatId;
}
if ($search !== '') {
    $conditions[] = '(n.name LIKE ? OR n.content LIKE ? OR g.title LIKE ?)';
    $params[] = "%{$search}%";
    $params[] = "%{$search}%";
    $params[] = "%{$search}%";
}

$where = $conditions ? 'WHERE ' . implode(' AND ', $conditions) : '';

$total = (int)dbScalar("SELECT COUNT(*) FROM notes n LEFT JOIN groups g ON g.id = n.chat_id {$where}", $params);
['pages' => $pages, 'offset' => $offset] = paginate($total, $curPage, $perPage);

$rows = dbQuery(
    "SELECT n.*, g.title as chat_title 
     FROM notes n 
     LEFT JOIN groups g ON g.id = n.chat_id
     {$where}
     ORDER BY n.chat_id, n.name ASC
     LIMIT {$perPage} OFFSET {$offset}",
    $params
);

$topGroups = dbQuery(
    'SELECT n.chat_id, g.title, COUNT(*) as cnt
     FROM notes n LEFT JOIN groups g ON g.id = n.chat_id
     GROUP BY n.chat_id ORDER BY cnt DESC LIMIT 8'
);
?>

<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px">
  <?php foreach ($topGroups as $tg): ?>
    <a href="<?= h(currentUrl(['chat' => $tg['chat_id'], 'p' => 1])) ?>"
       class="badge-pill <?= $chatId == $tg['chat_id'] ? 'badge-blue' : 'badge-gray' ?>"
       style="text-decoration:none; display:flex; align-items:center; gap:6px">
      <?= h($tg['title'] ?: $tg['chat_id']) ?>
      <span style="opacity:0.6; font-size:10px"><?= (int)$tg['cnt'] ?></span>
    </a>
  <?php endforeach; ?>
</div>

<div class="table-wrap">
  <div class="table-header">
    <h3>Notas Salvas <span class="badge-pill badge-gray"><?= $total ?></span></h3>
    <form class="search-bar" method="get">
      <input type="hidden" name="page" value="notes">
      <?php if ($chatId): ?><input type="hidden" name="chat" value="<?= h($chatId) ?>"><?php endif; ?>
      <input type="text" name="q" placeholder="Nome ou conteúdo…" value="<?= h($search) ?>">
      <button type="submit">Buscar</button>
      <?php if ($search || $chatId): ?><a href="?page=notes" style="color:var(--muted);font-size:12px;text-decoration:none">✕</a><?php endif; ?>
    </form>
  </div>

  <div class="table-container">
    <?php if (empty($rows)): ?>
      <div class="empty"><div class="icon">◈</div><p>Nenhuma nota encontrada.</p></div>
    <?php else: ?>
    <table>
      <thead>
        <tr>
          <th>Nome</th>
          <th>Grupo</th>
          <th>Conteúdo</th>
          <th>Criada por</th>
          <th>Data</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($rows as $n): ?>
        <tr>
          <td><strong style="color:var(--accent)">#<?= h($n['name']) ?></strong></td>
          <td class="trunc"><?= h($n['chat_title'] ?: $n['chat_id']) ?></td>
          <td class="trunc" style="max-width:300px; color:var(--muted)"><?= h(mb_substr($n['content'] ?? '', 0, 80)) ?>...</td>
          <td><span class="badge-pill badge-gray"><?= h($n['created_by'] ?: '—') ?></span></td>
          <td style="font-size:12px"><?= is_numeric($n['created_at']) ? date('d/m/Y', (int)$n['created_at']) : date('d/m/Y', strtotime($n['created_at'])) ?></td>
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
