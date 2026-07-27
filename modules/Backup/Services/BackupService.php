<?php
declare(strict_types=1);

namespace Modules\Backup\Services;

use App\Core\Application;
use App\Core\Services\{DatabaseService, LoggerService, SettingsService};

/**
 * BackupService — serializa e restaura toda a configuração de um grupo.
 *
 * O backup inclui:
 *  - Configurações de módulos (group_settings)
 *  - Notas salvas
 *  - Filtros de palavras
 *  - Regras do grupo
 *  - Advertências ativas
 *  - Bans ativos
 *  - Silenciamentos ativos
 */
class BackupService
{
    private const VERSION = 1;

    public function __construct(private readonly Application $app) {}

    // -------------------------------------------------------------------------
    // Export
    // -------------------------------------------------------------------------

    /**
     * Gera o array de backup completo de um grupo.
     */
    public function export(int $chatId): array
    {
        $db = $this->app->make(DatabaseService::class);

        return [
            'version'    => self::VERSION,
            'chat_id'    => $chatId,
            'exported_at'=> date('c'),
            'settings'   => $this->exportSettings($chatId, $db),
            'notes'      => $this->exportTable($db, 'notes',   $chatId),
            'filters'    => $this->exportTable($db, 'filters', $chatId),
            'rules'      => $this->exportRules($chatId, $db),
            'warns'      => $this->exportTable($db, 'warns',   $chatId),
            'bans'       => $this->exportTable($db, 'bans',    $chatId),
            'mutes'      => $this->exportTable($db, 'mutes',   $chatId),
        ];
    }

    /**
     * Serializa o backup para JSON compacto.
     */
    public function toJson(array $data): string
    {
        return json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    // -------------------------------------------------------------------------
    // Import / Restore
    // -------------------------------------------------------------------------

    /**
     * Valida e aplica um backup JSON a um grupo.
     * Retorna um array com estatísticas de restauração.
     *
     * @throws \InvalidArgumentException se o JSON for inválido ou incompatível
     */
    public function import(int $chatId, string $json): array
    {
        $data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);

        $this->validate($data);

        $db    = $this->app->make(DatabaseService::class);
        $stats = [];

        // Settings
        $stats['settings'] = $this->restoreSettings($chatId, $data['settings'] ?? [], $db);

        // Notes
        $stats['notes']   = $this->restoreTable($chatId, 'notes',   $data['notes']   ?? [], $db, ['chat_id', 'name', 'content', 'created_by']);
        $stats['filters'] = $this->restoreTable($chatId, 'filters', $data['filters'] ?? [], $db, ['chat_id', 'keyword', 'response', 'created_by']);
        $stats['warns']   = $this->restoreTable($chatId, 'warns',   $data['warns']   ?? [], $db, ['chat_id', 'user_id', 'reason', 'warned_by']);
        $stats['bans']    = $this->restoreTable($chatId, 'bans',    $data['bans']    ?? [], $db, ['chat_id', 'user_id', 'reason', 'banned_by']);
        $stats['mutes']   = $this->restoreTable($chatId, 'mutes',   $data['mutes']   ?? [], $db, ['chat_id', 'user_id', 'reason', 'muted_by']);
        $stats['rules']   = $this->restoreRules($chatId, $data['rules'] ?? null, $db);

        $this->app->make(LoggerService::class)->security(
            "BACKUP_RESTORE chat={$chatId} settings={$stats['settings']} notes={$stats['notes']} filters={$stats['filters']}"
        );

        // Invalidate settings cache
        if ($this->app->has(SettingsService::class)) {
            $this->app->make(SettingsService::class)->invalidate($chatId);
        }

        return $stats;
    }

    // -------------------------------------------------------------------------
    // Internals — export helpers
    // -------------------------------------------------------------------------

    private function exportSettings(int $chatId, DatabaseService $db): array
    {
        try {
            return $db->table('group_settings')
                ->where('chat_id', $chatId)
                ->get();
        } catch (\Throwable) {
            return [];
        }
    }

    private function exportTable(DatabaseService $db, string $table, int $chatId): array
    {
        try {
            return $db->table($table)
                ->where('chat_id', $chatId)
                ->get();
        } catch (\Throwable) {
            return [];
        }
    }

    private function exportRules(int $chatId, DatabaseService $db): ?array
    {
        try {
            $row = $db->table('group_settings')
                ->where('chat_id', $chatId)
                ->where('module', 'Rules')
                ->where('key', 'text')
                ->first();
            return $row ? ['text' => json_decode((string)$row['value'], true)] : null;
        } catch (\Throwable) {
            return null;
        }
    }

    // -------------------------------------------------------------------------
    // Internals — restore helpers
    // -------------------------------------------------------------------------

    private function validate(mixed $data): void
    {
        if (!is_array($data)) {
            throw new \InvalidArgumentException("Yaroqsiz zaxira fayli.");
        }
        if (!isset($data['version']) || (int)$data['version'] !== self::VERSION) {
            throw new \InvalidArgumentException(
                "Zaxira versiyasi mos emas. Kutilgan versiya: " . self::VERSION
            );
        }
        if (!isset($data['chat_id'])) {
            throw new \InvalidArgumentException("Zaxirada chat_id yo'q — fayl buzilgan.");
        }
    }

    /**
     * Restaura configurações de módulos.
     * Apaga as existentes do grupo e insere as do backup.
     */
    private function restoreSettings(int $chatId, array $rows, DatabaseService $db): int
    {
        try {
            $db->table('group_settings')->where('chat_id', $chatId)->delete();
        } catch (\Throwable) {}

        $count = 0;
        foreach ($rows as $row) {
            try {
                $driver = $db->driver();
                if ($driver === 'pgsql') {
                    $db->statement(
                        "INSERT INTO group_settings (chat_id, module, key, value)
                         VALUES (:c, :m, :k, :v)
                         ON CONFLICT (chat_id, module, key) DO UPDATE SET value = EXCLUDED.value",
                        [':c' => $chatId, ':m' => $row['module'], ':k' => $row['key'], ':v' => $row['value']]
                    );
                } else {
                    $db->statement(
                        "INSERT OR REPLACE INTO group_settings (chat_id, module, key, value)
                         VALUES (:c, :m, :k, :v)",
                        [':c' => $chatId, ':m' => $row['module'], ':k' => $row['key'], ':v' => $row['value']]
                    );
                }
                $count++;
            } catch (\Throwable) {}
        }
        return $count;
    }

    /**
     * Restaura uma tabela genérica: remove registros existentes do grupo e reinsere.
     * Apenas as colunas declaradas em $columns são copiadas (segurança).
     */
    private function restoreTable(int $chatId, string $table, array $rows, DatabaseService $db, array $columns): int
    {
        try {
            $db->table($table)->where('chat_id', $chatId)->delete();
        } catch (\Throwable) {}

        $count = 0;
        foreach ($rows as $row) {
            try {
                $insert = ['chat_id' => $chatId];
                foreach ($columns as $col) {
                    if ($col === 'chat_id') continue;
                    if (isset($row[$col])) $insert[$col] = $row[$col];
                }
                $db->table($table)->insert($insert);
                $count++;
            } catch (\Throwable) {}
        }
        return $count;
    }

    private function restoreRules(int $chatId, ?array $rules, DatabaseService $db): int
    {
        if ($rules === null || !isset($rules['text'])) return 0;
        try {
            $value = json_encode($rules['text'], JSON_UNESCAPED_UNICODE);
            $driver = $db->driver();
            if ($driver === 'pgsql') {
                $db->statement(
                    "INSERT INTO group_settings (chat_id, module, key, value)
                     VALUES (:c, 'Rules', 'text', :v)
                     ON CONFLICT (chat_id, module, key) DO UPDATE SET value = EXCLUDED.value",
                    [':c' => $chatId, ':v' => $value]
                );
            } else {
                $db->statement(
                    "INSERT OR REPLACE INTO group_settings (chat_id, module, key, value)
                     VALUES (:c, 'Rules', 'text', :v)",
                    [':c' => $chatId, ':v' => $value]
                );
            }
            return 1;
        } catch (\Throwable) {
            return 0;
        }
    }
}
