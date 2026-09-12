# GoyGram — Rich Messages на MTProto (Bot API 10.3 / layer 229)

Живые тесты rich-сообщений через MTProto-транспорт GoyGram на сырых TL-конструкторах.
Layer 229, Rust-сериализатор `goygram.ext` (wheel из PyPI, goygram ≥ 0.7.79).

## Ключевая идея

Rich-сообщение на MTProto — это **не HTML, а TL-конструкторы**:

```
messages.sendMessage(
    peer          = inputPeerUser(user_id, access_hash),
    message       = "",
    rich_message  = inputRichMessage(
        blocks = Vector<PageBlock>,      # дерево блоков
        photos = Vector<InputPhoto>,      # фото-референсы (id, access_hash, file_reference)
    ),
)
```

HTML-форма (`inputRichMessageHTML`) для медиа принимает **только HTTP-URL**
(`<img src="https://...">`) — `attach://`, `tg://photo?id=` и file_id Bot API
отбиваются. Свой медиа-контент — только через TL-форму с вектором `photos`.

## Схема (layer 229, актуальные конструкторы)

### inputRichMessage

```
inputRichMessage#e4c449fc flags:#
    blocks:Vector<PageBlock>
    photos:flags.2?Vector<InputPhoto>       # все фото сообщения
    documents:flags.3?Vector<InputDocument> # все документы
    users:flags.4?Vector<InputUser>
    = InputRichMessage;

inputRichMessageHTML#dacb836a flags:# html:string files:flags.2?Vector<InputRichFile>
inputRichFilePhoto#9b00622b id:string photo:InputPhoto = InputRichFile;
```

### Слайдшоу и коллаж

```
pageBlockSlideshow#31f9590 items:Vector<PageBlock> caption:PageCaption = PageBlock;
pageBlockCollage#65a0fa4d  items:Vector<PageBlock> caption:PageCaption = PageBlock;
pageBlockPhoto#1759c560 photo_id:long caption:PageCaption url:flags.0?string = PageBlock;
pageCaption#6f747657 text:RichText credit:RichText = PageCaption;
```

`pageBlockCollage` рендерится стопкой/сеткой, `pageBlockSlideshow` — свайпаемой лентой.
**Оба требуют `caption`** (можно пустой: `pageCaption(textEmpty, textEmpty)`) — иначе
сериализатор GoyGram падает с `missing required field caption`.

### Заголовки, текст, списки

```
pageBlockHeading1..6#        text:RichText
pageBlockParagraph#467a0766  text:RichText
pageBlockDivider#db20b188
pageBlockPreformatted#c070d93e text:RichText language:string
pageBlockBlockquote#66d1670b text:RichText caption:RichText
pageBlockDetails#76768bed    open:flags.0?true title:RichText blocks:Vector<PageBlock>
pageBlockOrderedList#1fd6f6c1 items:Vector<PageListOrderedItem>
pageListOrderedItemText#15031189 text:RichText
pageBlockFooter#48870999     text:RichText
```

### Таблицы

```
pageBlockTable#bf4dea82 flags:# bordered striped compact
    title:RichText rows:Vector<PageTableRow> = PageBlock;
pageTableRow#e0c0c5e5    cells:Vector<PageTableCell>
pageTableCell#34566b6a   flags:# header align_center align_right valign_*
                          text:flags.7?RichText colspan rowspan
```

### Формулы

```
pageBlockMath#59080c20 source:string = PageBlock;   # LaTeX, без RichText
```

### RichText (inline-форматирование)

```
textPlain#744694e0 text:string
textBold#6724abc4 / textItalic / textUnderline / textStrike / textFixed
textSpoiler#4c2a5d62 / textMarked#34b8621 / textSubscript / textSuperscript
textUrl#3c2884c1 text:RichText url:string webpage_id:long   # webpage_id обязателен (0 OK)
textEmail / textPhone / textAnchor / textCustomEmoji (document_id + alt)
textConcat#7e6260d7 texts:Vector<RichText>   # склейка спанов
textDate#a5b45e2b flags:# text:RichText date:int   # локализованная дата
```

## Пайплайн фото (аналог Telethon InputPhoto)

```
1. mt.upload_file(path)                          -> inputFile (id, parts, name)
2. messages.uploadMedia(peer, inputMediaUploadedPhoto(file))
                                                 -> messageMediaPhoto -> photo{id, access_hash, file_reference}
3. photos-вектор: inputPhoto(id, access_hash, file_reference) для каждого
4. blocks: pageBlockSlideshow(items=[pageBlockPhoto(photo_id, pageCaption(...)) x N],
                              caption=pageCaption(...))
5. messages.sendMessage(peer, message="", rich_message=inputRichMessage(blocks, photos))
```

## Peer-резолв для бота (критично)

Боту на MTProto **недоступны** `messages.getDialogs` / `users.getUsers` —
BOT_METHOD_INVALID. Peer c access_hash появляется только из MTProto-апдейтов:

1. Юзер пишет боту любое сообщение → апдейт несёт `users:[...]` с access_hash
2. GoyGram инжестит entities → `mt.entities[("user", uid)]`
3. `mt.resolve_peer(uid)` работает
4. **Persist**: сохраняй entity в JSON (`mt_entities.json`) — переиспользуй между запусками
5. Если сообщение пропущено — восстанови через `updates.getDifference(pts-N)`
   (сервер переигрывает недавние апдейты, entities инжестятся)

## Live-quirks живого API 10.3 (проверено 2026-09-12)

- `textUrl` требует `webpage_id` (0 допустим)
- Bot API blocks-форма (`sendRichMessage` JSON) парсит `paragraph`/`photo`/`heading`,
  но требует другие имена полей (`heading.size` — число, photo-блок — `{"type":"photo","media":file_id}`);
  сообщение уходит «ОК», но **на MTProto-уровне приходит пустым** — молчаливая фильтрация.
  Полноценно блоки работают только через MTProto TL-форму.
- `<img src>` в HTML-форме: только HTTP(S) URL
- Draft-режим (`sendRichMessageDraft`): кадр живёт ~20 сек, обновление циклом
  каждые 2-3 сек, после драфта обязателен финальный `sendRichMessage` (без tg-thinking)
- MTProto-драфты: `messages.setRichMessageDraft` — не проверено, в бэклоге

## Запуск теста

```bash
pip install goygram   # 0.7.79+, Rust ext из wheel

python3 tests/goygram_mtproto_rich_test.py \
    --token "$BOT_TOKEN" --chat "$OWNER_ID" \
    --photos p1.jpg p2.jpg p3.jpg
```

Тест отправляет (получателю в ЛС):
1. Слайдшоу из фото с rich-caption
2. Коллаж с rich-caption
3. Полное сообщение: h1-h5 + параграф + слайдшоу + divider + таблица + формулы
   (LaTeX) + нумерованный список + details + blockquote + preformatted + footer

Всё через `messages.sendMessage` с `inputRichMessage`. Ожидаемый результат:
`ok: true` + echo `updates` с конструкторами в raw.

## Структура

- `tests/goygram_mtproto_rich_test.py` — MTProto rich-тест (слайдшоу/коллаж/все блоки)
- `tests/goygram_rich_drafts_test.py` — Bot API драфт-стриминг (sendRichMessageDraft)
- `mt_entities.json` — persist кэш peer entities (не коммитить!)

## Возможные грабли

- `missing required field caption` — у pageBlockPhoto/Collage/Slideshow обязательный
  pageCaption (можно textEmpty×2)
- `BOT_METHOD_INVALID` на `messages.getDialogs` — нормально для ботов; нужен entity из апдейтов
- goygram из git-клона без собранного ext не работает — ставить из PyPI
- Схема тянется библиотекой с layer 229 floor; свежий api.tl: tdesktop dev branch
