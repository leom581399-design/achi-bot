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
    public function getDescription(): string { return 'Start the bot / show welcome message'; }
    public function getPermission(): Permission { return Permission::User; }
    public function getMiddleware(): array   { return []; }

    public function handle(Update $update, Application $app): void
    {
        $user = $update->getUser();
        $name = htmlspecialchars($user['first_name'] ?? 'there');

        $text = "👋 Salom, <b>{$name}</b>!\n\n"
              . "Men <b>ACHI BOT</b> — guruhingizni boshqarishga yordam beruvchi botman.\n\n"
              . "<b>Nima qila olaman:</b>\n"
              . "• 🛡️ Moderatsiya (ban, mute, warn)\n"
              . "• 📝 Eslatma va qoidalarni boshqarish\n"
              . "• 🤖 Avtomatik moderatsiya (flood, spam, captcha)\n"
              . "• 🔒 Xabar turlarini qulflash\n"
              . "• 📊 Guruh statistikasi\n\n"
              . "<b>Buyruqlar:</b>\n"
              . "/help — barcha mavjud buyruqlarni ko'rish\n\n"
              . "<i>Meni guruhingizga qo'shing va admin qiling — shundan keyin ishlashni boshlayman!</i>";

        $app->make(TelegramService::class)->reply($update, $text);
    }
}
