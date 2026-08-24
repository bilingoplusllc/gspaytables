"""Разбор таблиц окладов OPM в один структурированный JSON.

Две вещи здесь важнее остального кода вместе взятого.

ПЕРВОЕ — гейт двойного счёта. Ставку зоны можно вычислить самому:
    base x (1 + pct/100), округлить, срезать по потолку EX-IV.
Мы считаем её сами и сверяем с числом из файла ПОКЛЕТОЧНО. Расхождение хоть на
доллар в любой из ~8700 клеток — падение сборки. Урок MileageCurve: там сравнение
флага с "Y" при значении "Yes" тихо обнулило 217 256 строк, и никто не заметил,
потому что результат выглядел правдоподобно. Соответствие полей доказывается
самим файлом, а не ожиданием.

ВТОРОЕ — ступени НЕ считаются формулой. У GS-1 шаги между ступенями идут
1108, 1099, 1095, 1096, 642, 1088, 1094, 46, 1021 — то есть step1 + (N-1)*WGI
дало бы неверные числа на половине клеток. Только поячеечное чтение.

Только стандартная библиотека — D-009.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

NS = {"p": "http://schemas.datacontract.org/2004/07/PayTables.Business"}
HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "data" / "raw"
OUT = HERE / "data"

# Зона "Rest of U.S." — не город, и в текстах о ней надо говорить иначе.
RUS = "RUS"


def _txt(el, path: str) -> str:
    node = el.find(path, NS)
    if node is None or node.text is None:
        raise ValueError(f"нет узла {path}")
    return node.text.strip()


def parse_description(desc: str) -> dict:
    """Из <Description> достаём процент локалити, имя зоны и дату.

    Формат держится годами, но полагаться на позиции строк нельзя: у AK и HI
    текст короче. Поэтому ищем по смыслу, а не по номеру строки.
    """
    pct = re.search(r"Locality Payment of ([\d.]+)%", desc)
    # Две формы записи имени зоны, и вторая ломает наивный разбор:
    #   "For the Locality Pay Area of San Jose-San Francisco-Oakland, CA"
    #   "State of Alaska" / "State of Hawaii"  <- у AK и HI ПЕРВОЙ формы нет.
    # Из-за этого обе зоны получали пустое имя, оба пути схлопывались в ""
    # и страницы молча затирали друг друга: 58 записей -> 56 файлов.
    area = (re.search(r"For the Locality Pay Area of (.+?)(?:\n|$)", desc)
            or re.search(r"^(State of .+?)\s*$", desc, re.M))
    eff = re.search(r"Effective (\w+ \d{4})", desc)
    incr = re.search(r"Total Increase: ([\d.]+)%", desc)
    return {
        "locality_pct": float(pct.group(1)) if pct else 0.0,
        "area_name": area.group(1).strip() if area else "",
        "effective": eff.group(1) if eff else "",
        "total_increase_pct": float(incr.group(1)) if incr else None,
    }


def parse_table(path: Path) -> dict:
    root = ET.parse(path).getroot()
    code = _txt(root, "p:Abbreviation")
    desc = _txt(root, "p:Description")
    meta = parse_description(desc)

    grades: dict[int, dict[int, dict]] = {}
    for g in root.findall("p:Grades/p:Grade", NS):
        gv = g.find("p:Value", NS)
        if gv is None or not gv.text:
            raise ValueError(f"{code}: у грейда нет <Value>")
        grade = int(gv.text)
        steps: dict[int, dict] = {}
        for s in g.findall("p:Steps/p:Step", NS):
            step = int(_txt(s, "p:Value"))
            steps[step] = {
                "annual": int(_txt(s, "p:Annual")),
                "hourly": float(_txt(s, "p:Hourly")),
                "overtime": float(_txt(s, "p:Overtime")),
                # ВАЖНО: значение здесь 'true'/'false', а не 'Y'/'N'.
                # Сравниваем с текстом самого файла, приведя регистр.
                "capped": _txt(s, "p:Statutory_Cap_Applies").lower() == "true",
            }
        if not steps:
            raise ValueError(f"{code}: грейд {grade} без ступеней")
        grades[grade] = steps

    return {"code": code, "description": desc, **meta, "grades": grades}


def parse_ex_cap(path: Path) -> int:
    """Уровень EX-IV — это и есть законный потолок для GS."""
    root = ET.parse(path).getroot()
    rows = root.findall("p:Rows/p:ArrayOfCell", NS)
    for row in rows:
        cells = [c.find("p:Value", NS) for c in row.findall("p:Cell", NS)]
        vals = [c.text.strip() if c is not None and c.text else "" for c in cells]
        if vals and vals[0].strip().upper() in ("LEVEL IV", "IV"):
            money = re.sub(r"[^\d]", "", vals[1])
            if money:
                return int(money)
    raise ValueError("в EX.xml не найден уровень IV")


def verify(base: dict, loc: dict, cap: int) -> list[str]:
    """Гейт двойного счёта: пересчитываем ставку сами и сверяем с файлом."""
    problems: list[str] = []
    pct = Decimal(str(loc["locality_pct"]))
    for grade, steps in loc["grades"].items():
        for step, cell in steps.items():
            b = base["grades"].get(grade, {}).get(step)
            if b is None:
                problems.append(f"{loc['code']}: GS-{grade}/{step} нет в базовой таблице")
                continue
            raw = Decimal(b["annual"]) * (Decimal(1) + pct / Decimal(100))
            mine = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            capped = mine > cap
            mine = min(mine, cap)
            if mine != cell["annual"]:
                problems.append(
                    f"{loc['code']}: GS-{grade}/{step} посчитано {mine:,}, "
                    f"в файле {cell['annual']:,} (база {b['annual']:,}, {pct}%)")
            if capped != cell["capped"]:
                problems.append(
                    f"{loc['code']}: GS-{grade}/{step} флаг потолка не сходится "
                    f"(посчитано {capped}, в файле {cell['capped']})")
    return problems


def main(year: int = 2026) -> int:
    src = RAW / str(year)
    if not src.exists():
        print(f"нет данных за {year} — сначала fetch.py", file=sys.stderr)
        return 1

    cap = parse_ex_cap(src / "EX.xml")
    print(f"потолок EX-IV {year}: ${cap:,}")

    base = parse_table(src / "GS.xml")
    localities: dict[str, dict] = {}
    for f in sorted(src.glob("*.xml")):
        if f.stem in ("GS", "EX"):
            continue
        localities[f.stem] = parse_table(f)

    print(f"зон: {len(localities)}, грейдов в базе: {len(base['grades'])}")

    # Гейт: у зоны обязано быть имя, иначе адрес страницы схлопнется в пустой
    # и две зоны затрут друг друга. Ровно так в первой сборке потерялись
    # Аляска и Гавайи, и ни одна структурная проверка этого не заметила.
    nameless = [c for c, l in localities.items() if not l["area_name"].strip()]
    if nameless:
        print(f"ГЕЙТ НЕ ПРОЙДЕН: зона без названия: {', '.join(nameless)}",
              file=sys.stderr)
        return 1

    from collections import Counter
    slugs = Counter(re.sub(r"[^a-z0-9]+", "-", l["area_name"].lower()).strip("-")
                    for l in localities.values())
    dup = [s for s, k in slugs.items() if k > 1]
    if dup:
        print(f"ГЕЙТ НЕ ПРОЙДЕН: одинаковый адрес у разных зон: {dup}",
              file=sys.stderr)
        return 1

    # ---- гейт: пересчёт каждой клетки
    all_problems: list[str] = []
    for loc in localities.values():
        all_problems += verify(base, loc, cap)

    cells = sum(len(s) for l in localities.values() for s in l["grades"].values())
    if all_problems:
        print(f"\nГЕЙТ НЕ ПРОЙДЕН: {len(all_problems)} расхождений из {cells:,} клеток",
              file=sys.stderr)
        for p in all_problems[:15]:
            print("  " + p, file=sys.stderr)
        return 1
    print(f"гейт двойного счёта: {cells:,} клеток сошлись до доллара")

    # ---- свежесть по содержимому, а не по имени файла
    if str(year) not in base["effective"]:
        print(f"ГЕЙТ НЕ ПРОЙДЕН: в файле стоит '{base['effective']}', ожидался {year}",
              file=sys.stderr)
        return 1

    OUT.mkdir(exist_ok=True)
    payload = {
        "year": year,
        "effective": base["effective"],
        "ex_iv_cap": cap,
        "base": base,
        "localities": localities,
    }
    dst = OUT / f"paytables-{year}.json"
    dst.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"-> {dst.name} ({dst.stat().st_size:,} байт)")

    capped_cells = [(c, g, s) for c, l in localities.items()
                    for g, steps in l["grades"].items()
                    for s, cell in steps.items() if cell["capped"]]
    print(f"клеток на потолке: {len(capped_cells)} в "
          f"{len({c for c, _, _ in capped_cells})} зонах")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2026))
