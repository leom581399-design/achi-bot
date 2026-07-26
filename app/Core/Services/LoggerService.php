<?php
declare(strict_types=1);

namespace App\Core\Services;

/**
 * Simple PSR-3-inspired logger that writes to STDOUT/STDERR and to log files.
 *
 * Log files:
 *   logs/telegram.log — debug/info/warning
 *   logs/error.log    — error/critical
 *   logs/security.log — explicit security events
 */
class LoggerService
{
    private const LEVELS = [
        'debug'    => 0,
        'info'     => 1,
        'warning'  => 2,
        'error'    => 3,
        'critical' => 4,
    ];

    private int $minLevelValue;

    public function __construct(
        private readonly string $logDir,
        string $minLevel = 'info'
    ) {
        if (!is_dir($logDir)) {
            mkdir($logDir, 0755, true);
        }
        $this->minLevelValue = self::LEVELS[$minLevel] ?? 1;
    }

    public function debug(string $message, array $context = []): void
    {
        $this->log('debug', $message, $context);
    }

    public function info(string $message, array $context = []): void
    {
        $this->log('info', $message, $context);
    }

    public function warning(string $message, array $context = []): void
    {
        $this->log('warning', $message, $context);
    }

    public function error(string $message, array $context = []): void
    {
        $this->log('error', $message, $context);
    }

    public function critical(string $message, array $context = []): void
    {
        $this->log('critical', $message, $context);
    }

    public function security(string $message, array $context = []): void
    {
        $line = $this->format('security', $message, $context);
        file_put_contents($this->logDir . '/security.log', $line, FILE_APPEND | LOCK_EX);
        fwrite(STDOUT, $line);
    }

    // -------------------------------------------------------------------------

    private function log(string $level, string $message, array $context): void
    {
        if ((self::LEVELS[$level] ?? 0) < $this->minLevelValue) return;

        $line   = $this->format($level, $message, $context);
        $stream = in_array($level, ['error', 'critical'], true) ? STDERR : STDOUT;

        fwrite($stream, $line);

        $file = in_array($level, ['error', 'critical'], true)
            ? $this->logDir . '/error.log'
            : $this->logDir . '/telegram.log';

        file_put_contents($file, $line, FILE_APPEND | LOCK_EX);
    }

    private function format(string $level, string $message, array $context): string
    {
        $ts      = date('Y-m-d H:i:s');
        $ctx     = empty($context) ? '' : ' ' . json_encode($context, JSON_UNESCAPED_UNICODE);
        $lvlUC   = strtoupper(str_pad($level, 8));
        return "[{$ts}] [{$lvlUC}] {$message}{$ctx}" . PHP_EOL;
    }
}
