<?php
declare(strict_types=1);

namespace App\Core;

/**
 * Wraps a raw Telegram update payload and exposes typed accessors.
 * Modules and commands always receive an Update, never a raw array.
 */
class Update
{
    public readonly string $type;
    public readonly int    $updateId;

    public readonly ?array $message;
    public readonly ?array $editedMessage;
    public readonly ?array $callbackQuery;
    public readonly ?array $inlineQuery;
    public readonly ?array $chatMember;
    public readonly ?array $myChatMember;

    public function __construct(public readonly array $data)
    {
        $this->updateId      = $data['update_id'];
        $this->message       = $data['message']         ?? null;
        $this->editedMessage = $data['edited_message']  ?? null;
        $this->callbackQuery = $data['callback_query']  ?? null;
        $this->inlineQuery   = $data['inline_query']    ?? null;
        $this->chatMember    = $data['chat_member']     ?? null;
        $this->myChatMember  = $data['my_chat_member']  ?? null;

        $this->type = match(true) {
            isset($data['message'])         => 'message',
            isset($data['edited_message'])  => 'edited_message',
            isset($data['callback_query'])  => 'callback_query',
            isset($data['inline_query'])    => 'inline_query',
            isset($data['chat_member'])     => 'chat_member',
            isset($data['my_chat_member'])  => 'my_chat_member',
            default                         => 'unknown',
        };
    }

    // -------------------------------------------------------------------------
    // Command detection
    // -------------------------------------------------------------------------

    public function isCommand(): bool
    {
        if ($this->type !== 'message') return false;
        $text = $this->message['text'] ?? '';
        return str_starts_with($text, '/');
    }

    /** Returns the command name without the leading slash and without @BotName suffix. */
    public function getCommand(): ?string
    {
        if (!$this->isCommand()) return null;
        $text    = $this->message['text'] ?? '';
        $parts   = explode(' ', $text, 2);
        $command = explode('@', $parts[0])[0];
        return strtolower(ltrim($command, '/'));
    }

    /** Returns everything after the command (the arguments string). */
    public function getCommandArgs(): string
    {
        if (!$this->isCommand()) return '';
        $text  = $this->message['text'] ?? '';
        $parts = explode(' ', $text, 2);
        return trim($parts[1] ?? '');
    }

    // -------------------------------------------------------------------------
    // Common accessors
    // -------------------------------------------------------------------------

    public function getChatId(): ?int
    {
        return match($this->type) {
            'message'        => $this->message['chat']['id']                   ?? null,
            'edited_message' => $this->editedMessage['chat']['id']             ?? null,
            'callback_query' => $this->callbackQuery['message']['chat']['id']  ?? null,
            default          => null,
        };
    }

    public function getUserId(): ?int
    {
        return match($this->type) {
            'message'        => $this->message['from']['id']        ?? null,
            'edited_message' => $this->editedMessage['from']['id']  ?? null,
            'callback_query' => $this->callbackQuery['from']['id']  ?? null,
            'inline_query'   => $this->inlineQuery['from']['id']    ?? null,
            default          => null,
        };
    }

    public function getUser(): ?array
    {
        return match($this->type) {
            'message'        => $this->message['from']        ?? null,
            'edited_message' => $this->editedMessage['from']  ?? null,
            'callback_query' => $this->callbackQuery['from']  ?? null,
            'inline_query'   => $this->inlineQuery['from']    ?? null,
            default          => null,
        };
    }

    public function getText(): ?string
    {
        return match($this->type) {
            'message'        => $this->message['text']        ?? null,
            'edited_message' => $this->editedMessage['text']  ?? null,
            'callback_query' => $this->callbackQuery['data']  ?? null,
            default          => null,
        };
    }

    public function getMessageId(): ?int
    {
        return match($this->type) {
            'message'        => $this->message['message_id']                   ?? null,
            'edited_message' => $this->editedMessage['message_id']             ?? null,
            'callback_query' => $this->callbackQuery['message']['message_id']  ?? null,
            default          => null,
        };
    }

    public function getChatType(): ?string
    {
        return match($this->type) {
            'message'        => $this->message['chat']['type']                   ?? null,
            'edited_message' => $this->editedMessage['chat']['type']             ?? null,
            'callback_query' => $this->callbackQuery['message']['chat']['type']  ?? null,
            default          => null,
        };
    }

    public function isGroup(): bool
    {
        return in_array($this->getChatType(), ['group', 'supergroup'], true);
    }

    public function isPrivate(): bool
    {
        return $this->getChatType() === 'private';
    }

    public function isNewChatMember(): bool
    {
        return $this->type === 'message' && !empty($this->message['new_chat_members']);
    }

    public function isLeftChatMember(): bool
    {
        return $this->type === 'message' && isset($this->message['left_chat_member']);
    }

    public function getReplyToMessage(): ?array
    {
        if ($this->type !== 'message') return null;
        return $this->message['reply_to_message'] ?? null;
    }

    /** Shortcut: returns the user mentioned in the replied-to message, if any. */
    public function getReplyToUser(): ?array
    {
        return $this->getReplyToMessage()['from'] ?? null;
    }

    // -------------------------------------------------------------------------
    // Media accessors (Phase 1.5)
    // -------------------------------------------------------------------------

    public function getPhoto(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        if (!$msg) return null;
        $photos = $msg['photo'] ?? null;
        // Return the highest-resolution photo (last element)
        return is_array($photos) ? end($photos) : null;
    }

    public function getVideo(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['video'] ?? null;
    }

    public function getVoice(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['voice'] ?? null;
    }

    public function getAudio(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['audio'] ?? null;
    }

    public function getDocument(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['document'] ?? null;
    }

    public function getSticker(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['sticker'] ?? null;
    }

    public function getAnimation(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['animation'] ?? null;
    }

    public function getPoll(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['poll'] ?? null;
    }

    public function getLocation(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['location'] ?? null;
    }

    public function getContact(): ?array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['contact'] ?? null;
    }

    // -------------------------------------------------------------------------
    // Entities (Phase 1.5)
    // -------------------------------------------------------------------------

    /**
     * Returns message entities (mentions, hashtags, URLs, etc.).
     * Each entity: ['type' => ..., 'offset' => int, 'length' => int, ...]
     */
    public function getEntities(): array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['entities'] ?? [];
    }

    /**
     * Returns caption entities (for photo/video captions).
     */
    public function getCaptionEntities(): array
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['caption_entities'] ?? [];
    }

    /**
     * Returns the caption text of a media message.
     */
    public function getCaption(): ?string
    {
        $msg = $this->message ?? $this->editedMessage;
        return $msg['caption'] ?? null;
    }

    /**
     * Extract user IDs from text_mention entities (users without @username).
     * Returns array of user IDs.
     */
    public function getMentionedUserIds(): array
    {
        $ids = [];
        foreach ($this->getEntities() as $entity) {
            if ($entity['type'] === 'text_mention' && isset($entity['user']['id'])) {
                $ids[] = (int)$entity['user']['id'];
            }
        }
        return $ids;
    }

    /**
     * Extract full user objects from text_mention entities.
     * Returns array of user arrays.
     */
    public function getMentionedUsers(): array
    {
        $users = [];
        foreach ($this->getEntities() as $entity) {
            if ($entity['type'] === 'text_mention' && isset($entity['user'])) {
                $users[] = $entity['user'];
            }
        }
        return $users;
    }

    /**
     * Extract @usernames from mention entities.
     * Returns array of strings without the leading @.
     */
    public function getMentionedUsernames(): array
    {
        $text      = $this->getText() ?? '';
        $usernames = [];

        foreach ($this->getEntities() as $entity) {
            if ($entity['type'] === 'mention') {
                $username    = substr($text, $entity['offset'] + 1, $entity['length'] - 1);
                $usernames[] = $username;
            }
        }

        return $usernames;
    }

    /**
     * Returns true if the message contains media (photo, video, voice, document, sticker).
     */
    public function hasMedia(): bool
    {
        return $this->getPhoto()    !== null
            || $this->getVideo()    !== null
            || $this->getVoice()    !== null
            || $this->getAudio()    !== null
            || $this->getDocument() !== null
            || $this->getSticker()  !== null
            || $this->getAnimation() !== null;
    }

    /**
     * Returns true if the message is a forward.
     */
    public function isForward(): bool
    {
        $msg = $this->message ?? $this->editedMessage;
        return isset($msg['forward_origin']) || isset($msg['forward_from']) || isset($msg['forward_from_chat']);
    }
}
