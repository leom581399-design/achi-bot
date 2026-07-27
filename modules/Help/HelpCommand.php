<?php
declare(strict_types=1);

namespace Modules\Help;

use App\Core\Application;
use App\Core\CommandRegistry;
use App\Core\Contracts\CommandInterface;
use App\Core\Permission;
use App\Core\Services\TelegramService;
use App\Core\Update;

/**
 * /help — Lists all registered commands with their descriptions.
 */
class HelpCommand implements CommandInterface
{
    public function __construct(
        private readonly Application $app
    ) {}

    public function getCommand(): string     { return 'help'; }
    public function getDescription(): string { return 'Barcha mavjud buyruqlarni ko\'rsatadi'; }
    public function getPermission(): Permission { return Permission::User; }
    public function getMiddleware(): array   { return []; }

    public function handle(Update $update, Application $app): void
    {
        $registry = $app->make(CommandRegistry::class);
        $commands = $registry->all();

        $text = "<b>🤖 ACHI BOT — mavjud buyruqlar</b>\n\n";

        foreach ($commands as $cmd) {
            $text .= "/{$cmd->getCommand()} — {$cmd->getDescription()}\n";
        }

        $text .= "\n<i>Eslatma: moderatsiya buyruqlari ishlashi uchun meni guruhingizda admin qiling.</i>";

        // Guruhda bo'lsa - tilni tezkor o'zgartirish tugmasi. Bosilganda
        // LanguageCallbackListener "lang_menu" callback_data'sini qabul
        // qilib, uz/ru tanlash tugmalarini ko'rsatadi (xuddi /til
        // buyrug'i kabi).
        $keyboard = null;
        if ($update->isGroup()) {
            $keyboard = ['inline_keyboard' => [[
                ['text' => "🌐 Tilni o'zgartirish", 'callback_data' => 'lang_menu'],
            ]]];
        }

        $app->make(TelegramService::class)->reply($update, $text, array_filter([
            'reply_markup' => $keyboard,
        ]));
    }
}
