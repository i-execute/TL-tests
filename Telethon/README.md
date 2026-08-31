# Telethon — MTProto Layer Testing

MTProto protocol layer experiments using Telethon async client.

## Purpose

Test MTProto-level features:
- Event handlers (message, callback, inline query)
- Rich text with `MessageEntity` (bold, italic, code, pre, etc.)
- Inline keyboards with buttons (callback, URL, switch_inline)
- Media handling (photo, video, document, voice)
- Custom emoji via MTProto (premium support)
- Client-side updates and synchronization

## Structure

- `client_setup/` — Telethon initialization, session persistence
- `event_handlers/` — Message, callback, inline query handlers
- `media/` — Photo, video, document uploads/downloads
- `keyboards/` — Button building, callback data encoding
- `entities/` — MessageEntity formatting (bold, italic, code, pre)

## Status

Placeholder. Ready for test implementations.
