# GoyGram MTProto Rich Messages — полный справочник (layer 229, Bot API 10.3)

> Рабочий эталон: протестировано на живом Telegram 2026-09-12 через GoyGram 0.7.79
> (PyPI wheel, Rust ext). Полное сообщение со ВСЕМИ блоками + слайдшоу: сервер принял,
> клиент отрендерил — «идеальный пример rich-текста».

## 1. Архитектура

Rich-сообщение на MTProto — **сырые TL-конструкторы**, не HTML:

```
messages.sendMessage(
    peer         = inputPeerUser(user_id, access_hash),
    message      = "",
    random_id    = <int63>,
    rich_message = inputRichMessage(blocks, photos),
)
```

inputRichMessage (layer 229):

```
inputRichMessage#e4c449fc flags:#
    blocks:Vector<PageBlock>
    photos:flags.2?Vector<InputPhoto>
    documents:flags.3?Vector<InputDocument>
    users:flags.4?Vector<InputUser>
```

HTML-форма inputRichMessageHTML принимает медиа **только HTTP-URL**
(`<img src="https://…">`); `attach://`, `tg://photo?id=`, Bot API file_id —
отвергаются. Свои фото — только TL-форма с вектором `photos`.

## 2. Полный пайплайн фото (Telethon-style InputPhoto)

```
1. mt.upload_file(path)                        -> inputFile {id, parts, name, md5}
2. messages.uploadMedia(peer,
     inputMediaUploadedPhoto(file=inputFile))  -> messageMediaPhoto
                                                -> photo {id, access_hash, file_reference}
3. inputPhoto(id, access_hash, file_reference)  для каждого фото -> вектор photos
4. pageBlockPhoto(photo_id=photo.id, caption=pageCaption(textEmpty, textEmpty))
5. pageBlockSlideshow/Collage(items=[pageBlockPhoto x N], caption=pageCaption)
6. inputRichMessage(blocks=[...], photos=[...])
7. messages.sendMessage(rich_message=...)
```

**ВАЖНО**: `photo_id` в pageBlockPhoto = long-ID фото из шага 2 (тот же, что в
`inputPhoto.id`).

## 3. Сериализация в GoyGram

Rust-ядро (`goygram.ext`) сериализует конструкторы из JSON-описаний:

```python
import json
import goygram.ext as rx

def ser(name: str, body: dict) -> str:
    return bytes(rx.serialize_constructor(name, json.dumps(body))).hex()

plain   = ser("textPlain", {"text": "Привет"})
bold    = ser("textBold", {"text": plain})
caption = ser("pageCaption", {"text": bold, "credit": ser("textEmpty", {})})
```

Правило: значение каждого TL-поля-конструктора — hex-строка результата
serialize_constructor; векторы — списки hex-строк; скаляры (long/int/string/bool) —
как есть в JSON. Так строится дерево любой глубины.

## 4. Все рабочие блоки (проверено на живом API)

| Блок | TL-конструктор | Поля |
|---|---|---|
| Заголовки h1-h5 (+h6) | `pageBlockHeading1..6` | text:RichText |
| Параграф | `pageBlockParagraph` | text:RichText |
| Слайдшоу (свайп!) | `pageBlockSlideshow` | items:Vector&lt;PageBlock&gt;, caption:PageCaption |
| Коллаж (сетка/стопка) | `pageBlockCollage` | items, caption |
| Таблица | `pageBlockTable` | bordered/striped/compact:bool, title:RichText, rows:Vector&lt;PageTableRow&gt; |
| Формула LaTeX | `pageBlockMath` | **source:string** (не RichText!) |
| Нумерованный список | `pageBlockOrderedList` | items:Vector&lt;PageListOrderedItem&gt;, start, type |
| Список с чекбоксами | `pageBlockList` | items:Vector&lt;PageListItem&gt; (checkbox/checked) |
| Details (сворачиваемый) | `pageBlockDetails` | open:bool, title:RichText, blocks:Vector&lt;PageBlock&gt; |
| Blockquote | `pageBlockBlockquote` | text, caption |
| Pull-quote | `pageBlockPullquote` | text, caption |
| Preformatted | `pageBlockPreformatted` | text, language |
| Divider | `pageBlockDivider` | — |
| Footer | `pageBlockFooter` | text |
| Фото-блок | `pageBlockPhoto` | photo_id:long, caption:PageCaption, url/webpage_id опц. |
| Embed | `pageBlockEmbed` | url/html, w, h, caption |
| Map | `pageBlockMap` | geo:GeoPoint, zoom, w, h, caption |
| Channel | `pageBlockChannel` | channel:Chat |
| Видео-блок | `pageBlockVideo` | video_id:long, caption |
| Обложка | `pageBlockCover` | cover:PageBlock |

Таблицы (детально):

```
pageBlockTable#bf4dea82 flags:# bordered striped compact
    title:RichText rows:Vector<PageTableRow> = PageBlock;
pageTableRow#e0c0c5e5  cells:Vector<PageTableCell>;
pageTableCell#34566b6a flags:# header:flags.0?true align_center:flags.3?true
    align_right:flags.4?true valign_middle valign_bottom text:flags.7?RichText
    colspan:flags.1?int rowspan:flags.2?int
```

Нумерованные списки:

```
pageListOrderedItemText#15031189 flags:# checkbox checked num text:RichText value type
pageListOrderedItemBlocks#8ff2d5f0 blocks:Vector<PageBlock>
```

## 5. RichText (inline-форматирование)

```
textPlain(text) · textBold(text) · textItalic · textUnderline · textStrike · textFixed
textMarked(text) · textSpoiler(text) · textSubscript · textSuperscript
textUrl(text, url, webpage_id:long)   # webpage_id ОБЯЗАТЕЛЕН (0 допустим!)
textEmail(text, email) · textPhone(text, phone)
textAnchor(text, name) · textCustomEmoji(document_id, alt)
textConcat(texts:Vector<RichText>)    # склейка спанов — основной способ смешанного текста
textDate(date:int, text)              # локализованная дата
textButton(text, type, style)         # inline-кнопки внутри текста
```

## 6. Peer-резолв для бота на MTProto (критично!)

Боту недоступны `messages.getDialogs` / `users.getUsers` → BOT_METHOD_INVALID.
access_hash юзера появляется **только из MTProto-апдейтов**:

1. Цель пишет боту любое сообщение → апдейт несёт `users:[...]` с access_hash
2. GoyGram инжестит → `mt.entities[("user", uid)]`
3. `mt.resolve_peer(uid)` работает
4. **Persist в JSON** (`mt_entities.json`) — переиспользовать между запусками
5. Пропустили апдейт? `updates.getDifference(pts-N)` переигрывает недавние
   сообщения с полными entities (проверено — работает)

## 7. Live-quirks (живой API 2026-09-12)

- `textUrl` без `webpage_id` → ValueError сериализатора GoyGram (0 — ок)
- `pageBlockPhoto`/`Collage`/`Slideshow` без `caption` → `missing required field caption`
  (достаточно `pageCaption(textEmpty, textEmpty)`)
- Bot API JSON-blocks (sendRichMessage): парсит paragraph/heading/photo, но имена полей
  отличаются (`heading.size` — число; photo-блок `{"type":"photo","media":file_id}`).
  **OK-ответ не гарантирует доставку** — на MTProto-уровне сообщение может уйти пустым
  (молчаливая фильтрация). Полноценные блоки — только через MTProto TL-форму.
- HTML `<img src>` — только HTTP(S); `attach://` и `tg://photo?id=` отбиты
- Драфт (Bot API): ~20 сек жизни, обновлять каждые 2-3 сек, финал — обычный
  sendRichMessage без tg-thinking (драфт пропадает без следа)
- `pageBlockMath`: LaTeX рендерится формулой (E=mc², интегралы, дроби — проверено)

## 8. Эталонное «идеальное» сообщение (16 блоков, живьём ОК)

```
blocks = [
  pageBlockHeading1..5("Заголовок H1..H5"),
  pageBlockParagraph(textConcat([textBold("Жирный"), " параграф с ",
                    textItalic("курсивом"), " и ", textSpoiler("спойлером")])),
  pageBlockSlideshow(items=[pageBlockPhoto(id1..3)], caption=rich_caption),
  pageBlockDivider(),
  pageBlockTable(bordered+striped+compact, title="Таблица блоков", rows=[
      header("Блок", "TL-конструктор", "Статус"),
      ("Heading1-5", "pageBlockHeading1..5", "OK"),
      ("Paragraph", "pageBlockParagraph", "OK"),
      ("Slideshow", "pageBlockSlideshow", "OK"),
      ("Collage",   "pageBlockCollage",   "OK"),
      ("Table",     "pageBlockTable",     "OK"),
      ("Math",      "pageBlockMath",      "OK"),
  ]),
  pageBlockMath("E = mc^2"),
  pageBlockMath("\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}"),
  pageBlockOrderedList(["первый пункт", "второй пункт", "третий пункт"]),
  pageBlockDetails(open=false, title="Развернуть подробности",
                  blocks=[2 x pageBlockParagraph]),
  pageBlockBlockquote(text="Цитата", caption="Автор цитаты"),
  pageBlockPreformatted("print('hello')", language="python"),
  pageBlockFooter("Footer: конец полного теста"),
]
photos = [inputPhoto(id1..3, access_hash, file_reference)]
```

Rich-caption для слайдшоу/коллажа:

```
pageCaption(
  text = textConcat([ textBold("Слайдшоу"), " — три фото, свайпай" ]),
  credit = textEmpty,
)
```

## 9. Источник TL-схемы

tdesktop dev branch api.tl (layer 229 floor) — GoyGram тянет ту же схему
автоматически при старте. Свежая схема: `raw.githubusercontent.com/telegramdesktop/tdesktop/dev/Telegram/SourceFiles/mtproto/scheme/api.tl`
