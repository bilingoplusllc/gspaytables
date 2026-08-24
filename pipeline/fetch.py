"""Скачивает таблицы окладов OPM за указанный год.

Список кодов зон берётся ИЗ индексной страницы, а не зашивается: число зон
менялось (48 -> 54 -> 58), и захардкоженный список молча пропустит новую зону.

Только стандартная библиотека — D-009.
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://www.opm.gov"
INDEX = BASE + "/policy-data-oversight/pay-leave/salaries-wages/{year}/general-schedule/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "data" / "raw"

# Индексы цен BEA. Годового ключа API не нужно: архив лежит открыто.
BEA_ZIP = "https://apps.bea.gov/regional/zip/MARPP.zip"


def get(url: str, tries: int = 3) -> bytes:
    last = None
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:  # noqa: PERF203
            last = e
            time.sleep(2 * (n + 1))
    raise RuntimeError(f"не скачалось после {tries} попыток: {url} ({last})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    args = ap.parse_args()
    year = args.year

    out = RAW / str(year)
    out.mkdir(parents=True, exist_ok=True)

    print(f"индекс {year}…", flush=True)
    idx = get(INDEX.format(year=year)).decode("utf-8", "replace")

    # Коды зон вытаскиваем из ссылок на XML этого же года.
    codes = sorted(set(re.findall(
        rf"/salary-tables/xml/{year}/([A-Z0-9]+)\.xml", idx)))
    if not codes:
        print("ОШИБКА: в индексе не найдено ни одной ссылки на XML", file=sys.stderr)
        return 1
    print(f"нашлось таблиц: {len(codes)}")

    # EX (потолок исполнительной шкалы) лежит отдельно и в индексе GS его нет.
    if "EX" not in codes:
        codes.append("EX")

    ok = 0
    for code in codes:
        dst = out / f"{code}.xml"
        url = f"{BASE}/policy-data-oversight/pay-leave/salaries-wages/salary-tables/xml/{year}/{code}.xml"
        try:
            body = get(url)
        except RuntimeError as e:
            print(f"  {code}: {e}", file=sys.stderr)
            continue
        # Пустое тело с кодом 200 — известное поведение OPM на старых годах.
        if len(body) < 512:
            print(f"  {code}: подозрительно мало ({len(body)} байт) — пропущено",
                  file=sys.stderr)
            continue
        dst.write_bytes(body)
        ok += 1
        print(f"  {code}: {len(body):,} байт")

    # Определения зон: какие округа входят в какую зону.
    defs_url = (BASE + "/policy-data-oversight/pay-leave/salaries-wages/"
                f"{year}/locality-pay-area-definitions/")
    try:
        (out / "locality-definitions.html").write_bytes(get(defs_url))
        print("  определения зон: скачаны")
    except RuntimeError as e:
        print(f"  определения зон: {e}", file=sys.stderr)

    # Индексы цен BEA. Без них rpp.py не соберётся, а вместе с ним не
    # соберётся весь сайт: покупательная способность — его единственное
    # отличие от справочников конкурентов.
    bea_dst = HERE / "data" / "marpp.zip"
    try:
        blob = get(BEA_ZIP)
        # Проверяем, что это действительно архив, а не страница с ошибкой:
        # BEA отдаёт HTML со статусом 200, когда файл переехал.
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            names = z.namelist()
        if not any(n.startswith("MARPP_MSA_") and n.endswith(".csv") for n in names):
            raise RuntimeError(f"в архиве нет таблицы MARPP_MSA: {names[:4]}")
        bea_dst.write_bytes(blob)
        print(f"  индексы цен BEA: {len(blob):,} байт")
    except (RuntimeError, zipfile.BadZipFile) as e:
        print(f"  индексы цен BEA: {e}", file=sys.stderr)
        return 1

    print(f"\nготово: {ok} из {len(codes)} таблиц + BEA -> {out}")
    return 0 if ok == len(codes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
