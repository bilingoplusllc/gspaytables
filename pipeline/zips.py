"""Мост «почтовый индекс -> зона локалити».

Зачем. Человек знает свой индекс. Он не знает ни округ, ни официальное имя зоны
(«San Jose-San Francisco-Oakland, CA»). Самый частый вопрос темы — «какая у меня
зона» — на наших страницах до сих пор не имел прямого ответа: мы печатали список
округов и предлагали читателю найти себя в нём.

Как. Бюро переписи публикует связку ZCTA (почтовый район) с округами. У OPM зона
задана списком округов с кодами FIPS. Соединяем по FIPS.

Тонкости, из-за которых наивная версия врёт:

* ZCTA пересекает границы округов. Берём округ с наибольшей ПЛОЩАДЬЮ СУШИ внутри
  этого ZCTA (AREALAND_PART), а не первый попавшийся. Для индексов, попадающих в
  разные зоны локалити, отдаём обе и честно пишем на странице, что индекс на границе.
* ZCTA — не то же самое, что почтовый индекс USPS: часть индексов обслуживают только
  абонентские ящики и своей территории не имеет. Такие в файле отсутствуют, и это надо
  показывать как «не нашли», а не подставлять ближайший.
* Округа, не перечисленные ни в одной зоне, относятся к Rest of U.S. — она определена
  исключением. Поэтому «не нашли округ» и «Rest of U.S.» — разные ответы, и путать их
  нельзя: во втором случае ответ у нас ЕСТЬ.

Только стандартная библиотека — D-009.
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import edition

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"

SRC = DATA / "zcta-county.txt"


def load_crosswalk(path: Path) -> dict:
    """ZCTA -> список (код округа, площадь суши в этом ZCTA)."""
    out: dict[str, list] = {}
    with io.open(path, encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\n").split("|")
        i_z = header.index("GEOID_ZCTA5_20")
        i_c = header.index("GEOID_COUNTY_20")
        i_a = header.index("AREALAND_PART")
        for line in f:
            r = line.rstrip("\n").split("|")
            if len(r) <= i_a:
                continue
            z, c, a = r[i_z].strip(), r[i_c].strip(), r[i_a].strip()
            if not z or not c:
                continue          # строки без ZCTA — это агрегаты по округам
            try:
                area = int(a) if a else 0
            except ValueError:
                area = 0
            out.setdefault(z, []).append((c, area))
    return out


def build() -> int:
    if not SRC.exists():
        raise SystemExit(f"нет файла {SRC} — сначала pipeline/fetch.py")

    locs = json.loads(
        (DATA / f"localities-{edition.YEAR}.json").read_text(encoding="utf-8"))

    # округ -> зона. Берём только пятизначные коды: девятизначные в файле OPM
    # обозначают военные объекты, а не округа, и по индексу их не найти.
    county_zone: dict[str, str] = {}
    state_zone: dict[str, str] = {}
    for code, rec in locs.items():
        for p in rec.get("places", []):
            fips = str(p.get("code", ""))
            kind = p.get("kind")
            if kind == "county" and len(fips) == 5 and fips.isdigit():
                county_zone[fips] = code
            elif kind == "state" and len(fips) == 2 and fips.isdigit():
                # Аляска и Гавайи заданы кодом ШТАТА, а не списком округов.
                # Без этой ветки все их индексы уходили в Rest of U.S. — то есть
                # сайт называл бы неверную зону и неверную зарплату целым двум
                # штатам. Поймано контролем на известных индексах.
                state_zone[fips] = code

    cross = load_crosswalk(SRC)

    zip_zone: dict[str, str] = {}
    split = 0
    for z, parts in cross.items():
        # Все зоны, в которые попадает этот индекс, по убыванию площади.
        seen: dict[str, int] = {}
        for c, area in parts:
            # Порядок важен: сначала точный округ, потом штат целиком, и лишь
            # затем остаток. Штат целиком — это не запасной вариант, а точное
            # определение зоны для Аляски и Гавайев.
            zone = county_zone.get(c) or state_zone.get(c[:2]) or "RUS"
            seen[zone] = seen.get(zone, 0) + area
        if len(seen) > 1:
            split += 1
        best = max(seen.items(), key=lambda kv: kv[1])[0]
        zip_zone[z] = best

    # Компактный формат: две строки вместо словаря на 33 тысячи ключей.
    #   keys  — все индексы подряд, отсортированные, по 5 знаков каждый;
    #   vals  — по одному символу на индекс, позиция символа = позиция индекса.
    # Поиск на клиенте — двоичный по строке. Словарь JSON занимал 369 КБ,
    # этот вид — вдвое меньше, и разбирать его не нужно вовсе.
    zones = sorted({v for v in zip_zone.values()})
    ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    if len(zones) > len(ALPHA):
        raise RuntimeError(f"зон {len(zones)} — алфавита не хватает")
    ordered = sorted(zip_zone.items())
    payload = {
        "zones": zones,
        "keys": "".join(z for z, _ in ordered),
        "vals": "".join(ALPHA[zones.index(v)] for _, v in ordered),
        "note": "ZCTA 2020 (U.S. Census Bureau) x OPM locality pay area definitions",
    }
    dst = DATA / "zip-zone.json"
    dst.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    by_zone: dict[str, int] = {}
    for zone in zip_zone.values():
        by_zone[zone] = by_zone.get(zone, 0) + 1
    print(f"индексов сопоставлено: {len(zip_zone):,} -> {len(zones)} зон")
    print(f"  индексов на границе зон: {split:,} (отдана зона с большей площадью)")
    print(f"  Rest of U.S.: {by_zone.get('RUS', 0):,} индексов "
          f"({100 * by_zone.get('RUS', 0) // max(1, len(zip_zone))}%)")
    print(f"-> {dst.name} ({dst.stat().st_size:,} байт)")

    # Контроль: несколько заведомо известных индексов обязаны попасть куда надо.
    # Без него «сопоставлено 33 000» не значит ничего.
    CHECK = {
        "20001": "DCB",   # жилой Вашингтон (у 20500 нет своей территории)
        "94102": "SF",    # Сан-Франциско
        "10001": "NY",    # Манхэттен
        "35801": "HNT",   # Хантсвилл, Алабама
        "99501": "AK",    # Анкоридж
        "96813": "HI",    # Гонолулу
        "59101": "RUS",   # Биллингс, Монтана — вне всех названных зон
    }
    bad = [(z, want, zip_zone.get(z)) for z, want in CHECK.items()
           if zip_zone.get(z) != want]
    if bad:
        for z, want, got in bad:
            print(f"  КОНТРОЛЬ НЕ ПРОЙДЕН: {z} ожидали {want}, получили {got}")
        return 1
    print(f"  контроль на {len(CHECK)} известных индексах пройден")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
