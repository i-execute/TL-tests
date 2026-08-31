# GoyGram — Custom Async Telegram Implementation

Custom async Telegram client library for specialized use cases.

## Purpose

Build custom async Telegram implementations without external dependencies:
- Lightweight async HTTP client for Bot API
- MTProto protocol implementation (if needed)
- Custom request/response handling
- Streaming and long polling optimization
- Gateway integration

## Structure

- `http_client/` — Custom aiohttp-based Bot API client
- `mtproto/` — MTProto message serialization (TL schema)
- `handlers/` — Event dispatching and routing
- `utils/` — Helpers for JSON, crypto, base64

## Status

Placeholder. Ready for custom implementations.
