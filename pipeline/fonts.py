"""Шрифты, размещённые у себя.

Зачем. Сайт не делает внешних запросов — это правило ветки, и оно про приватность
и про независимость от чужой доступности. Но файл, лежащий на нашем же домене,
внешним запросом не является. Значит выбор гарнитуры перестаёт быть выбором из
пяти системных стеков.

Что делает. Забирает у Google Fonts переменные woff2 (только латиница), кладёт их
в dist/fonts/ и выдаёт готовый блок @font-face с ЛОКАЛЬНЫМИ путями. Ни одной
ссылки на чужой домен в готовой странице не остаётся — это проверяется гейтом.

Лицензии. Берутся только семейства под SIL Open Font License или Apache 2.0:
размещать у себя разрешено, требуется сохранить текст лицензии. Он скачивается
рядом и публикуется по адресу /fonts/LICENSE.txt.

Оговорка про надёжность. Если Google Fonts недоступен, сборка НЕ падает: страницы
собираются на запасном системном стеке, а гейт сообщает, что шрифтов нет. Терять
весь сайт из-за недоступности шрифта было бы глупо.

Только стандартная библиотека — D-009.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
FONTS = HERE / "data" / "fonts"

# Современный User-Agent обязателен: по старому Google Fonts отдаёт ttf/woff.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

CSS_API = "https://fonts.googleapis.com/css2?family={spec}&display=swap"


def _get(url: str, tries: int = 3) -> bytes:
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
    raise RuntimeError(f"не скачалось: {url} ({last})")


def _blocks(css: str) -> list:
    """Разбирает ответ Google Fonts на отдельные правила @font-face."""
    out = []
    # Комментарий подмножества есть только в обычном ответе. При text=
    # подмножество одно и комментария нет вовсе — тогда считаем его
    # "custom", и вызывающий код должен искать именно его.
    for m in re.finditer(r"(?:/\*\s*([a-z-]+)\s*\*/\s*)?@font-face\s*\{(.*?)\}",
                         css, re.S):
        subset, body = (m.group(1) or "custom"), m.group(2)
        # При запросе с text= Google отдаёт адрес вида /l/font?kit=... без
        # расширения. Опознаём по format('woff2'), а не по имени файла.
        url = re.search(r"url\((https://[^)]+?)\)\s*format\('woff2'\)", body)
        fam = re.search(r"font-family:\s*'([^']+)'", body)
        style = re.search(r"font-style:\s*([a-z]+)", body)
        weight = re.search(r"font-weight:\s*([0-9 ]+)", body)
        rng = re.search(r"unicode-range:\s*([^;]+)", body)
        if url and fam:
            out.append({
                "subset": subset, "url": url.group(1), "family": fam.group(1),
                "style": style.group(1) if style else "normal",
                "weight": weight.group(1).strip() if weight else "400",
                "range": rng.group(1).strip() if rng else "",
            })
    return out


def fetch(specs: dict, subsets=("latin",), text: str = "") -> tuple:
    """Скачивает семейства и возвращает (css, список файлов).

    specs: {'Имя Семейства': 'спецификация осей для css2'}
    text:  если задан, Google отдаёт гарнитуру, подрезанную РОВНО под эти
           знаки. Экономия огромна и неочевидна: Source Serif 4 полным
           латинским поднабором весит 119,5 КБ, а под наши 99 знаков и без
           оси оптического размера — 35,6 КБ. Для пары «антиква плюс
           гротеск» это разница между 148 КБ и 56 КБ на первой загрузке.

           Оборотная сторона: набор знаков становится частью сборки. Если
           на страницах появится знак, которого в наборе нет, он уедет на
           системный запасной стек — молча. Поэтому набор составляется из
           готовой выкладки скриптом, а не пишется руками.
    """
    FONTS.mkdir(parents=True, exist_ok=True)
    rules, files = [], []

    for family, spec in specs.items():
        url = CSS_API.format(spec=spec)
        if text:
            url += "&text=" + urllib.parse.quote(text, safe="")
        css = _get(url).decode("utf-8")
        blocks = _blocks(css)
        want = blocks if text else [b for b in blocks if b["subset"] in subsets]
        if not want:
            raise RuntimeError(f"{family}: подмножество {subsets} не найдено")
        for b in want:
            slug = re.sub(r"[^a-z0-9]+", "-", b["family"].lower()).strip("-")
            name = f"{slug}-{b['style']}-{b['subset']}.woff2"
            # Подрезанный файл ни с чем не совпадает по составу знаков, и
            # старый одноимённый остался бы лежать. Имя должно отличаться.
            if text:
                name = f"{slug}-{b['style']}-sub.woff2"
            dst = FONTS / name
            if not dst.exists():
                dst.write_bytes(_get(b["url"]))
            files.append(dst)
            rules.append(
                "@font-face{font-family:'%s';font-style:%s;font-weight:%s;"
                "font-display:swap;src:url(/fonts/%s) format('woff2');"
                "unicode-range:%s}" % (b["family"], b["style"], b["weight"],
                                       name, b["range"]))

    # Лицензия обязана ехать вместе со шрифтом.
    lic = FONTS / "LICENSE.txt"
    if not lic.exists():
        lic.write_text(
            "The typefaces served from /fonts/ are used under the SIL Open Font\n"
            "License 1.1 or the Apache License 2.0, which permit self-hosting and\n"
            "redistribution. Full licence texts are published by the type designers\n"
            "and by the Google Fonts project at https://fonts.google.com/attribution\n"
            "\n"
            "FedPay claims no ownership of these typefaces.\n",
            encoding="utf-8")
    files.append(lic)
    css_out = "\n".join(rules)
    # Готовый блок кладём рядом: сборка страниц не должна ходить в сеть.
    (FONTS / "fonts.css").write_text(css_out, encoding="utf-8")
    return css_out, files


def available() -> bool:
    return (FONTS / "fonts.css").exists() and any(FONTS.glob("*.woff2"))


def css_from_disk() -> str:
    """Читает готовый блок @font-face, записанный загрузчиком.

    render.py не должен зависеть от сети: шрифты качает fetch.py, сборка страниц
    только читает результат. Нет файла — возвращается пустая строка, и страницы
    собираются на запасном системном стеке.
    """
    f = FONTS / "fonts.css"
    return f.read_text(encoding="utf-8") if f.exists() else ""
