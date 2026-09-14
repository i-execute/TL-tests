---
name: telegram-buttons-mtproto
description: Use when building Telegram bot buttons via GoyGram MTProto.
---

# Telegram buttons via GoyGram MTProto (layer 229)

Три механизма кнопок, каждый — свой TL-конструктор. Проверено на живом Telegram 2026-09-14.
Эталон: `/home/forget/TL-tests/GoyGram/tests/buttons_all3_test.py` (шлёт 3 сообщения: keyboard / pageButton / textButton, премиум-эмодзи во всех).

## Таблица выбора

| Механизм | Конструкторы | Где рендерится | Тип text |
|---|---|---|---|
| keyboard | replyInlineMarkup → keyboardInlineButtonRow → keyboardInlineButton | ПОД сообщением (reply_markup) | **string, плейн** |
| page | pageBlockButtonRow → pageButton (hex в blocks) | кнопка-БЛОК rich-сообщения | RichText |
| text | textButton (hex внутри RichText абзаца) | ВНУТРИ текста rich-сообщения | RichText |

## Билдеры (рабочий код)

```python
def kb_btn(label, data, style=None, icon=None):  # keyboard: ПОД сообщением
    body = {"_": "keyboardInlineButton", "text": label,  # ПЛЕЙН, НЕ RichText
            "type": ser("inlineButtonTypeCallback", {"data": data.encode().hex()})}
    st = {}
    if style: st[style] = True
    if icon: st["icon"] = ICONS[icon]  # премиум-эмодзи ТОЛЬКО здесь
    if st: body["style"] = ser("keyboardButtonStyle", st)
    return body

markup = {"_": "replyInlineMarkup", "rows":
          [{"_": "keyboardInlineButtonRow", "buttons": row} for row in rows]}
# отправка: messages.sendMessage(..., random_id=..., reply_markup=markup)
```

```python
def page_btn(label, data, style=None, emo=None):  # кнопка-блок rich-сообщения
    text = rt(label) if not emo else concat([emo(emo), rt(" " + label)])
    body = {"text": text, "type": ser("inlineButtonTypeCallback", {"data": data.encode().hex()})}
    if style: body["style"] = ser("richButtonStyle", {style: True})
    return ser("pageButton", body)

row = ser("pageBlockButtonRow", {"align_center": True, "buttons": [...]})
# отправка: rich_message={"_": "inputRichMessage", "blocks": [h, p, row1, row2]}
```

```python
def text_btn(label, data, style=None, emo=None):  # кнопка ВНУТРИ текста
    # как page_btn, но return ser("textButton", body)
# в абзац: ser("pageBlockParagraph", {"text": concat([rt("..."), text_btn(...), rt(" ...")])})
```

## Премиум-эмодзи — главное правило

- **keyboard**: text — ПЛЕЙН-строка, RichText туда нельзя (клиент рисует base64-кашу).
  Премиум = `keyboardButtonStyle.icon` (long = document_id).
- **page/text**: text — RichText, премиум = `textCustomEmoji {"document_id": int, "alt": "💊"}` в textConcat.

Проверенные document_id: 💊 5463081281048818043, 🌡 5463054218459884779, 😴 5462990652943904884,
👍 5465465194056525619, 💩 5465198330558557107, 🚫 5462882007451185227, 👉 5463392464314315076,
🧠 5447595110743168717, 👌 5447363161034346459, 😌 5449619723966761441.

## Стили заливки (проверено на живом клиенте)

- `keyboardButtonStyle`: bg_primary, bg_danger, bg_success, icon
- `richButtonStyle`: bg_primary, bg_danger, bg_success, link
- Рендер: **яркая заливка только у bg_primary** (hero-кнопка); bg_success/bg_danger — приглушённые;
  link — как гиперссылка; без стиля — белая. Это дизайн клиента, не баг кода.
- Комбо флагов (primary+link и т.п.) клиент откатывает к дефолту — один стиль на кнопку.

## Типы кнопок (InlineButtonType*)

`inlineButtonTypeCallback {data: hex}`, `url {url}`, `copy {copy_text}`, `disabled`,
`switch_inline {query}`, `webview {url}`, `user_profile {user_id}`.

## Callback и редактирование

- Апдейт `updateBotCallbackQuery` (query_id, data hex, user_id) через `core.update_hook` / `core.cb_hook`.
- Ответ: `messages.setBotCallbackAnswer` (query_id, message, cache_time).
- `messages.editMessage` с новым reply_markup / rich_message — работает для обоих механизмов.

## Грабли

- keyboard-кнопки в reply_markup — dict-ы с полем `"_"` (mt.call сериализует сам); без `"_"` →
  `ValueError: unknown constructor type KeyboardInlineButton`
- rich blocks — hex-строки через `ser()`; `pageBlockTitle`/`pageBlockSubtitle` в inputRichMessage дают
  `RICH_MESSAGE_BLOCK_UNSUPPORTED` — заголовки только `pageBlockHeading1..6`
- document_id — long int, не строка
- обычные юникод-эмодзи работают везде; премиум — по правилам выше
