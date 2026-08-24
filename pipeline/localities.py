"""Разбор определений зон локалити: какие округа входят в какую зону.

Это единственный источник по-настоящему уникального текста для каждой страницы,
и одновременно ответ на вопрос, которого нет ни у одного конкурента: слово "zip"
не встречается на их страницах ни разу, хотя человек не знает свою зону и ищет
по месту работы.

Две ловушки, о которых предупреждала спецификация и которые здесь обработаны:
1. Не все коды — пятизначные FIPS округов. Есть девятизначные коды военных
   объектов, и регулярка \\d{5} их молча съест, приписав объект не туда.
2. Один и тот же округ может быть в одной зоне, а военная база внутри него —
   в другой (Burlington County NJ в зоне Филадельфии, база в нём — в зоне
   Нью-Йорка). Поэтому храним все записи как есть, не схлопывая.

Только стандартная библиотека — D-009.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "data" / "raw"
DATA = HERE / "data"


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def parse(year: int, wanted: dict[str, str]) -> dict:
    """Достаёт список мест для каждой ИЗВЕСТНОЙ зоны.

    Раньше здесь была попытка выделить заголовок зоны из вёрстки — она дала
    1 зону из 58, потому что разметка OPM непредсказуема. Надёжнее наоборот:
    мы уже знаем все 58 имён из таблиц окладов, поэтому ищем каждое имя в
    тексте и забираем то, что идёт после него до следующего имени.
    """
    src = RAW / str(year) / "locality-definitions.html"
    txt = clean(src.read_text(encoding="utf-8", errors="replace"))

    # Позиция каждого имени в тексте. Берём ПОСЛЕДНЕЕ вхождение: первое —
    # это оглавление вверху страницы, а нам нужен сам раздел.
    marks = []
    for code, name in wanted.items():
        needle = name.replace("State of ", "")
        pos = txt.rfind(needle)
        if pos < 0:
            continue
        marks.append((pos, code, name))
    marks.sort()

    areas: dict[str, dict] = {}
    for i, (pos, code, name) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else len(txt)
        chunk = txt[pos:stop]
        # Отрезаем всё до заголовка таблицы, иначе в улов попадёт само имя зоны.
        if "FIPS" in chunk:
            chunk = chunk.split("FIPS", 1)[1]
        # Коды: 2 знака — штат целиком, 5 — округ, 9 — военный объект.
        places = re.findall(
            r"([A-Z][A-Za-z.'\-/ ]+?(?:,\s*[A-Z]{2})?)\s+(\d{2}|\d{5}|\d{9})(?=\s|$)",
            chunk)
        recs = []
        for pname, pcode in places:
            # У многоштатных зон внутри есть подразделы со своим заголовком
            # таблицы, и служебный текст затекает в начало имени округа:
            # "Back to Top Maryland Place Name FIPS Allegany County, MD".
            # Режем всё до последнего служебного маркера.
            for marker in ("Place Name FIPS", "Place Name", "Back to Top", "FIPS"):
                if marker in pname:
                    pname = pname.rsplit(marker, 1)[-1]
            pname = pname.strip(" ,")
            if not pname or pname.lower() in ("place name", "fips", "back to top"):
                continue
            # Осталось имя штата-подзаголовка в начале? Оно всегда без запятой
            # и без слова County — отбрасываем ведущие слова до первого,
            # после которого идёт "County"/"City"/"Parish"/"Borough".
            m = re.search(r"([A-Z][A-Za-z.'\- ]*?(?:County|Parish|Borough|city|City)"
                          r"(?:,\s*[A-Z]{2})?)$", pname)
            if m:
                pname = m.group(1).strip()
            kind = ("state" if len(pcode) == 2 else
                    "county" if len(pcode) == 5 else "installation")
            recs.append({"name": pname, "code": pcode, "kind": kind})
        areas[code] = {"places": recs}
    return areas


def main(year: int = 2026) -> int:
    tables = json.loads((DATA / f"paytables-{year}.json").read_text(encoding="utf-8"))
    wanted = {c: l["area_name"] for c, l in tables["localities"].items()}

    areas = parse(year, wanted)

    out, empty = {}, []
    for code in wanted:
        places = areas.get(code, {}).get("places", [])
        counties = [p for p in places if p["kind"] == "county"]
        states = sorted({p["name"].split(", ")[-1] for p in counties if ", " in p["name"]})
        out[code] = {
            "places": places,
            "counties": len(counties),
            "installations": sum(1 for p in places if p["kind"] == "installation"),
            "states": states,
        }
        if not places:
            empty.append((code, wanted[code]))

    (DATA / f"localities-{year}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    total = sum(v["counties"] for v in out.values())
    ok = len(out) - len(empty)
    print(f"определения: {ok} из {len(out)} зон, округов всего {total}")
    if empty:
        print(f"без мест {len(empty)}:")
        for c, nm in empty[:12]:
            print(f"  {c} — {nm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2026))
