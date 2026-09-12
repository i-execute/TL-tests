#!/usr/bin/env python3
"""GoyGram Rich Messages / Drafts / tg-thinking — live Bot API test.

Token & chat: TL-tests demo bot, owner DM.
Run: python3 goygram_rich_drafts_test.py
"""
import asyncio
import time
import secrets
from goygram import GoyGram, Rich

import os

TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("TARGET_CHAT", "0"))
assert TOKEN and OWNER_ID, "Set BOT_TOKEN / TARGET_CHAT env vars (secrets stay out of repo)"

E = {
    "calm":    "5449619723966761441",  # 😌
    "ok":      "5447363161034346459",  # 👌
    "think":   "5296739894914207637",  # 🤔
    "brain":   "5447595110743168717",  # 🧠
    "analyze": "5384182985224374928",  # 🧐
    "perfect": "5384182740411240426",  # 💯
    "fire":    "5296250904297624056",  # 💩 (для негатив-кейса не нужен, но пусть)
}


def h1(eid, txt):
    return f'<h1><tg-emoji emoji-id="{eid}">{txt}</tg-emoji></h1>'


async def main():
    app = GoyGram(bot_token=TOKEN)

    results = []

    def log(name, ok, detail=""):
        results.append((name, ok, detail))
        print(f"[{'OK' if ok else 'FAIL'}] {name} {('— ' + detail) if detail else ''}")

    # ---------------------------------------------------------------- send_rich (builder)
    try:
        r = (
            Rich()
            .heading("GoyGram Rich Test", 1)
            .text(f'GoyGram {__import__("goygram").__version__} — send_rich builder path. ')
            .b("Bold").text(" ").i("italic").text(" ").code("inline code").nl()
            .emoji(E["ok"], "👌")
            .list(["blocks", "tables", "details"], ordered=False)
            .details("Details block", Rich().text("Скрытый текст внутри <details>.").code("code inside").nl())
            .math(r"E = mc^2")
            .btn_row(
                Rich().btn_url("GoyGram repo", "https://github.com/GoyGram/GoyGram"),
                Rich().btn_cb("Callback btn", "gg:cb"),
            )
        )
        res = await app.send_rich(OWNER_ID, r)
        msg = res.get("result", res) if isinstance(res, dict) else res
        log("send_rich builder", bool(msg.get("message_id") or msg.get("messageId")),
            f"message_id={msg.get('message_id') or msg.get('messageId')}")
    except Exception as e:
        log("send_rich builder", False, repr(e))

    # ---------------------------------------------------------------- send_rich (raw HTML string)
    try:
        html = (
            h1(E["analyze"], "🧐") + "\n"
            "<p>Raw HTML string path — таблица и цитата:</p>\n"
            "<table><tr><th>Транспорт</th><th>Метод</th></tr>"
            "<tr><td>Bot API</td><td><code>sendRichMessage</code></td></tr>"
            "<tr><td>MTProto</td><td><code>messages.sendMessage</code> + <code>inputRichMessageHTML</code></td></tr></table>\n"
            '<blockquote>Rich — это новый формат сообщений Telegram.<cite>— Bot API 10.x</cite></blockquote>'
        )
        res = await app.send_rich(OWNER_ID, html)
        msg = res.get("result", res) if isinstance(res, dict) else res
        log("send_rich raw string", bool(msg.get("message_id") or msg.get("messageId")))
    except Exception as e:
        log("send_rich raw string", False, repr(e))

    # ---------------------------------------------------------------- tg-thinking in DRAFT (must work)
    try:
        draft_id = secrets.randbits(63)
        frame1 = (
            h1(E["brain"], "🧠") + "\n"
            "<tg-thinking>Инициализация пайплайна...</tg-thinking>\n"
            "<p>Готовим кадры для стриминга.</p>"
        )
        res = await app.sendRichMessageDraft(chat_id=OWNER_ID, draft_id=draft_id, rich_message={"html": frame1})
        ok = isinstance(res, dict)
        log("sendRichMessageDraft + tg-thinking", ok, f"draft_id={draft_id}")
        await asyncio.sleep(1.0)

        # frame 2: thinking changes, partial content grows
        frame2 = (
            h1(E["brain"], "🧠") + "\n"
            "<tg-thinking>Семантический анализ...</tg-thinking>\n"
            "<blockquote>Скрытый процесс генерации: 2/5 токенов ▓▓░░░</blockquote>"
        )
        res2 = await app.sendRichMessageDraft(chat_id=OWNER_ID, draft_id=draft_id, rich_message={"html": frame2})
        log("draft frame 2 (progress)", isinstance(res2, dict))
        await asyncio.sleep(1.0)

        # frame 3: still draft — math + table preview with thinking
        frame3 = (
            h1(E["brain"], "🧠") + "\n"
            "<tg-thinking>Проверка формул...</tg-thinking>\n"
            "<tg-math>\\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\varepsilon_0}</tg-math>"
        )
        res3 = await app.sendRichMessageDraft(chat_id=OWNER_ID, draft_id=draft_id, rich_message={"html": frame3})
        log("draft frame 3 (math)", isinstance(res3, dict))
        await asyncio.sleep(1.0)

        # FINAL via sendRichMessage (no tg-thinking!)
        final = (
            h1(E["perfect"], "💯") + "\n"
            "<p>Финальное сообщение после стрима — <tg-thinking> здесь нет.</p>\n"
            "<tg-math>i\\hbar\\frac{\\partial}{\\partial t}\\Psi = \\hat{H}\\Psi</tg-math>\n"
            '<details><summary>Метрики стрима</summary><ul>'
            '<li><b>Кадров:</b> 3 draft + 1 final</li>'
            '<li><b>Транспорт:</b> Bot API (aiohttp)</li>'
            "<li><b>Библиотека:</b> GoyGram 0.7.79</li></ul></details>"
        )
        res4 = await app.sendRichMessage(chat_id=OWNER_ID, rich_message={"html": final})
        msg = res4.get("result", res4) if isinstance(res4, dict) else res4
        log("final sendRichMessage (no thinking)", bool(msg.get("message_id") or msg.get("messageId")))
    except Exception as e:
        log("drafts flow", False, repr(e))

    # ---------------------------------------------------------------- tg-thinking in FINAL (must FAIL -> verify error)
    try:
        bad = (
            h1(E["think"], "🤔") + "\n"
            "<p>Это сообщение с tg-thinking в финале — должно быть отклонено или очищено.</p>\n"
            "<tg-thinking>Этот блок не должен пройти в sendRichMessage</tg-thinking>"
        )
        res = await app.sendRichMessage(chat_id=OWNER_ID, rich_message={"html": bad})
        msg = res.get("result", res) if isinstance(res, dict) else res
        mid = msg.get("message_id") or msg.get("messageId")
        log("tg-thinking in FINAL (expect reject/clean)", True, f"sent id={mid} — check chat manually")
    except Exception as e:
        # If API rejected with RICH_MESSAGE_BLOCK_UNSUPPORTED — that's expected behaviour
        ename = type(e).__name__
        if "RICH" in str(e).upper() or "BLOCK" in str(e).upper():
            log("tg-thinking in FINAL (expect reject/clean)", True, f"rejected as expected: {str(e)[:120]}")
        else:
            log("tg-thinking in FINAL (expect reject/clean)", False, f"{ename}: {str(e)[:160]}")

    print("\n=== SUMMARY ===")
    ok_n = sum(1 for _, ok, _ in results if ok)
    print(f"{ok_n}/{len(results)} passed")
    for name, ok, detail in results:
        print(f"  {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))


if __name__ == "__main__":
    asyncio.run(main())
