#!/usr/bin/env python3
"""Три механизма кнопок в трёх сообщениях: keyboard, rich (pageButton), text (textButton).
Премиум-эмодзи везде: keyboard -> keyboardButtonStyle.icon, rich/text -> textCustomEmoji.
TL-tests эталон. Без конкретного проекта — общие кнопки и эмодзи."""
import asyncio
import json
import os
import re
import secrets
import time
from pathlib import Path

from goygram import GoyGram
from goygram.schema_manager import init_schema
from goygram.security import bootstrap_session
import goygram.ext as rx

init_schema(rx)

SESSION = "tltests_mtbot"
ENV_PATH = "/home/forget/Arena/.env"  # TELEGRAM_API_ID / TELEGRAM_API_HASH
ENT = Path("mt_entities.json")
USER_ID = 7610246474  # target user; entities loaded from mt_entities.json

EMOJI = {
    "pill": 5463081281048818043,     # 💊
    "therm": 5463054218459884779,    # 🌡
    "sleepy": 5462990652943904884,   # 😴
    "ok": 5465465194056525619,       # 👍
    "poop": 5465198330558557107,     # 💩
    "noentry": 5462882007451185227,  # 🚫
    "point": 5463392464314315076,    # 👉
}
ALT = {"pill": "💊", "therm": "🌡", "sleepy": "😴", "ok": "👍",
       "poop": "💩", "noentry": "🚫", "point": "👉"}


def ser(name, body):
    return bytes(rx.serialize_constructor(name, json.dumps(body))).hex()


def rt(t):
    return ser("textPlain", {"text": t})


def emo(key):
    return ser("textCustomEmoji", {"document_id": EMOJI[key], "alt": ALT[key]})


def concat(parts):
    return ser("textConcat", {"texts": parts})


def kb_btn(label, data, style=None, icon=None):  # keyboard: ПОД сообщением
    body = {"_": "keyboardInlineButton", "text": label,  # ПЛЕЙН, НЕ RichText
            "type": ser("inlineButtonTypeCallback", {"data": data.encode().hex()})}
    st = {}
    if style: st[style] = True
    if icon: st["icon"] = EMOJI[icon]  # премиум-эмодзи ТОЛЬКО здесь
    if st: body["style"] = ser("keyboardButtonStyle", st)
    return body


def kb_markup(rows):
    return {"_": "replyInlineMarkup", "rows":
            [{"_": "keyboardInlineButtonRow", "buttons": r} for r in rows]}


def page_btn(label, data, style=None, emoji_key=None):
    """pageButton в pageBlockButtonRow: text:RichText → textCustomEmoji ок."""
    text = rt(label)
    if emoji_key:
        text = concat([emo(emoji_key), rt(" " + label)])
    body = {"text": text, "type": ser("inlineButtonTypeCallback", {"data": data.encode().hex()})}
    if style:
        body["style"] = ser("richButtonStyle", {style: True})
    return ser("pageButton", body)


def btn_row(buttons, align_center=True):
    return ser("pageBlockButtonRow", {"align_center": align_center, "buttons": buttons})


def text_btn(label, data, style=None, emoji_key=None):
    """textButton — кнопка ВНУТРИ текста rich-сообщения: text:RichText."""
    text = rt(label)
    if emoji_key:
        text = concat([emo(emoji_key), rt(" " + label)])
    body = {"text": text, "type": ser("inlineButtonTypeCallback", {"data": data.encode().hex()})}
    if style:
        body["style"] = ser("richButtonStyle", {style: True})
    return ser("textButton", body)


async def load_entities(core):
    if ENT.exists():
        for uid, ent in json.loads(ENT.read_text()).items():
            core.mt.entities[("user", int(uid))] = ent


async def resolve_target(core):
    try:
        return await core.mt.resolve_peer(USER_ID)
    except Exception:
        pass
    state = await core.mt.call("updates.getState", api_id=core.api_id)
    pts = state.get("pts", 100) if isinstance(state, dict) else 100
    await core.mt.call("updates.getDifference", api_id=core.api_id,
                       pts=max(1, pts - 500), date=int(time.time()) - 7200, qts=0)
    return await core.mt.resolve_peer(USER_ID)


async def send_rich(core, peer, blocks):
    return await core.mt.call("messages.sendMessage", peer=peer, message="",
                              random_id=secrets.randbits(63),
                              rich_message={"_": "inputRichMessage", "blocks": blocks})


async def main():
    env = Path(os.environ.get("CREDS_ENV", ENV_PATH)).read_text()
    api_id = int(os.environ.get("TELEGRAM_API_ID") or re.search(r"TELEGRAM_API_ID=(\d+)", env).group(1))
    api_hash = os.environ.get("TELEGRAM_API_HASH") or re.search(r"TELEGRAM_API_HASH=([0-9a-f]+)", env).group(1)
    token = os.environ.get("BOT_TOKEN") or re.search(r"BOT_TOKEN=(\S+)", Path(".env").read_text()).group(1)

    app = GoyGram(bot_token=token, api_id=api_id, api_hash=api_hash,
                  default_transport="mtproto", session_name=SESSION)
    core = app.core
    await bootstrap_session(core, api_id=api_id, api_hash=api_hash,
                            session_name=SESSION, bot_token=token)
    await core.mt.start()
    await load_entities(core)
    peer = await resolve_target(core)
    print("[OK] peer resolved", flush=True)

    # ── 1. KEYBOARD: премиум-эмодзи через keyboardButtonStyle.icon ────────────
    markup = kb_markup([
        [kb_btn("Отправить", "kb:go", "bg_primary", "ok"),
         kb_btn("Отмена", "kb:no", None, "sleepy")],
        [kb_btn("Забанить", "kb:ban", "bg_danger", "poop"),
         kb_btn("Подробнее", "kb:pt", None, "point"),
         kb_btn("Нельзя", "kb:off", None, "noentry")],
    ])
    await core.mt.call("messages.sendMessage", peer=peer,
                       message="Вид 1 — keyboard-кнопки (премиум-эмодзи через icon в стиле)",
                       random_id=secrets.randbits(63),
                       reply_markup=markup)
    print("[OK] 1 KEYBOARD sent", flush=True)

    # ── 2. RICH pageButton: textCustomEmoji в RichText кнопки ─────────────────
    r1 = btn_row([
        page_btn("Отправить", "rb:go", "bg_primary", "ok"),
        page_btn("Отмена", "rb:no", None, "sleepy"),
    ])
    r2 = btn_row([
        page_btn("Забанить", "rb:ban", "bg_danger", "poop"),
        page_btn("Подробнее", "rb:pt", None, "point"),
    ])
    r3 = btn_row([
        page_btn("Лекарство", "rb:pill", "bg_success", "pill"),
        page_btn("Температура", "rb:therm", None, "therm"),
        page_btn("Запрет", "rb:off", None, "noentry"),
    ])
    h = ser("pageBlockHeading2", {"text": concat([emo("pill"), rt(" Вид 2 — pageButton")])})
    p = ser("pageBlockParagraph", {"text": rt(
        "Кнопки-блоки: pageBlockButtonRow → pageButton. text:RichText → textCustomEmoji.")})
    await send_rich(core, peer, [h, p, r1, r2, r3])
    print("[OK] 2 RICH pageButton sent", flush=True)

    # ── 3. TEXT textButton: премиум-эмодзи в кнопке внутри текста ──────────────
    h3 = ser("pageBlockHeading2", {"text": concat([emo("therm"), rt(" Вид 3 — textButton")])})
    p3 = ser("pageBlockParagraph", {"text": concat([
        rt("Кнопки в строке: "),
        text_btn("Отправить", "tb:go", "bg_primary", "ok"),
        rt(" "),
        text_btn("Отмена", "tb:no", None, "sleepy"),
        rt(" "),
        text_btn("Забанить", "tb:ban", "bg_danger", "poop"),
        rt(" "),
        text_btn("Туда", "tb:pt", None, "point"),
        rt(" "),
        text_btn("Аптека", "tb:pill", "bg_success", "pill"),
        rt(" "),
        text_btn("Нельзя", "tb:off", None, "noentry"),
        rt(".")])})
    await send_rich(core, peer, [h3, p3])
    print("[OK] 3 TEXT textButton sent", flush=True)

    await asyncio.sleep(2)
    await core.close()

asyncio.run(main())
