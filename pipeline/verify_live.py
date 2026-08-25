"""Сверка ОТДАННОГО с СОБРАННЫМ, побайтово, по всем адресам карты сайта.

Зачем отдельная проверка после выкладки. 26.08.2026 все 23 гейта были зелёными,
а живой сайт отдавал не то, что мы собрали: Cloudflare по умолчанию включает
обфускацию почты и подменял контакт в подвале на «[email protected]», дописывая
лишний скрипт на каждую из 164 страниц. Гейты этого не видят по построению —
они читают `dist/`, а правка появляется между `dist/` и читателем.

Побайтовая сверка закрывает весь класс разом: не нужно знать, какие именно
преобразования включены на границе (Rocket Loader, Automatic HTTPS Rewrites,
Server-side Excludes и прочие), достаточно сравнить байты.

Сверять нужно именно БАЙТЫ. Построчный diff однажды показал ноль расхождений
при разнице в 150 байт: чтение файла в текстовом режиме на Windows схлопывает
`\\r\\n`, а чтение из сети — нет.

Отдельно проверяется ответ от лица Googlebot: платформа вправе вести себя с
ботом иначе, а именно он и есть главный посетитель справочного сайта.

Запуск:  python pipeline/verify_live.py
"""
from __future__ import annotations

import io
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

UA_HUMAN = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
UA_BOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

# Сколько страниц проверить от лица бота. Полный обход ботом не нужен: если
# платформа обращается с ботом иначе, это видно на первых же страницах разных
# типов, а лишние запросы от чужого User-Agent — плохая манера к самим себе.
BOT_SAMPLE = 10


def fetch(url: str, ua: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": ua,
        # Просим несжатое, иначе сравнивать пришлось бы после распаковки.
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def local_for(url: str, host: str) -> Path:
    path = url.split(host, 1)[1].strip("/")
    return DIST / (f"{path}/index.html" if path else "index.html")


def main() -> int:
    sm = DIST / "sitemap.xml"
    if not sm.exists():
        print("нет dist/sitemap.xml — сначала собрать сайт", file=sys.stderr)
        return 1

    urls = re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8"))
    if not urls:
        print("в карте сайта нет ни одного адреса", file=sys.stderr)
        return 1
    host = urls[0].split("//", 1)[1].split("/", 1)[0]
    print(f"адресов в карте: {len(urls)}, домен: {host}", flush=True)

    bad: list[str] = []
    for i, url in enumerate(urls, 1):
        lp = local_for(url, host)
        if not lp.exists():
            bad.append(f"{url}: нет локального файла {lp.name}")
            continue
        try:
            live = fetch(url, UA_HUMAN)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            bad.append(f"{url}: не ответил ({e})")
            continue
        want = lp.read_bytes()
        if live != want:
            bad.append(f"{url}: отдано {len(live)} б, собрано {len(want)} б")
        if i % 50 == 0:
            print(f"  проверено {i}", flush=True)

    print(f"расхождений от лица человека: {len(bad)} из {len(urls)}")
    for line in bad[:10]:
        print(f"   {line}")

    # Разные типы страниц, а не первые попавшиеся: если граница ведёт себя
    # с ботом иначе, это чаще зависит от типа страницы, чем от её адреса.
    kinds = ("/locality/", "/gs-", "/promotion/", "/calculator/", "/states/",
             "/compare/", "/about", "/methodology")
    probe = [urls[0]] + [u for u in urls if any(k in u for k in kinds)][:BOT_SAMPLE - 1]
    bot_bad: list[str] = []
    for url in probe:
        try:
            live = fetch(url, UA_BOT)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            bot_bad.append(f"{url}: не ответил ({e})")
            continue
        if live != local_for(url, host).read_bytes():
            bot_bad.append(f"{url}: расхождение")

    print(f"расхождений от лица Googlebot: {len(bot_bad)} из {len(probe)}")
    for line in bot_bad:
        print(f"   {line}")

    if bad or bot_bad:
        print("\nСВЕРКА НЕ ПРОЙДЕНА: живой сайт отдаёт не то, что собрано.",
              file=sys.stderr)
        return 1
    print("\nсверка пройдена: отдано побайтово равно собранному")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
