#!/usr/bin/env python3
"""GoyGram MTProto Rich Messages — live test suite (Bot API 10.3 / layer 229).

Covers, via raw TL constructors (goygram.ext serializer):
  - photo upload -> InputPhoto (messages.uploadMedia + inputMediaUploadedPhoto)
  - swipeable SLIDESHOW (pageBlockSlideshow + pageBlockPhoto + inputPhoto vector)
  - COLLAGE (pageBlockCollage)
  - rich captions (pageCaption + textConcat/textBold/textMarked/textUrl)
  - headings h1-h5, paragraphs, tables, math, ordered lists, details,
    blockquote, preformatted, footer, divider

Requirements:
  - pip install goygram (0.7.79+, Rust ext from PyPI wheel)
  - env: TELEGRAM_API_ID / TELEGRAM_API_HASH (Arena .env)
  - bot token with MTProto allowed
  - peer entity cache: the target user must have messaged the bot at least once
    (entity with access_hash is ingested from MTProto updates; persisted to
    mt_entities.json for reuse)

Usage:
  python3 goygram_mtproto_rich_test.py --token <BOT_TOKEN> --chat <USER_ID> \
      [--photos p1.jpg p2.jpg p3.jpg] [--entity-cache mt_entities.json]

Without --token/--chat the script reads BOT_TOKEN / TARGET_CHAT env vars.
"""
import argparse
import asyncio
import json
import re
import secrets
import sys
from pathlib import Path

from goygram import GoyGram
from goygram.security import bootstrap_session
import goygram.ext as rx

SESSION_NAME = "tltests_mtbot"
ENT_FILE = Path("mt_entities.json")


# ---------------------------------------------------------------- helpers
def ser(name: str, body: dict) -> str:
    """Serialize a TL constructor to hex (goygram.ext Rust core)."""
    return bytes(rx.serialize_constructor(name, json.dumps(body))).hex()


def rt(text: str) -> str:
    """Plain RichText."""
    return ser("textPlain", {"text": text})


def rt_concat(parts: list) -> str:
    """Concatenated RichText (like a run of inline spans)."""
    return ser("textConcat", {"texts": parts})


def empty_caption() -> str:
    return ser("pageCaption", {
        "text": ser("textEmpty", {}),
        "credit": ser("textEmpty", {}),
    })


def find_photo(obj):
    if isinstance(obj, dict):
        if obj.get("_") == "photo":
            return obj
        for v in obj.values():
            r = find_photo(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_photo(v)
            if r:
                return r
    return None


# ---------------------------------------------------------------- core class
class MTRich:
    def __init__(self, token: str, api_id: int, api_hash: str):
        self.app = GoyGram(bot_token=token, api_id=api_id, api_hash=api_hash,
                           default_transport="mtproto", session_name=SESSION_NAME)
        self.core = self.app.core

    async def start(self):
        await bootstrap_session(self.core, api_id=self.core.api_id,
                                api_hash=self.core.api_hash,
                                session_name=SESSION_NAME, bot_token=self.core.bot_token
                                if hasattr(self.core, "bot_token") else None)
        await self.core.mt.start()
        self.restore_entities()

    def restore_entities(self):
        if ENT_FILE.exists():
            for uid, ent in json.loads(ENT_FILE.read_text()).items():
                self.core.mt.entities[("user", int(uid))] = ent

    def save_entity(self, uid: int):
        ent = self.core.mt.entities.get(("user", uid))
        if ent:
            data = json.loads(ENT_FILE.read_text()) if ENT_FILE.exists() else {}
            data[str(uid)] = ent
            ENT_FILE.write_text(json.dumps(data))

    async def resolve_peer(self, chat_id: int):
        return await self.core.mt.resolve_peer(chat_id)

    async def upload_photo(self, peer, path: str, name: str = "photo.jpg") -> dict:
        """upload_file -> inputFile -> inputMediaUploadedPhoto -> uploadMedia -> photo."""
        up = await self.core.mt.upload_file(path, file_name=name)
        file_hex = ser("inputFile", {"id": up["id"], "parts": up["parts"],
                                     "name": up["name"], "md5_checksum": up.get("md5", "")})
        media_hex = ser("inputMediaUploadedPhoto", {"file": file_hex})
        res = await self.core.mt_req("messages.uploadMedia", peer=peer, media=media_hex)
        ph = find_photo(res)
        if not ph:
            raise RuntimeError(f"no photo in uploadMedia result: {str(res)[:200]}")
        return {"id": ph["id"], "access_hash": ph["access_hash"],
                "file_reference": ph.get("file_reference", "")}

    async def send_rich(self, peer, blocks: list, photos: list | None = None) -> dict:
        rich_tl = {"_": "inputRichMessage", "blocks": blocks}
        if photos:
            rich_tl["photos"] = photos
        return await self.core.mt_req("messages.sendMessage",
            peer=peer, message="", random_id=secrets.randbits(63),
            rich_message=rich_tl)

    async def close(self):
        await self.core.close()


# ---------------------------------------------------------------- builders
def build_slideshow(photo_refs: list, caption_hex: str | None = None) -> tuple[str, list]:
    """Swipeable slideshow; returns (block_hex, photos_vector_hex)."""
    cap = caption_hex or empty_caption()
    photo_blocks = [ser("pageBlockPhoto", {"photo_id": p["id"], "caption": cap})
                    for p in photo_refs]
    block = ser("pageBlockSlideshow", {"items": photo_blocks, "caption": cap})
    photos_vec = [ser("inputPhoto", {"id": p["id"], "access_hash": p["access_hash"],
                                     "file_reference": p["file_reference"]})
                  for p in photo_refs]
    return block, photos_vec


def build_collage(photo_refs: list, caption_hex: str | None = None) -> tuple[str, list]:
    """Grid collage; returns (block_hex, photos_vector_hex)."""
    cap = caption_hex or empty_caption()
    photo_blocks = [ser("pageBlockPhoto", {"photo_id": p["id"], "caption": cap})
                    for p in photo_refs]
    block = ser("pageBlockCollage", {"items": photo_blocks, "caption": cap})
    photos_vec = [ser("inputPhoto", {"id": p["id"], "access_hash": p["access_hash"],
                                     "file_reference": p["file_reference"]})
                  for p in photo_refs]
    return block, photos_vec


def build_rich_caption(text_bold: str = "Мой коллаж", marked: str = "выделенный текст",
                        link_text: str = "ссылка на дока",
                        url: str = "https://goygram.github.io/docs/Rich-API") -> str:
    """pageCaption with textBold + textMarked + textUrl concatenated."""
    bold = ser("textBold", {"text": rt(text_bold)})
    sep = rt(" — ")
    marked_hex = ser("textMarked", {"text": rt(marked)})
    sep2 = rt(" и ")
    link = ser("textUrl", {"text": rt(link_text), "url": url, "webpage_id": 0})
    text = rt_concat([bold, sep, marked_hex, sep2, link])
    return ser("pageCaption", {"text": text, "credit": ser("textEmpty", {})})


def build_all_blocks(photo_refs: list | None = None) -> tuple[list, list]:
    """Full showcase: h1-h5, paragraph, slideshow, divider, table, math,
    ordered list, details, blockquote, preformatted, footer."""
    blocks, photos_vec = [], []
    if photo_refs:
        ss_block, ss_photos = build_slideshow(photo_refs)
        blocks.append(ss_block)
        photos_vec.extend(ss_photos)

    blocks.append(ser("pageBlockHeading1", {"text": rt("Заголовок H1")}))
    blocks.append(ser("pageBlockHeading2", {"text": rt("Заголовок H2")}))
    blocks.append(ser("pageBlockHeading3", {"text": rt("Заголовок H3")}))
    blocks.append(ser("pageBlockHeading4", {"text": rt("Заголовок H4")}))
    blocks.append(ser("pageBlockHeading5", {"text": rt("Заголовок H5")}))

    blocks.append(ser("pageBlockParagraph", {"text": rt_concat([
        ser("textBold", {"text": rt("Жирный")}),
        rt(" параграф с "),
        ser("textItalic", {"text": rt("курсивом")}),
        rt(" и "),
        ser("textSpoiler", {"text": rt("спойлером")}),
    ])}))

    blocks.append(ser("pageBlockDivider", {}))

    def cell(text, header=False, align_center=True):
        body = {"text": rt(text)}
        if header:
            body["header"] = True
        if align_center:
            body["align_center"] = True
        return ser("pageTableCell", body)

    def row(cells):
        return ser("pageTableRow", {"cells": cells})

    rows = [
        row([cell("Блок", header=True), cell("TL-конструктор", header=True), cell("Статус", header=True)]),
        row([cell("Heading1-5"), cell("pageBlockHeading1..5"), cell("✅")]),
        row([cell("Paragraph"), cell("pageBlockParagraph"), cell("✅")]),
        row([cell("Slideshow"), cell("pageBlockSlideshow"), cell("✅")]),
        row([cell("Collage"), cell("pageBlockCollage"), cell("✅")]),
        row([cell("Table"), cell("pageBlockTable"), cell("✅")]),
        row([cell("Math"), cell("pageBlockMath"), cell("✅")]),
    ]
    blocks.append(ser("pageBlockTable", {
        "bordered": True, "striped": True, "compact": True,
        "title": rt_concat([ser("textBold", {"text": rt("Таблица")}), rt(" блоков")]),
        "rows": rows,
    }))

    blocks.append(ser("pageBlockMath", {"source": "E = mc^2"}))
    blocks.append(ser("pageBlockMath", {"source": r"\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}"}))

    blocks.append(ser("pageBlockOrderedList", {
        "items": [ser("pageListOrderedItemText", {"text": rt(t)})
                  for t in ("первый пункт", "второй пункт", "третий пункт")],
    }))

    blocks.append(ser("pageBlockDetails", {
        "open": False,
        "title": rt("Развернуть подробности"),
        "blocks": [ser("pageBlockParagraph", {"text": rt("Скрытый контент внутри details-блока")}),
                   ser("pageBlockParagraph", {"text": rt("Вторая строка скрытого контента")})],
    }))

    blocks.append(ser("pageBlockBlockquote", {
        "text": rt("Цитата: простой текст"),
        "caption": rt("Автор цитаты"),
    }))

    blocks.append(ser("pageBlockPreformatted",
                      {"text": rt("code block: print('hello')"), "language": "python"}))
    blocks.append(ser("pageBlockFooter", {"text": rt("Footer: полный тест всех блоков")}))
    return blocks, photos_vec


# ---------------------------------------------------------------- live test
async def run(args):
    env = Path(args.env).read_text()
    api_id = int(re.search(r"TELEGRAM_API_ID=(\d+)", env).group(1))
    api_hash = re.search(r"TELEGRAM_API_HASH=([0-9a-f]+)", env).group(1)

    mt = MTRich(args.token, api_id, api_hash)
    await mt.start()
    peer = await mt.resolve_peer(args.chat)
    print("[OK] peer resolved")

    results = {}

    # 1) photos upload
    photo_refs = []
    if args.photos:
        for i, p in enumerate(args.photos, 1):
            ref = await mt.upload_photo(peer, p, f"photo{i}.jpg")
            photo_refs.append(ref)
            print(f"[OK] photo {i}: id={ref['id']}")
    results["upload"] = bool(photo_refs) or "skipped"

    # 2) slideshow
    if photo_refs:
        block, photos_vec = build_slideshow(photo_refs, build_rich_caption())
        res = await mt.send_rich(peer, [block], photos_vec)
        results["slideshow"] = res.get("ok", False)
        print(f"[{'OK' if results['slideshow'] else 'FAIL'}] slideshow")

    # 3) collage
    if photo_refs:
        block, photos_vec = build_collage(photo_refs, build_rich_caption())
        res = await mt.send_rich(peer, [block], photos_vec)
        results["collage"] = res.get("ok", False)
        print(f"[{'OK' if results['collage'] else 'FAIL'}] collage")

    # 4) all blocks + slideshow in one message
    blocks, photos_vec = build_all_blocks(photo_refs)
    res = await mt.send_rich(peer, blocks, photos_vec)
    results["all_blocks"] = res.get("ok", False)
    print(f"[{'OK' if results['all_blocks'] else 'FAIL'}] all_blocks ({len(blocks)} blocks)")

    await mt.close()

    ok = all(v is True or v == "skipped" for v in results.values())
    print(json.dumps(results, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=None, help="bot token (or BOT_TOKEN env)")
    ap.add_argument("--chat", type=int, default=None, help="target user id (or TARGET_CHAT env)")
    ap.add_argument("--env", default="/home/forget/Arena/.env",
                    help=".env with TELEGRAM_API_ID/TELEGRAM_API_HASH")
    ap.add_argument("--photos", nargs="*", default=None, help="photo paths for slideshow/collage")
    args = ap.parse_args()
    args.token = args.token or os.environ.get("BOT_TOKEN")
    args.chat = args.chat or int(os.environ.get("TARGET_CHAT", "0"))
    if not args.token or not args.chat:
        ap.error("need --token/--chat or BOT_TOKEN/TARGET_CHAT env")
    asyncio.run(run(args))


if __name__ == "__main__":
    import os
    main()
