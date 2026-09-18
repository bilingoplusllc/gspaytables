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

import edition

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


def _lead_city(name: str) -> str:
    """Первый город в названии зоны. OPM называет главный город первым, и
    это единственный осмысленный способ развести ничью между кандидатами с
    одинаковым числом совпадений."""
    head = name.split(",")[0]
    first = re.split(r"[-–/]", head)[0].strip().lower()
    return first


def _states(name: str) -> set[str]:
    """Коды штатов из хвоста названия — ВСЕ, а не первый.

    Здесь была ловушка, стоившая сайту его собственной витрины. Прежняя
    версия брала регуляркой `([A-Z]{2})` ОДИН код: «MO-IL» превращалось в
    «MO». Сравнение потом пересекало БУКВЫ этой строки с буквами другой, и
    `set("MO") & set("NM")` давало `{"M"}` — непустое. То есть проверка
    штата не срабатывала даже там, где штаты разные, и Сент-Луис в Миссури
    получал цены Фармингтона в Нью-Мексико.

    Возвращается МНОЖЕСТВО КОДОВ. Сравнивать множества кодов и множества
    букв — разные действия, и одно из них ничего не проверяет.
    """
    m = re.search(r",\s*([A-Z]{2}(?:-[A-Z]{2})*)", name)
    return set(m.group(1).split("-")) if m else set()


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
                    "cities": _cities(clean), "state": _states(clean)})
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
    """Метро-область для зоны: по городам, по штату и по ПЕРВОМУ городу.

    ТРИ ПРАВИЛА, И НИ ОДНО ИЗ НИХ НЕ ЛИШНЕЕ.

    1. Совпадение по городам. Названия у OPM и BEA пишутся по-разному, и
       сравнивать строки целиком бессмысленно.

    2. Штат обязан пересечься. Раньше эта проверка была НАПИСАНА И ТУТ ЖЕ
       ВЫБРОШЕНА — в её теле стояло `pass`. Шесть зон получали цены чужого
       города, три из них из другого штата: Сент-Луис (Миссури) считался по
       Фармингтону (Нью-Мексико), Колумбус в Огайо — по Колумбусу в
       Джорджии, Рочестер в Нью-Йорке — по Рочестеру в Миннесоте. От этого
       39 рангов «что покупает зарплата» из 57 были неверны, а витрина
       сайта на четверть состояла из артефактов.

    3. НИЧЬЯ РЕШАЕТСЯ ПЕРВЫМ НАЗВАННЫМ ГОРОДОМ, а не порядком строк в файле
       BEA. Тринадцать привязок из 55 решались ничьёй, и семь из них были
       верны по алфавитной случайности. Худший случай ждал своего часа:
       «Omaha-Council Bluffs-FREMONT, NE-IA» набирает по одному совпадению и
       с Омахой (91,9), и с Сан-Франциско-Окленд-ФРИМОНТ (115,6) — разница
       23,7 пункта, то есть 22 853 доллара на ячейке GS-12/5, и держалась
       она ровно на том, что «O» в алфавите раньше «S». Теперь побеждает
       кандидат, содержащий первый город из имени зоны, — OPM называет
       главный город первым.

    Правило «первый город» применяется ТОЛЬКО как тай-брейк. Как приоритет
    оно перекинуло бы Сан-Франциско на Сан-Хосе и сдвинуло 15 зон из 57 —
    это отдельное решение владельца, а не побочный эффект починки.
    """
    want = _cities(area_name)
    st = _states(area_name)
    lead = _lead_city(area_name)
    best, best_score, best_lead = None, 0, False
    for cand in bea:
        # Зоны бывают многоштатные ("DC-MD-VA-WV-PA"), метро — тоже; хватает
        # пересечения по одному коду. Пустой штат у кандидата не отбрасываем:
        # это не отказ, а отсутствие сведений.
        if st and cand["state"] and not (st & cand["state"]):
            continue
        score = len(want & cand["cities"])
        if not score:
            continue
        has_lead = bool(lead) and lead in cand["cities"]
        if score > best_score or (score == best_score and has_lead
                                  and not best_lead):
            best, best_score, best_lead = cand, score, has_lead
    if best is None or best_score == 0:
        return None
    return {"msa": best["msa"], "rpp": best["rpp"],
            "matched_cities": sorted(want & best["cities"]),
            "exact": best_score == len(want)}


def check(payload: dict, bea: list[dict]) -> None:
    """ГЕЙТ ПРИВЯЗКИ. Падает громко, а не печатает предупреждение.

    Зачем он есть. Зарплатные ячейки мы не считаем — мы их переписываем у
    OPM и сверяем дважды. А ВОТ ЭТУ связь мы выбираем сами, и именно она
    даёт сайту его единственное отличие от конкурентов: «что зарплата
    покупает». Она же до сегодняшнего дня была единственным крупным звеном,
    у которого не было ни одной проверки — и шесть зон из 57 ехали с ценами
    чужого города, три из них из другого штата, ПОЛГОДА, при всех зелёных
    гейтах.

    Проверяется ТРИ вещи, и каждая ловит свой класс отказа.
    """
    areas = payload["areas"]
    by_msa = {c["msa"]: c for c in bea}
    bad = []

    # 1. ШТАТ. Тот самый отказ: Сент-Луис в Миссури с ценами Фармингтона в
    #    Нью-Мексико. Сравниваются МНОЖЕСТВА КОДОВ, а не буквы: буквенное
    #    пересечение «MO» и «NM» непусто, и проверка на буквах не проверяет
    #    ничего.
    tables = json.loads(
        (DATA / f"paytables-{edition.YEAR}.json").read_text(encoding="utf-8"))
    for code, v in sorted(areas.items()):
        if not v.get("rpp") or v.get("level") == "state":
            continue
        area_name = tables["localities"][code]["area_name"]
        want = _states(area_name)
        cand = by_msa.get(v["msa"])
        if cand is None:
            bad.append(f"{code}: метро {v['msa']!r} нет в файле BEA")
            continue
        if want and cand["state"] and not (want & cand["state"]):
            bad.append(f"{code}: зона {area_name!r} ({'-'.join(sorted(want))}) "
                       f"получила цены {v['msa']!r} "
                       f"({'-'.join(sorted(cand['state']))}) — другой штат")

    # 2. НИЧЬЯ, КОТОРУЮ НЕ РАЗВЁЛ СМЫСЛ. Тринадцать привязок из 55 решались
    #    порядком строк в файле BEA, и семь были верны по алфавитной
    #    случайности. Худшая: «Omaha-Council Bluffs-FREMONT, NE-IA» одинаково
    #    совпадала с Омахой и с Сан-Франциско-Окленд-ФРИМОНТ — разница 23,7
    #    пункта. Перенумеруй BEA свой файл, и витрина сайта молча
    #    перетасуется. Ничья, не разрешённая первым названным городом, —
    #    это не «выбрали как-нибудь», это «выбрали ничем».
    for code, v in sorted(areas.items()):
        if not v.get("rpp") or v.get("level") == "state":
            continue
        area_name = tables["localities"][code]["area_name"]
        want_c, st = _cities(area_name), _states(area_name)
        lead = _lead_city(area_name)
        score = len(want_c & by_msa[v["msa"]]["cities"]) if v["msa"] in by_msa else 0
        rivals = [c for c in bea
                  if c["msa"] != v["msa"]
                  and (not st or not c["state"] or (st & c["state"]))
                  and len(want_c & c["cities"]) == score
                  and not (lead and lead in c["cities"])]
        if rivals and not (lead and lead in by_msa[v["msa"]]["cities"]):
            bad.append(
                f"{code}: {v['msa']!r} выбрана ничьёй по порядку файла — "
                f"столько же совпадений у {rivals[0]['msa']!r} "
                f"(индексы {v['rpp']} и {rivals[0]['rpp']})")

    # 3. ПУСТАЯ ВЫБОРКА — ТОЖЕ ОТКАЗ. Проверка, которой нечего проверять,
    #    зеленеет ровно так же, как исправная.
    checked = sum(1 for v in areas.values()
                  if v.get("rpp") and v.get("level") != "state")
    if checked < 40:
        bad.append(f"проверено всего {checked} привязок — выборка не та, "
                   f"и зелёный здесь ничего не значит")

    if bad:
        raise RuntimeError("ГЕЙТ ПРИВЯЗКИ УПАЛ:" + "".join(
            "\n  · " + b for b in bad))
    print(f"  гейт привязки: {checked} зон, штат сходится у всех, "
          f"ничьих по порядку файла нет")


def build() -> dict:
    tables = json.loads(
        (DATA / f"paytables-{edition.YEAR}.json").read_text(encoding="utf-8"))
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

    check(payload, bea)

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
