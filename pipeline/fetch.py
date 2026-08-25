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

import edition

import fonts

BASE = "https://www.opm.gov"
INDEX = BASE + "/policy-data-oversight/pay-leave/salaries-wages/{year}/general-schedule/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "data" / "raw"

# Индексы цен BEA. Годового ключа API не нужно: архив лежит открыто.
BEA_ZIP = "https://apps.bea.gov/regional/zip/MARPP.zip"
# Индексы по штатам: нужны Аляске и Гавайям, где зона = штат целиком.
BEA_STATE_ZIP = "https://apps.bea.gov/regional/zip/SARPP.zip"
# Связка почтовых районов с округами: нужна, чтобы отвечать на самый частый
# вопрос темы — «какая у меня зона» — по индексу, а не по списку округов.
CENSUS_ZCTA = ("https://www2.census.gov/geo/docs/maps-data/data/rel2020/"
               "zcta520/tab20_zcta520_county20_natl.txt")


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
    # Год издания приходит из одной константы, а не литералом: с зашитым
    # годом январская пересборка молча собрала бы прошлогодние таблицы.
    ap.add_argument("--year", type=int, default=edition.YEAR)
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
    for url, fname, want in ((BEA_ZIP, "marpp.zip", "MARPP_MSA_"),
                            (BEA_STATE_ZIP, "sarpp.zip", "SARPP_STATE_")):
        if not _bea(url, HERE / "data" / fname, want):
            return 1

    zdst = HERE / "data" / "zcta-county.txt"
    try:
        blob = get(CENSUS_ZCTA)
        # Файл обязан быть таблицей с разделителем «|», а не страницей ошибки.
        first = blob[:400].decode("utf-8-sig", errors="replace")
        if "GEOID_ZCTA5" not in first:
            raise RuntimeError(f"это не таблица ZCTA: {first[:80]!r}")
        zdst.write_bytes(blob)
        print(f"  {zdst.name}: {len(blob):,} байт")
    except RuntimeError as e:
        print(f"  {zdst.name}: {e}", file=sys.stderr)
        return 1

    # Шрифт кладём в сборку файлом: внешних запросов на сайте быть не должно,
    # а файл на собственном домене внешним запросом не является.
    try:
        # Набор знаков берётся с запасом относительно нынешней выкладки: гейт
        # покрытия всё равно поймает выход за него, но ронять сборку из-за
        # одного апострофа в новом названии зоны незачем.
        TEXT = ("".join(chr(c) for c in range(0x20, 0x7F))
                + "\u00b7\u00d7\u2013\u2014\u2018\u2019"
                  "\u201c\u201d\u2026\u2212")
        css, ff = fonts.fetch(
            {"Source Serif 4": "Source+Serif+4:wght@400..700",
             "Libre Franklin": "Libre+Franklin:wght@400..700"}, text=TEXT)
        print(f"  шрифт: {len(ff) - 1} файлов, {sum(f.stat().st_size for f in ff):,} байт")
    except RuntimeError as e:
        # Терять весь сайт из-за недоступности шрифта неразумно: страницы
        # соберутся на запасном системном стеке, гейт об этом сообщит.
        print(f"  шрифт: {e} — собираем без него", file=sys.stderr)

    print(f"\nготово: {ok} из {len(codes)} таблиц + BEA + Census -> {out}")
    return 0 if ok == len(codes) else 1


def _bea(url: str, dst: Path, want: str) -> bool:
    """Качает архив BEA и убеждается, что это архив, а не страница с ошибкой."""
    try:
        blob = get(url)
        # BEA отдаёт HTML со статусом 200, когда файл переехал, поэтому
        # проверяем содержимое, а не код ответа.
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            names = z.namelist()
        if not any(n.startswith(want) and n.endswith(".csv") for n in names):
            raise RuntimeError(f"в архиве нет таблицы {want}: {names[:4]}")
        dst.write_bytes(blob)
        print(f"  {dst.name}: {len(blob):,} байт")
        return True
    except (RuntimeError, zipfile.BadZipFile) as e:
        print(f"  {dst.name}: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    raise SystemExit(main())
