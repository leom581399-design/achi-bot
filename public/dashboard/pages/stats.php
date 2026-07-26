<?php
$chatId  = trim($_GET['chat'] ?? '');
$perPage = 20;
$curPage = max(1, (int)($_GET['p'] ?? 1));

if (!tableExists('message_stats')) {
    echo '<div class="empty"><div class="icon">📊</div><p>Sem dados de estatísticas disponíveis.</p></div>';
    return;
}

$groups = dbQuery(
    'SELECT ms.chat_id, g.title, SUM(ms.msg_count) as total
     FROM message_stats ms
     LEFT JOIN groups g ON g.id = ms.chat_id
     GROUP BY ms.chat_id
     ORDER BY total DESC'
);

$conditions = [];
$params     = [];
if ($chatId !== '') {
    $conditions[] = 'ms.chat_id = ?';
    $params[]     = $chatId;
}
$where = $conditions ? 'WHERE ' . implode(' AND ', $conditions) : '';

$total = (int)dbScalar(
    "SELECT COUNT(*) FROM (SELECT user_id FROM message_stats {$where} GROUP BY user_id) t",
    $params
);
['pages' => $pages, 'offset' => $offset] = paginate($total, $curPage, $perPage);

$rows = dbQuery(
    "SELECT ms.user_id, SUM(ms.msg_count) as total
     FROM message_stats ms
     {$where}
     GROUP BY ms.user_id
     ORDER BY total DESC
     LIMIT {$perPage} OFFSET {$offset}",
    $params
);

$medals = ['🥇', '🥈', '🥉'];
$startRank = ($curPage - 1) * $perPage + 1;
?>

<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px;align-items:center">
  <a href="?page=stats" class="badge-pill <?= !$chatId ? 'badge-blue' : 'badge-gray' ?>" style="text-decoration:none">Todos os Grupos</a>
  <?php foreach ($groups as $g): ?>
    <a href="<?= h(currentUrl(['chat' => $g['chat_id'], 'p' => 1])) ?>"
       class="badge-pill <?= $chatId == $g['chat_id'] ? 'badge-blue' : 'badge-gray' ?>"
       style="text-decoration:none; display:flex; align-items:center; gap:6px">
      <?= h($g['title'] ?: $g['chat_id']) ?>
      <span style="opacity:0.6; font-size:10px"><?= number_format((int)$g['total']) ?></span>
    </a>
  <?php endforeach; ?>
</div>

<div class="table-wrap">
  <div class="table-header">
    <h3>Ranking de Atividade <span class="badge-pill badge-gray"><?= $total ?> usuários</span></h3>
  </div>
  <div class="table-container">
    <?php if (empty($rows)): ?>
      <div class="empty"><div class="icon">📈</div><p>Nenhuma estatística encontrada para este filtro.</p></div>
    <?php else: ?>
    <table>
      <thead>
        <tr>
          <th style="width:60px">Pos</th>
          <th>User ID</th>
          <th>Mensagens</th>
          <th>Participação</th>
        </tr>
      </thead>
      <tbody>
        <?php 
        $maxMsgs = (int)($rows[0]['total'] ?? 1);
        foreach ($rows as $i => $r): 
          $rank = $startRank + $i;
          $percent = $maxMsgs > 0 ? round(((int)$r['total'] / $maxMsgs) * 100) : 0;
        ?>
        <tr>
          <td style="font-size:18px; font-weight:700"><?= $medals[$rank - 1] ?? $rank . 'º' ?></td>
          <td><code style="color:var(--accent)"><?= h($r['user_id']) ?></code></td>
          <td><strong><?= number_format((int)$r['total']) ?></strong></td>
          <td style="width:200px">
            <div style="width:100%; height:6px; background:rgba(255,255,255,0.05); border-radius:10px; overflow:hidden">
              <div style="width:<?= $percent ?>%; height:100%; background:var(--accent); border-radius:10px"></div>
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
