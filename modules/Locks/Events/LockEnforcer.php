<?php
declare(strict_types=1);

namespace Modules\Locks\Events;

use App\Core\Application;
use App\Core\Services\{LoggerService, TelegramService};
use App\Core\Telegram\TelegramClient;
use App\Core\Update;
use Modules\Locks\Services\LockService;

/**
 * Ouve message.received e deleta mensagens que violam os locks ativos.
 * Admins são isentos.
 */
class LockEnforcer
{
    public function __construct(private readonly Application $app) {}

    public function __invoke(mixed $data): void
    {
        $this->handle(is_array($data) ? $data : []);
    }

    public function handle(array $data): void
    {
        /** @var Update $update */
        $update = $data['update'] ?? null;
        if ($update === null || !$update->isGroup()) return;

        $chatId = $update->getChatId();
        $userId = $update->getUserId();

        // Admins não são afetados pelos locks
        $telegram = $this->app->make(TelegramService::class);
        if ($telegram->isAdmin($chatId, $userId)) return;

        $service = $this->app->make(LockService::class);

        $type = $this->detectMessageType($update);
        if ($type === null) return;

        if ($service->isLocked($chatId, $type)) {
            $this->deleteMessage($chatId, $update->getMessageId());
            $this->app->make(LoggerService::class)->info(
                "LOCK_ENFORCED chat={$chatId} user={$userId} type={$type}"
            );
        }
    }

    /** Detecta o tipo de conteúdo da mensagem para comparar com os locks. */
    private function detectMessageType(Update $update): ?string
    {
        // 'all' é um super-tipo — verificado via isLocked
        if ($update->isForward())                return 'forward';
        if ($update->getSticker() !== null)       return 'sticker';
        if ($update->getAnimation() !== null)     return 'gif';
        if ($update->getPhoto() !== null)         return 'photo';
        if ($update->getVideo() !== null)         return 'video';
        if ($update->getVoice() !== null)         return 'voice';
        if ($update->getDocument() !== null)      return 'media';
        if ($update->getAudio() !== null)         return 'media';
        if ($update->getPoll() !== null)          return 'poll';
        if ($update->getContact() !== null)       return 'contact';
        if ($update->getLocation() !== null)      return 'location';

        $msg = $update->message ?? $update->editedMessage ?? null;
        if ($msg === null) return null;

        if (isset($msg['game']))                  return 'game';

        // Inline keyboard (botões)
        if (isset($msg['reply_markup']['inline_keyboard'])) return 'inline';

        // URL na mensagem
        foreach ($update->getEntities() as $entity) {
            if (in_array($entity['type'], ['url', 'text_link'], true)) return 'url';
        }

        // Texto puro
        $text = $update->getText();
        if ($text !== null && !$update->isCommand()) return 'text';

        return null;
    }

    private function deleteMessage(int $chatId, ?int $messageId): void
    {
        if ($messageId === null) return;
        try {
            $this->app->make(TelegramClient::class)->deleteMessage($chatId, $messageId);
        } catch (\Throwable) {
            // ignora falhas de deleção (mensagem já deletada, sem permissão, etc.)
        }
    }
}
