# API 10.3 Showcase

Bot API 10.3 rich messages interactive demonstration with streaming animations, LaTeX math, custom emoji, maps, and live system stats.

## File: demo_bot_api_10_3.py

A production-ready Bot API 10.3 client using long polling with premium features:

### Key Features

**Rich Messages (HTML)**
- Headings (`<h1>` — `<h6>`)
- Blockquotes, tables, lists, code blocks with syntax highlighting
- Collapsible details (`<details>/<summary>`)
- Asides/citations (`<aside>`, `<cite>`)

**Custom Premium Emoji**
- 103 verified emoji IDs from user's Telegram premium library
- Integrated via `<tg-emoji emoji-id="ID">glyph</tg-emoji>` tags
- Categories: Positive, Neutral, Analysis, Thinking, Happy, Surprised, Negative

**Streaming Drafts**
- `sendRichMessageDraft` API for animated frame progression
- `<tg-thinking>` tags show AI thinking animation
- NLP pipeline demo: Causal LM (next-token) + Masked LM (attention)
- Glitch effect text overlays for visual impact

**LaTeX Mathematics**
- Schrödinger equation: `iℏ ∂Ψ/∂t = Ĥ Ψ`
- Navier-Stokes (fluid dynamics)
- Einstein field equations (general relativity)
- Inline formulas with high precision: `G ≈ 6.674 × 10⁻¹¹ N·m²/kg²`

**Interactive Maps**
- `<tg-map>` geo-coordinates rendering
- Example: Tokyo, Japan (35.6895° N, 139.6917° E)
- Zoom levels support

**System Monitoring**
- Real-time CPU load averages from `/proc/loadavg`
- Memory usage (total/free/buffers/cached) from `/proc/meminfo`
- System uptime from `/proc/uptime`
- Visual progress bars (filled/empty blocks: `█░`)

**Interactive Buttons**
- Callback queries with `<tg-button-row>` layout
- Menu navigation (back, submit, refresh)
- Data encoding via base64 (optional)

### Menu Hierarchy

```
/start
  ↓
Main Menu (Ultimate Bot API 10.3 Showcase)
  ├─ Формат (Format Demo)
  ├─ Math (Equations)
  ├─ Карта (Map)
  ├─ NLP Stream (Streaming Animation)
  ├─ Stats (System Dashboard)
  └─ Options (Model Selection)
```

**NLP Stream Demo Flow:**
1. Causal LM: "The cat sat on the mat." (word-by-word with glitch animation)
2. Masked LM: "The quick brown fox jumps over the lazy dog." (attention visualization)
3. Final summary: Pangram score, bidirectional transformer, latency metrics

### Error Handling

- Rate limiting (429) with exponential backoff
- Retry logic (3 attempts) for transient network errors
- API error logging with response codes
- Exception tracing for debugging

### Configuration

Edit line 11:
```python
TOKEN = "YOUR_BOT_TOKEN_HERE"
```

### Running

```bash
python3 demo_bot_api_10_3.py
```

Bot will start polling for updates. Send `/start` to activate the menu.

### Dependencies

```
aiohttp>=3.8.0
```

### Tested Protocols

- **Bot API Version:** 10.3
- **Rich Message Format:** HTML with inline formatting
- **Draft Animation:** Async streaming frames with 0.5-2s delays
- **Custom Emoji:** Premium IDs only (verified registry)

### Limitations & Notes

- Long polling (simpler than webhooks; ~1s update latency)
- Draft animations work best in DMs (not groups/channels)
- `<tg-thinking>` only in drafts; removed before final send
- LaTeX requires official Telegram client support
- Maps require geo-coordinates (latitude, longitude, zoom)

---

**Status:** Production-ready  
**Last Updated:** 2026-08-31  
**API Compatibility:** Telegram Bot API 10.3+
