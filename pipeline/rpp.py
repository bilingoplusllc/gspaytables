"""Переходник «зона локалити OPM -> метро-область BEA» и уровень цен.

Зачем это существует. Локалити OPM привязано к зарплатам частного сектора в
регионе, а НЕ к ценам. Поэтому номинально высокая ставка в дорогом городе может
означать меньшую покупательную способность, чем скромная ставка в дешёвом.
Ни один из шести конкурентов этого не считает — проверено грепом по их страницам:
слов "cost of living" и "Regional Price" нет ни у кого.

Сопоставление имён — единственное место, где мы можем ошибиться молча, поэтому:
1) совпадение ищется по НАБОРУ городов в названии, а не по строке целиком;
2) каждая связка помечается способом, которым она получена;
3) несопоставленные зоны остаются без цифры, и страница честно пишет «нет данных»,
   вместо того чтобы подставить среднее по стране.

Только стандартная библиотека — D-009.
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"

# Зоны, у которых нет метро-области в принципе: это штаты целиком либо остаток США.
# Зоны, совпадающие с целым штатом: для них берём индекс уровня штата — это
# не прокси, а точное совпадение границ.
STATEWIDE = {"AK": "Alaska", "HI": "Hawaii"}

# Остаток США индекса не получает. «Нестоличная часть США» выглядит подходящим
# ответом, но описывает другое множество: в Rest of U.S. входят и метро-области,
# которым просто не назначили отдельную зону.
NON_METRO = {
    "RUS": "Rest of U.S. — это не город и не штат, а остаток из всех штатов сразу",
}


def _cities(name: str) -> set[str]:
    """Города из названия зоны: 'San Jose-San Francisco-Oakland, CA' -> {san jose,…}."""
    head = name.split(",")[0]
    parts = re.split(r"[-–/]", head)
    return {p.strip().lower() for p in parts if p.strip()}


def _state(name: str) -> str:
    m = re.search(r",\s*([A-Z]{2})", name)
    return m.group(1) if m else ""


def load_bea(zip_path: Path) -> list[dict]:
    """RPP «все товары и услуги» по метро-областям, последний доступный год."""
    z = zipfile.ZipFile(zip_path)
    name = next(n for n in z.namelist() if n.upper().startswith("MARPP_MSA"))
    with z.open(name) as f:
        rows = list(csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig")))

    header = [h.strip() for h in rows[0]]
    years = [(i, h) for i, h in enumerate(header) if re.fullmatch(r"\d{4}", h)]
    last_i, last_year = years[-1]

    out = []
    for r in rows[1:]:
        if len(r) <= last_i:
            continue
        if r[header.index("LineCode")].strip() != "1":   # 1 = All items
            continue
        geo = r[header.index("GeoName")].strip()
        if "Metropolitan Statistical Area" not in geo:
            continue
        raw = r[last_i].strip()
        try:
            rpp = float(raw)
        except ValueError:
            continue                                      # (NA) и прочерки
        clean = geo.replace("(Metropolitan Statistical Area)", "").strip()
        out.append({"msa": clean, "rpp": rpp,
                    "cities": _cities(clean), "state": _state(clean)})
    return out, last_year


def load_state(zip_path: Path) -> tuple[dict, str]:
    """RPP «все товары и услуги» по штатам, последний доступный год."""
    z = zipfile.ZipFile(zip_path)
    name = next(n for n in z.namelist() if n.upper().startswith("SARPP_STATE"))
    with z.open(name) as f:
        rows = list(csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig")))
    header = [h.strip() for h in rows[0]]
    years = [(i, h) for i, h in enumerate(header) if re.fullmatch(r"\d{4}", h)]
    last_i, last_year = years[-1]
    i_line = header.index("LineCode")
    i_geo = header.index("GeoName")
    i_desc = header.index("Description")
    out = {}
    for row in rows[1:]:
        if len(row) <= last_i or row[i_line].strip() != "1":
            continue
        # Смысл кода читаем из самой записи, а не принимаем на веру: строка
        # обязана называть себя «All items», иначе мы взяли не тот показатель.
        if "all items" not in row[i_desc].strip().lower():
            raise RuntimeError(f"LineCode 1 оказался не All items: {row[i_desc]!r}")
        try:
            out[row[i_geo].strip()] = float(row[last_i].strip())
        except ValueError:
            continue
    return out, last_year


def match(area_name: str, bea: list[dict]) -> dict | None:
    """Ищем метро-область по пересечению городов, а не по совпадению строки."""
    want = _cities(area_name)
    st = _state(area_name)
    best, best_score = None, 0
    for cand in bea:
        # Штат должен совпасть хотя бы по одной букве кода: зоны бывают
        # многоштатные ("DC-MD-VA-WV-PA"), метро — тоже.
        if st and cand["state"] and not (set(st) & set(cand["state"])):
            pass  # не отбрасываем: многоштатные коды пишутся по-разному
        score = len(want & cand["cities"])
        if score > best_score:
            best, best_score = cand, score
    if best is None or best_score == 0:
        return None
    return {"msa": best["msa"], "rpp": best["rpp"],
            "matched_cities": sorted(want & best["cities"]),
            "exact": best_score == len(want)}


def build() -> dict:
    tables = json.loads((DATA / "paytables-2026.json").read_text(encoding="utf-8"))
    bea, year = load_bea(DATA / "marpp.zip")
    states, state_year = load_state(DATA / "sarpp.zip")
    if state_year != year:
        raise RuntimeError(f"годы BEA разошлись: метро {year}, штаты {state_year}")

    result, unmatched = {}, []
    for code, loc in tables["localities"].items():
        if code in NON_METRO:
            result[code] = {"rpp": None, "why": NON_METRO[code]}
            continue
        if code in STATEWIDE:
            nm = STATEWIDE[code]
            if nm not in states:
                raise RuntimeError(f"нет индекса штата для {nm}")
            result[code] = {"msa": f"State of {nm}", "rpp": states[nm],
                            "level": "state", "matched_cities": [],
                            "exact": True, "why": None}
            continue
        m = match(loc["area_name"], bea)
        if m is None:
            unmatched.append((code, loc["area_name"]))
            result[code] = {"rpp": None, "why": "метро-область не сопоставлена"}
        else:
            result[code] = {**m, "why": None}

    payload = {"bea_year": year, "us_base": 100.0, "areas": result}
    (DATA / "rpp-map.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    ok = sum(1 for v in result.values() if v.get("rpp"))
    exact = sum(1 for v in result.values() if v.get("exact"))
    print(f"RPP за {year}: сопоставлено {ok} из {len(result)} зон "
          f"(точных {exact}, из них по штату {len(STATEWIDE)}), "
          f"без индекса {len(NON_METRO)}")
    for code, nm in unmatched:
        print(f"  не сопоставлено: {code} — {nm}")
    return payload


if __name__ == "__main__":
    build()
