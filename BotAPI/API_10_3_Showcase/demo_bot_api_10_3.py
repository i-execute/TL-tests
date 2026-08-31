
import asyncio
import aiohttp
import traceback
import base64
import time
import os
import re
import random

TOKEN = "8842320592:AAGIwEtJA2SbwFF1qtYIQTDd7B6G_YKu3wA"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

async def send_request(session, method, payload):
    url = f"{API_URL}/{method}"
    for _ in range(3):
        try:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    if data.get("error_code") == 429:
                        retry_after = data.get("parameters", {}).get("retry_after", 1)
                        print(f"Rate limited ({method}). Sleeping {retry_after}s...")
                        await asyncio.sleep(retry_after + 0.1)
                        continue
                    print(f"API Error ({method}):", data)
                return data
        except Exception as e:
            print(f"Request Exception ({method}):", e)
            await asyncio.sleep(1)
    return {"ok": False}

def generate_bar(percent, length=12):
    percent = max(0, min(100, percent))
    filled = int((percent / 100) * length)
    empty = length - filled
    return "█" * filled + "░" * empty

def get_real_stats():
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_s = float(f.readline().split()[0])
            uptime_str = f"{int(uptime_s // 86400)}d {int((uptime_s % 86400) // 3600)}h {int((uptime_s % 3600) // 60)}m"
        with open('/proc/loadavg', 'r') as f:
            load = f.readline().split()[:3]
            cpu_str = f"{load[0]}, {load[1]}, {load[2]}"
            cpu_pct = min(100, float(load[0]) * 10)
        with open('/proc/meminfo', 'r') as f:
            content = f.read()
            total = int(re.search(r"MemTotal:\s+(\d+)", content).group(1))
            free = int(re.search(r"MemFree:\s+(\d+)", content).group(1))
            buffers = int(re.search(r"Buffers:\s+(\d+)", content).group(1))
            cached = int(re.search(r"Cached:\s+(\d+)", content).group(1))
            used = total - free - buffers - cached
            ram_pct = (used / total) * 100
            ram_str = f"{used // 1024} MB / {total // 1024} MB"
        
        cpu_bar = generate_bar(cpu_pct)
        ram_bar = generate_bar(ram_pct)
        return uptime_str, cpu_str, cpu_bar, ram_str, ram_bar, cpu_pct, ram_pct
    except Exception as e:
        return "N/A", "N/A", "██░░░░░░░░", "N/A", "██░░░░░░░░", 0, 0

def get_main_menu(chat_id, message_id=None):
    html = (
        '<h1><tg-emoji emoji-id="5449619723966761441">😌</tg-emoji> Ultimate Bot API 10.3 Showcase</h1>\n'
        '<p>Добро пожаловать в премиальный демонстрационный стенд. Этот интерфейс полностью построен на новых блоках <b>Rich Messages</b>.</p>\n'
        '<aside>The future of communication is structured, elegant, and instantly delivered.<cite>— Hermes Core</cite></aside>\n'
        '<tg-button-row>'
        '<tg-button type="callback_data" data="demo_format"><tg-emoji emoji-id="5192784923093652913">📅</tg-emoji> Формат</tg-button>'
        '<tg-button type="callback_data" data="demo_math"><tg-emoji emoji-id="5384182985224374928">🧐</tg-emoji> Math</tg-button>'
        '</tg-button-row>\n'
        '<tg-button-row>'
        '<tg-button type="callback_data" data="demo_map"><tg-emoji emoji-id="5447163161587241349">🗺</tg-emoji> Карта</tg-button>'
        '<tg-button type="callback_data" data="demo_llm"><tg-emoji emoji-id="5447595110743168717">🧠</tg-emoji> NLP Stream</tg-button>'
        '</tg-button-row>\n'
        '<tg-button-row>'
        '<tg-button type="callback_data" data="demo_stats"><tg-emoji emoji-id="5384182740411240426">💯</tg-emoji> Stats</tg-button>'
        '<tg-button type="callback_data" data="noop2"><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Options</tg-button>'
        '</tg-button-row>'
    )
    payload = {"chat_id": chat_id, "rich_message": {"html": html}}
    if message_id: payload["message_id"] = message_id
    return payload

def get_stats_menu(chat_id, message_id):
    uptime, cpu, cpu_bar, ram, ram_bar, cpu_p, ram_p = get_real_stats()
    html = (
        '<h1><tg-emoji emoji-id="5384182740411240426">💯</tg-emoji> Инфраструктура Сервера</h1>\n'
        '<p>Реальные данные с хост-машины (Ubuntu / Linux), обновляются в реальном времени при нажатии.</p>\n'
        '<table>'
        '<tr><th>Метрика</th><th>Значение</th><th>Загрузка</th></tr>'
        f'<tr><td><b>CPU Load</b></td><td>{cpu}</td><td><code>{cpu_bar}</code></td></tr>'
        f'<tr><td><b>Memory</b></td><td>{ram}</td><td><code>{ram_bar}</code></td></tr>'
        f'<tr><td><b>Uptime</b></td><td>{uptime}</td><td><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Stable</td></tr>'
        '</table>\n'
        '<details><summary><tg-emoji emoji-id="5447595110743168717">🧠</tg-emoji> Подробности об окружении</summary>'
        '<p>Процессы-потребители ограничены namespace\'ами. Основной юзербот <code>heroku</code> утилизирует выделенные квоты, оставляя ресурсы для демона Hermes Agent.</p>'
        '</details>\n'
        '<tg-button-row>'
        '<tg-button type="callback_data" data="demo_stats"><tg-emoji emoji-id="5877410604225924969">🔄</tg-emoji> Обновить</tg-button>'
        '<tg-button type="callback_data" data="back"><tg-emoji emoji-id="5449619723966761441">😌</tg-emoji> Назад</tg-button>'
        '</tg-button-row>'
    )
    return {"chat_id": chat_id, "message_id": message_id, "rich_message": {"html": html}}

def get_options_menu(chat_id, message_id):
    html = (
        '<h1><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Настройки</h1>\n'
        '<p>Выберите желаемую модель для стриминга:</p>\n'
        '<ul>'
        '<li><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> <b>free-gemini-3.1-pro-preview</b> (Active)</li>'
        '<li><tg-emoji emoji-id="5384157249780337109">😑</tg-emoji> <i>claude-3-5-sonnet-20240620</i></li>'
        '<li><tg-emoji emoji-id="5384157249780337109">😑</tg-emoji> <i>Qwen/Qwen2.5-7B-Instruct</i></li>'
        '<li><tg-emoji emoji-id="5384157249780337109">😑</tg-emoji> <i>gpt-4o</i></li>'
        '</ul>\n'
        '<tg-button-row>'
        '<tg-button type="callback_data" data="back"><tg-emoji emoji-id="5449619723966761441">😌</tg-emoji> Назад</tg-button>'
        '</tg-button-row>'
    )
    return {"chat_id": chat_id, "message_id": message_id, "rich_message": {"html": html}}

def get_format_menu(chat_id, message_id):
    html = (
        '<h1><tg-emoji emoji-id="5192784923093652913">📅</tg-emoji> Глубокое Форматирование</h1>\n'
        '<p>Здесь представлена мощь блочной верстки. Поддерживаются любые вложенные структуры.</p>\n'
        '<table>'
        '<tr><th>Модуль</th><th>Статус</th><th>Оптимизация</th></tr>'
        '<tr><td><b>Gateway</b></td><td><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Online</td><td>99%</td></tr>'
        '<tr><td><b>Inference</b></td><td><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Active</td><td>94%</td></tr>'
        '<tr><td><b>Vector DB</b></td><td><tg-emoji emoji-id="5384157249780337109">😑</tg-emoji> Standby</td><td>---</td></tr>'
        '</table>\n'
        '<details><summary><tg-emoji emoji-id="5384182985224374928">🧐</tg-emoji> Исходный код ядра (Rust)</summary>'
        '<pre><code class="language-rust">'
        'fn initialize_quantum_core() -> Result<(), Error> {\n'
        '    let core = QuantumCore::new(Qubits::max());\n'
        '    core.entangle_all()?;\n'
        '    Ok(())\n'
        '}'
        '</code></pre></details>\n'
        '<details><summary><tg-emoji emoji-id="5384182985224374928">🧐</tg-emoji> Исходный код пайплайна (Python)</summary>'
        '<pre><code class="language-python">'
        '@app.route("/stream")\n'
        'async def stream_tokens(req):\n'
        '    return web.Response(text="Done")\n'
        '</code></pre></details>\n'
        '<aside>Чистый код — это не тот, который написан без ошибок, а тот, который читается как хорошая проза.<cite>— Роберт Мартин</cite></aside>\n'
        '<tg-button-row>'
        '<tg-button type="callback_data" data="back"><tg-emoji emoji-id="5449619723966761441">😌</tg-emoji> В меню</tg-button>'
        '</tg-button-row>'
    )
    return {"chat_id": chat_id, "message_id": message_id, "rich_message": {"html": html}}

def get_math_menu(chat_id, message_id):
    html = (
        '<h1><tg-emoji emoji-id="5384182985224374928">🧐</tg-emoji> Высшая Математика</h1>\n'
        '<p>Отрисовка сложных формул через нативный LaTeX движок.</p>\n'
        '<h3>Уравнение Шрёдингера</h3>\n'
        '<tg-math>i\\hbar\\frac{\\partial}{\\partial t}\\Psi(\\mathbf{r},t) = \\hat{H}\\Psi(\\mathbf{r},t)</tg-math>\n'
        '<h3>Уравнения Навье-Стокса</h3>\n'
        '<tg-math>\\rho \\left(\\frac{\\partial \\mathbf{v}}{\\partial t} + \\mathbf{v} \\cdot \\nabla \\mathbf{v}\\right) = -\\nabla p + \\mu \\nabla^2 \\mathbf{v} + \\mathbf{f}</tg-math>\n'
        '<h3>Уравнения поля Эйнштейна</h3>\n'
        '<tg-math>R_{\\mu \\nu} - \\frac{1}{2} R g_{\\mu \\nu} + \\Lambda g_{\\mu \\nu} = \\frac{8 \\pi G}{c^4} T_{\\mu \\nu}</tg-math>\n'
        '<p>Математика внутри текста: гравитационная постоянная <tg-math>G \\approx 6.674 \\times 10^{-11} \\text{ N}\\cdot\\text{m}^2/\\text{kg}^2</tg-math>, что делает расчёты крайне точными.</p>\n'
        '<tg-button-row><tg-button type="callback_data" data="back"><tg-emoji emoji-id="5449619723966761441">😌</tg-emoji> В меню</tg-button></tg-button-row>'
    )
    return {"chat_id": chat_id, "message_id": message_id, "rich_message": {"html": html}}

def get_map_menu(chat_id, message_id):
    html = (
        '<h1><tg-emoji emoji-id="5192784923093652913">🗺</tg-emoji> Интерактивная Карта</h1>\n'
        '<p>Нативная интеграция гео-точек прямо внутри Rich Messages.</p>\n'
        '<h3>🗺️ Токио, Япония</h3>\n'
        '<tg-map lat="35.6895" long="139.6917" zoom="12"/>\n'
        '<p>Сноски также поддерживаются для гео-данных.<tg-reference name="ref-tokyo">35.6895° N, 139.6917° E</tg-reference></p>\n'
        '<tg-button-row><tg-button type="callback_data" data="back"><tg-emoji emoji-id="5449619723966761441">😌</tg-emoji> В меню</tg-button></tg-button-row>'
    )
    return {"chat_id": chat_id, "message_id": message_id, "rich_message": {"html": html}}

def make_glitch(word):
    chars = list(word)
    glitch_chars = ["█", "▓", "▒", "░", "§", "∆", "×", "÷"]
    for i in range(len(chars)):
        if random.random() > 0.3:
            chars[i] = random.choice(glitch_chars)
    res = "".join(chars)
    tag = random.choice(["mark", "s", "code", "b", "i"])
    return f"<{tag}>{res}</{tag}>"

async def run_llm_demo(session, chat_id):
    draft_id = int(time.time())
    header = '<h1><tg-emoji emoji-id="5447595110743168717">🧠</tg-emoji> NLP Pipeline Visualization</h1>\n'
    
    think_phrases = [
        "Initializing Causal LM heads...",
        "Computing cross-attention...",
        "Sampling logits (Temperature: 0.7)...",
        "Loading Masked LM weights...",
        "Evaluating bidirectional context...",
        "Predicting masked token IDs..."
    ]

    text1_words = ["The", "cat", "sat", "on", "the", "mat."]
    text2_words = ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog."]
    
    # Send initial draft
    await send_request(session, "sendRichMessageDraft", {
        "chat_id": chat_id, "draft_id": draft_id, 
        "rich_message": {"html": header + '<tg-thinking>Waking up Neural Network...</tg-thinking>\n'}
    })
    await asyncio.sleep(0.6)
    
    # Stage 1: Causal LM (Next Token) with Glitches
    accumulated_1 = ""
    for i, word in enumerate(text1_words):
        think = think_phrases[i % 3]
        
        # Frame A: Heavy Glitch
        glitch_word_1 = make_glitch(word)
        html_a = (
            header +
            f'<tg-thinking>{think}</tg-thinking>\n' +
            '<h3><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Causal LM Generation</h3>\n' +
            f'<blockquote>{accumulated_1} {glitch_word_1}</blockquote>\n'
        )
        await send_request(session, "sendRichMessageDraft", {
            "chat_id": chat_id, "draft_id": draft_id, "rich_message": {"html": html_a}
        })
        await asyncio.sleep(0.5)
        
        # Frame B: Light Glitch
        glitch_word_2 = make_glitch(word)
        html_b = (
            header +
            f'<tg-thinking>{think}</tg-thinking>\n' +
            '<h3><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Causal LM Generation</h3>\n' +
            f'<blockquote>{accumulated_1} {glitch_word_2}</blockquote>\n'
        )
        await send_request(session, "sendRichMessageDraft", {
            "chat_id": chat_id, "draft_id": draft_id, "rich_message": {"html": html_b}
        })
        await asyncio.sleep(0.5)
        
        accumulated_1 += word + " "

    # Stage 2: Masked LM (Attention)
    mask_targets = [1, 3, 7] # quick, fox, lazy
    for i, target_idx in enumerate(mask_targets):
        
        # Two frames of glitchy decoding for the mask
        for _ in range(2):
            t2_display = []
            for j, w in enumerate(text2_words):
                if j == target_idx:
                    t2_display.append(make_glitch(w))
                elif j > target_idx and j in mask_targets:
                    t2_display.append(f'<mark>[MASK]</mark>')
                else:
                    t2_display.append(w)
            
            text2_html = " ".join(t2_display)
            think = think_phrases[3 + (i % 3)]
            
            html = (
                header +
                f'<tg-thinking>{think}</tg-thinking>\n' +
                '<h3><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Causal LM</h3>\n' +
                f'<blockquote>{accumulated_1}</blockquote>\n' +
                '<h3><tg-emoji emoji-id="5384182985224374928">🧐</tg-emoji> Masked LM</h3>\n' +
                f'<blockquote>{text2_html}</blockquote>\n'
            )
            await send_request(session, "sendRichMessageDraft", {
                "chat_id": chat_id, "draft_id": draft_id, "rich_message": {"html": html}
            })
            await asyncio.sleep(0.6)

    # Final Message
    final_html = (
        header +
        '<h3><tg-emoji emoji-id="5447363161034346459">👌</tg-emoji> Causal LM</h3>\n' +
        f'<blockquote>{accumulated_1}</blockquote>\n' +
        '<h3><tg-emoji emoji-id="5384182985224374928">🧐</tg-emoji> Masked LM</h3>\n' +
        f'<blockquote>{" ".join(text2_words)}</blockquote>\n' +
        '<details><summary><tg-emoji emoji-id="5447595110743168717">🧠</tg-emoji> NLP Metrics</summary>' +
        '<ul><li><b>Pangram Score:</b> 100% (A-Z)</li><li><b>Attention:</b> Bidirectional Transformer</li><li><b>Latency:</b> 42ms/token</li></ul></details>\n' +
        '<tg-button-row><tg-button type="callback_data" data="back"><tg-emoji emoji-id="5449619723966761441">😌</tg-emoji> Назад</tg-button></tg-button-row>'
    )
    
    await send_request(session, "sendRichMessage", {
        "chat_id": chat_id, "rich_message": {"html": final_html}
    })

async def handle_callback(session, callback_id, data, chat_id, message_id):
    await send_request(session, "answerCallbackQuery", {"callback_query_id": callback_id})
    
    try:
        decoded = base64.b64decode(data).decode('utf-8')
    except:
        decoded = data
        
    actual = decoded if decoded in ("demo_format", "demo_math", "demo_map", "demo_stats", "demo_llm", "back", "noop2") else data

    if actual == "demo_format":
        await send_request(session, "editMessageText", get_format_menu(chat_id, message_id))
    elif actual == "demo_math":
        await send_request(session, "editMessageText", get_math_menu(chat_id, message_id))
    elif actual == "demo_map":
        await send_request(session, "editMessageText", get_map_menu(chat_id, message_id))
    elif actual == "demo_stats":
        await send_request(session, "editMessageText", get_stats_menu(chat_id, message_id))
    elif actual == "noop2":
        await send_request(session, "editMessageText", get_options_menu(chat_id, message_id))
    elif actual == "back":
        await send_request(session, "editMessageText", get_main_menu(chat_id, message_id))
    elif actual == "demo_llm":
        asyncio.create_task(run_llm_demo(session, chat_id))

async def main():
    async with aiohttp.ClientSession() as session:
        print("Bot starting up...")
        offset = None
        while True:
            try:
                params = {"timeout": 30}
                if offset: params["offset"] = offset
                
                async with session.get(f"{API_URL}/getUpdates", params=params) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(2)
                        continue
                    
                    data = await resp.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1

                        if "message" in update:
                            msg = update["message"]
                            chat_id = msg["chat"]["id"]
                            if msg.get("text", "").startswith("/start"):
                                await send_request(session, "sendRichMessage", get_main_menu(chat_id))
                                
                        elif "callback_query" in update:
                            cq = update["callback_query"]
                            chat_id = cq["message"]["chat"]["id"]
                            message_id = cq["message"]["message_id"]
                            cb_data = cq.get("data", "")
                            cq_id = cq["id"]
                            
                            await handle_callback(session, cq_id, cb_data, chat_id, message_id)
            except Exception as e:
                print("Poller error:")
                traceback.print_exc()
                await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
