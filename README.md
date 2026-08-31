# TL-tests — Telegram Layers Testing Laboratory

Complete testing and demonstration repository for Telegram Bot API, Telethon, and GoyGram library implementations across different protocol layers.

## Directory Structure

```
TL-tests/
├── BotAPI/
│   └── API_10_3_Showcase/          # Bot API 10.3 features demonstrations
│       └── demo_bot_api_10_3.py    # Rich Messages, streaming drafts, buttons, math
├── Telethon/                       # MTProto layer experiments
├── GoyGram/                        # Custom async implementations
└── README.md
```

## BotAPI/API_10_3_Showcase

**demo_bot_api_10_3.py** — Premium Bot API 10.3 interactive showcase.

### Features Demonstrated

| Feature | Example |
|---------|---------|
| **Rich Messages** | HTML blocks with headings, blockquotes, tables |
| **Custom Emoji** | 103+ verified premium emoji IDs with `<tg-emoji>` tags |
| **Streaming Drafts** | `sendRichMessageDraft` with animated `<tg-thinking>` frames |
| **LaTeX Math** | Schrödinger, Navier-Stokes, Einstein field equations via `<tg-math>` |
| **Interactive Maps** | `<tg-map>` with geo-coordinates |
| **Inline Buttons** | Callback queries with `<tg-button-row>` layout |
| **System Stats** | Real-time `/proc/uptime`, `/proc/meminfo` monitoring |
| **Code Blocks** | Syntax-highlighted Rust, Python examples |
| **Collapsible Details** | `<details>/<summary>` for expandable content |

### Menu Structure

- **Main Menu** → Format, Math, Map, NLP Stream, Stats, Options
- **NLP Pipeline** → Two-stage demo (Causal LM + Masked LM) with glitch animations
- **Stats Dashboard** → Live server uptime, CPU load, memory usage
- **Math Showcase** → Complex physics/engineering equations
- **Options** → Model selection interface

### Running

```bash
# Set token in demo_bot_api_10_3.py (line 11)
TOKEN = "YOUR_BOT_TOKEN_HERE"

# Start polling
python3 demo_bot_api_10_3.py
```

### API Endpoints Used

- `sendRichMessage` — Final rich message delivery
- `sendRichMessageDraft` — Animated streaming with thinking
- `editMessageText` — Menu transitions
- `answerCallbackQuery` — Button feedback
- `getUpdates` — Long polling with 30s timeout

## Telethon

Placeholder for Telethon MTProto layer testing (async `TelegramClient`, event handlers).

## GoyGram

Placeholder for custom async Telegram implementations.

---

**Protocol Versions:**
- Bot API: **10.3** (Rich Messages, LaTeX, Maps, Drafts)
- MTProto: TBD (Telethon subsection)
- Custom: TBD (GoyGram subsection)

**Testing Focus:** Rich formatting, streaming animations, button interactions, system integration.

---

*Created: 2026-08-31*  
*Status: Active Development*
