<?php
declare(strict_types=1);

namespace Modules\Start;

use App\Core\Application;
use App\Core\Contracts\CommandInterface;
use App\Core\Permission;
use App\Core\Services\TelegramService;
use App\Core\Update;

/**
 * /start — Welcome message, shown when the bot is first opened in private chat.
 */
class StartCommand implements CommandInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function getCommand(): string     { return 'start'; }
    public function getDescription(): string { return 'Botni ishga tushiradi / xush kelibsiz xabarini ko\'rsatadi'; }
    public function getPermission(): Permission { return Permission::User; }
    public function getMiddleware(): array   { return []; }

    public function handle(Update $update, Application $app): void
    {
        $user = $update->getUser();
        $name = htmlspecialchars($user['first_name'] ?? 'Do\'stim');

        $text = "👋 Salom, <b>{$name}</b>!\n\n"
              . "Men <b>ACHI BOT</b> — guruhingizni boshqarishga yordam beruvchi botman.\n\n"
              . "<b>Nima qila olaman:</b>\n"
              . "• 🛡️ Moderatsiya (ban, mute, warn)\n"
              . "• 📝 Eslatma va qoidalarni boshqarish\n"
              . "• 🤖 Avtomatik moderatsiya (flood, spam, captcha)\n"
              . "• 🔒 Xabar turlarini qulflash\n"
              . "• 📊 Guruh statistikasi\n\n"
              . "<i>Meni guruhingizga qo'shing va admin qiling — shundan keyin ishlashni boshlayman!</i>";

        // Inline tugmalar: /help'ga o'tish uchun qisqa yo'l va guruhga
        // qo'shish tugmasi (Telegram "start-group" tugmasi orqali botni
        // guruhga to'g'ridan-to'g'ri qo'shish oynasini ochadi).
        $me = null;
        try {
            $me = $app->make(\App\Core\Telegram\TelegramClient::class)->getMe();
        } catch (\Throwable) {}

        $buttons = [
            [
                ['text' => "📋 Buyruqlar ro'yxati", 'callback_data' => 'start_help'],
            ],
        ];
        if ($me !== null && isset($me['username'])) {
            $buttons[] = [
                ['text' => "➕ Guruhga qo'shish", 'url' => "https://t.me/{$me['username']}?startgroup=true"],
            ];
        }

        $app->make(TelegramService::class)->reply($update, $text, [
            'reply_markup' => ['inline_keyboard' => $buttons],
        ]);
    }
}
