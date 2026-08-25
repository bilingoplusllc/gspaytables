"""Самостоятельный снимок собранной страницы — чтобы посмотреть глазами.

Зачем нужен отдельный инструмент. Собранная страница ссылается на /fonts/ и
на /fp.<отпечаток>.js абсолютными путями: открытая двойным кликом, она
покажет системный шрифт и мёртвые контролы, то есть не то, что на самом деле
отгружается. Снимок вшивает гарнитуры в base64 и подставляет скрипт целиком,
поэтому файл можно переслать и открыть где угодно.

Это не сборочный артефакт: в dist он не попадает и в карту сайта не входит.
Только для показа.

    python pipeline/snapshot.py [адрес] [куда]
    python pipeline/snapshot.py /locality/denver-aurora-co/ /tmp/den.html
"""
from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DIST = HERE / "dist"


def snapshot(url: str = "/", out: Path | None = None) -> Path:
    rel = url.strip("/")
    src = DIST / (rel + "/index.html" if rel else "index.html")
    if not src.exists():
        src = DIST / rel
    if not src.exists():
        raise SystemExit(f"нет такой страницы: {src}")

    html = src.read_text(encoding="utf-8")

    # 1. гарнитуры внутрь файла
    def font(m):
        p = DIST / m.group(1).lstrip("/")
        if not p.exists():
            return m.group(0)
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        return f"url(data:font/woff2;base64,{b64})"

    html = re.sub(r"url\((/fonts/[^)]+\.woff2)\)", font, html)

    # 2. скрипт целиком вместо ссылки
    def js(m):
        p = DIST / m.group(1).lstrip("/")
        if not p.exists():
            return m.group(0)
        return "<script>" + p.read_text(encoding="utf-8") + "</script>"

    html = re.sub(r'<script src="(/fp\.[^"]+\.js)"[^>]*></script>', js, html)

    # 3. предзагрузка шрифтов теряет смысл и ведёт в никуда
    html = re.sub(r'<link rel="preload"[^>]*>\s*', "", html)

    # 4. иконки лежат файлами и по file:// не найдутся
    html = re.sub(r'<link rel="(?:apple-touch-)?icon"[^>]*>\s*', "", html)

    out = out or (HERE / "research" / "design-2026-08" /
                  ("snapshot-" + (rel.replace("/", "-") or "home") + ".html"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "/"
    o = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    p = snapshot(u, o)
    print(f"{p}  ({p.stat().st_size / 1024:.0f} КБ)")
