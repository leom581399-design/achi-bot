<?php
$search  = trim($_GET['q'] ?? '');
$perPage = 20;
$curPage = max(1, (int)($_GET['p'] ?? 1));

if (!tableExists('groups')) {
    echo '<div class="empty"><div class="icon">⚠</div><p>Tabela <code>groups</code> não encontrada.</p></div>';
    return;
}

$where  = '';
$params = [];
if ($search !== '') {
    $where    = "WHERE title LIKE ? OR id LIKE ?";
    $params   = ["%{$search}%", "%{$search}%"];
}

$total  = (int)dbScalar("SELECT COUNT(*) FROM groups {$where}", $params);
['pages' => $pages, 'offset' => $offset] = paginate($total, $curPage, $perPage);

$rows = dbQuery(
    "SELECT g.id as chat_id, g.title, g.username, g.type, g.member_count,
            (SELECT COUNT(*) FROM bans b WHERE b.chat_id = g.id AND b.active = 1) as ban_count,
            (SELECT COUNT(*) FROM warns w WHERE w.chat_id = g.id) as warn_count,
            (SELECT COUNT(*) FROM notes n WHERE n.chat_id = g.id) as note_count
     FROM groups g {$where}
     ORDER BY g.title ASC
     LIMIT {$perPage} OFFSET {$offset}",
    $params
);
?>

<div class="table-wrap">
  <div class="table-header">
    <h3>Grupos Monitorados <span class="badge-pill badge-gray"><?= $total ?></span></h3>
    <form class="search-bar" method="get">
      <input type="hidden" name="page" value="groups">
      <input type="text" name="q" placeholder="Buscar por nome ou ID…" value="<?= h($search) ?>">
      <button type="submit">Buscar</button>
      <?php if ($search): ?><a href="?page=groups" style="color:var(--muted);font-size:12px;text-decoration:none">✕ Limpar</a><?php endif; ?>
    </form>
  </div>

  <div class="table-container">
    <?php if (empty($rows)): ?>
      <div class="empty"><div class="icon">◉</div><p>Nenhum grupo encontrado.</p></div>
    <?php else: ?>
    <table>
      <thead>
        <tr>
          <th>Grupo</th>
          <th>Chat ID</th>
          <th>Tipo</th>
          <th>Membros</th>
          <th>Atividade</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($rows as $g): ?>
        <tr>
          <td>
            <div style="display:flex;align-items:center;gap:12px">
              <div style="width:36px;height:36px;background:var(--bg);border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--accent);border:1px solid var(--border)">
                <?= mb_strtoupper(mb_substr($g['title'] ?: '?', 0, 1)) ?>
              </div>
              <div>
                <strong><?= h($g['title'] ?: 'Sem título') ?></strong>
                <?php if ($g['username']): ?><br><span style="font-size:11px;color:var(--muted)">@<?= h($g['username']) ?></span><?php endif; ?>
              </div>
            </div>
          </td>
          <td><code style="font-size:12px;color:var(--muted)"><?= h($g['chat_id']) ?></code></td>
          <td><span class="badge-pill badge-gray"><?= h($g['type'] ?? 'group') ?></span></td>
          <td><strong><?= number_format((int)$g['member_count']) ?></strong></td>
          <td>
            <div style="display:flex;gap:6px">
              <span class="badge-pill badge-red" title="Bans"><?= $g['ban_count'] ?></span>
              <span class="badge-pill badge-yellow" title="Warns"><?= $g['warn_count'] ?></span>
              <span class="badge-pill badge-blue" title="Notas"><?= $g['note_count'] ?></span>
            </div>
          </td>
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
