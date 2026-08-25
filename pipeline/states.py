"""Страницы по штатам.

Зачем. У federalpay.org страница `/gs/2026/texas` стоит первой в выдаче по
«gs pay scale 2026 texas», у generalschedule.org таких страниц пятьдесят. У нас
не было ни одной, хотя данных для них больше: 920 округов с привязкой к штату
плюс пересчёт на местные цены.

Чем наша сильнее. Конкурент печатает одну таблицу на штат. Но в 24 штатах зон
НЕСКОЛЬКО, и разница между ними доходит до 24 863 долларов на одной и той же
клетке таблицы — в Калифорнии GS-12 ступень 5 стоит от 101 954 до 126 817 в
зависимости от того, в каком округе стоит здание. Это и есть сюжет страницы, и
его нет ни у кого.

Никакого размножения шаблона: текст следует из состава штата. Штат с одной
зоной, штат с шестью и штат целиком внутри Rest of U.S. — три разных страницы,
а не одна с подставленным названием.
"""
from __future__ import annotations

REF_GRADE, REF_STEP = "12", "5"

# Коды и названия штатов. Это не данные о зарплатах, а общеизвестный справочник:
# коды берутся из названий округов OPM, названия нужны для заголовков.
NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida",
    "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

# Зоны, заданные кодом штата, а не списком округов.
STATEWIDE = {"AK": "02", "HI": "15"}


def state_zones(L: dict) -> dict:
    """Штат -> {код зоны: число округов этой зоны в штате}."""
    out: dict[str, dict[str, int]] = {}
    for code, rec in L.items():
        for p in rec.get("places", []):
            if p.get("kind") == "county" and "," in p["name"]:
                st = p["name"].rsplit(",", 1)[1].strip()
            elif p.get("kind") == "state":
                st = {v: k for k, v in STATEWIDE.items()}.get(p.get("code", ""))
                if not st:
                    continue
            else:
                continue
            if st not in NAMES:
                continue
            out.setdefault(st, {})
            out[st][code] = out[st].get(code, 0) + 1
    return out


def state_page(st: str, zones: dict, T: dict, R: dict, ranks: dict,
               shell, esc, money, slug, rail: str = "",
               reach: dict = None) -> tuple:
    """Возвращает (относительный адрес, HTML)."""
    name = NAMES[st]
    year = T["year"]
    locs = T["localities"]

    rows = []
    for code, n_counties in zones.items():
        loc = locs[code]
        cell = loc["grades"][REF_GRADE][REF_STEP]
        rpp = R["areas"].get(code, {}).get("rpp")
        rows.append({
            "code": code, "name": loc["area_name"], "pct": loc["locality_pct"],
            "pay": cell["annual"], "counties": n_counties, "rpp": rpp,
            "adj": cell["annual"] / (rpp / 100.0) if rpp else None,
            "nom": ranks["nominal"].get(code),
            "ka": ranks["adjusted"].get(code),
        })
    rows.sort(key=lambda r: -r["pay"])

    rus = locs["RUS"]["grades"][REF_GRADE][REF_STEP]["annual"]
    hi, lo = rows[0], rows[-1]
    spread = hi["pay"] - lo["pay"]
    n = len(rows)

    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li><a href="/states/">States</a></li>'
         f'<li>{esc(name)}</li></ol>']
    B.append(f'<h1>{esc(name)} GS pay scale, {year}</h1>')

    if n == 1 and rows[0]["code"] == "RUS":
        B.append(f'<p class="sub">Every federal duty station in {esc(name)} is paid '
                 f'at the Rest of U.S. rate. There is no named locality pay area in '
                 f'this state, and no part of it is paid more than any other.</p>')
    elif n == 1:
        B.append(f'<p class="sub">One locality pay area covers the federal jobs in '
                 f'{esc(name)}, at {rows[0]["pct"]:g}% above the nationwide base '
                 f'table. What that is actually worth once local prices are counted '
                 f'is a different question, and this page answers it.</p>')
    else:
        B.append(f'<p class="sub">{n} different locality pay areas cover '
                 f'{esc(name)}, and the same GS-{REF_GRADE} step {REF_STEP} is paid '
                 f'anywhere from {money(lo["pay"])} to {money(hi["pay"])} depending '
                 f'on nothing but which county the building sits in.</p>')

    # --- факты
    facts = []
    facts.append(f'<div class="fact"><p class="fact-k">Locality pay areas</p>'
                 f'<span class="kpi">{n}</span>'
                 f'<span class="kpi-sub">covering federal duty stations in '
                 f'{esc(name)}.</span></div>')
    if n > 1:
        facts.append(f'<div class="fact"><p class="fact-k">Spread within the state</p>'
                     f'<span class="kpi">{money(spread)}</span>'
                     f'<span class="kpi-sub">between the best-paid and worst-paid '
                     f'area here, at GS-{REF_GRADE} step {REF_STEP}. Same grade, '
                     f'same step, same state.</span></div>')
    else:
        facts.append(f'<div class="fact"><p class="fact-k">Locality adjustment</p>'
                     f'<span class="kpi">{rows[0]["pct"]:g}%</span>'
                     f'<span class="kpi-sub">on top of the nationwide base table, '
                     f'for every grade and step.</span></div>')

    best_adj = max((r for r in rows if r["adj"]), key=lambda r: r["adj"], default=None)
    if best_adj and n > 1 and best_adj["code"] != hi["code"]:
        facts.append(f'<div class="fact"><p class="fact-k">Goes furthest here</p>'
                     f'<span class="kpi">{money(best_adj["adj"])}</span>'
                     f'<span class="kpi-sub">of purchasing power in '
                     f'{esc(best_adj["name"])} — which is not the '
                     f'best-paid area in the state.</span></div>')
    elif best_adj:
        facts.append(f'<div class="fact"><p class="fact-k">What it buys</p>'
                     f'<span class="kpi">{money(best_adj["adj"])}</span>'
                     f'<span class="kpi-sub">at average U.S. prices, from a salary '
                     f'of {money(best_adj["pay"])}.</span></div>')

    # Сравнивать зону с самой собой бессмысленно: в штатах, где единственная
    # зона и есть Rest of U.S., карточка показывала «+$0».
    if hi["code"] != "RUS":
        facts.append(f'<div class="fact"><p class="fact-k">Against Rest of U.S.</p>'
                     f'<span class="kpi">+{money(hi["pay"] - rus)}</span>'
                     f'<span class="kpi-sub">is what the best-paid area in '
                     f'{esc(name)} adds over the {money(rus)} paid outside every '
                     f'named area.</span></div>')
    else:
        facts.append(f'<div class="fact"><p class="fact-k">The rate here</p>'
                     f'<span class="kpi">{money(rus)}</span>'
                     f'<span class="kpi-sub">is what a GS-{REF_GRADE} step '
                     f'{REF_STEP} is paid anywhere in {esc(name)} — the same '
                     f'figure as everywhere else outside a named area.</span></div>')
    B.append(f'<div class="facts">{"".join(facts[:4])}</div>')
    B.append('<div class="ad-slot ad-band">Advertisement</div>')

    # --- таблица зон штата
    body = []
    for r in rows:
        adj = money(r["adj"]) if r["adj"] else "—"
        rpp = f'{r["rpp"]:.1f}' if r["rpp"] else "—"
        body.append(
            f'<tr><th scope="row"><a href="/locality/{slug(r["name"])}/">'
            f'{esc(r["name"])}</a></th>'
            f'<td class="num">{r["pct"]:g}%</td>'
            f'<td class="num">{money(r["pay"])}</td>'
            f'<td class="num">{rpp}</td>'
            f'<td class="num">{adj}</td>'
            f'<td class="num">{r["counties"] or "—"}</td></tr>')

    B.append(f'<section class="q" id="areas">'
             f'<h2>Which areas cover {esc(name)}, and what each pays</h2>'
             f'<p class="q-lead">Rates are GS-{REF_GRADE} step {REF_STEP} in {year}. '
             f'The last column is how many counties of this state each area '
             f'covers.</p>'
             f'<div class="scroll" tabindex="0" role="region" '
             f'aria-label="Scrollable table"><table><thead><tr>'
             f'<th>Locality pay area</th><th class="num">Locality pay</th>'
             f'<th class="num">On paper</th><th class="num">Prices</th>'
             f'<th class="num">What it buys</th>'
             f'<th class="num">Counties here</th></tr></thead>'
             f'<tbody>{"".join(body)}</tbody></table></div>')

    if n > 1:
        B.append(f'<p>The spread is {money(spread)} a year on an identical grade and '
                 f'step. Locality pay is set from what private employers in each '
                 f'region pay for comparable work, so an area with a strong private '
                 f'labor market pays more — and an area with expensive '
                 f'housing does not, unless the two happen to coincide.</p>')
        if best_adj and best_adj["code"] != hi["code"]:
            B.append(f'<p>Which is why the best-paid area in {esc(name)} is not the '
                     f'one where the salary goes furthest. '
                     f'<strong>{esc(hi["name"])}</strong> writes the biggest paycheck '
                     f'at {money(hi["pay"])}; '
                     f'<strong>{esc(best_adj["name"])}</strong> pays '
                     f'{money(best_adj["pay"])} and leaves you '
                     f'{money(best_adj["adj"] - (hi["adj"] or best_adj["adj"]))} '
                     f'better off once local prices are counted.</p>')
    B.append('</section>')

    # --- по грейдам
    grid = []
    for g in range(1, 16):
        cells = []
        for r in rows[:6]:
            c = locs[r["code"]]["grades"][str(g)][REF_STEP]
            mark = ' class="num capped"' if c["capped"] else ' class="num"'
            cells.append(f'<td{mark}>{c["annual"]:,}</td>')
        grid.append(f'<tr><th scope="row">GS-{g}</th>{"".join(cells)}</tr>')
    heads = "".join(f'<th class="num">{esc(r["name"].split(",")[0])}</th>'
                    for r in rows[:6])
    B.append(f'<section class="q" id="grades">'
             f'<h2>Every grade at step {REF_STEP} in {esc(name)}</h2>'
             f'<p class="q-lead">Annual rates in U.S. dollars. Cells marked '
             f'&#9650; have been cut to the {money(T["ex_iv_cap"])} statutory '
             f'ceiling.</p>'
             f'<div class="scroll" tabindex="0" role="region" '
             f'aria-label="Scrollable table"><table><thead><tr><th>Grade</th>'
             f'{heads}</tr></thead><tbody>{"".join(grid)}</tbody></table></div>'
             f'<p>Each area has its own full table of 150 rates; follow the links '
             f'above. To put your own grade and step against any of them, use the '
             f'<a href="/calculator/">pay calculator</a>, which will also find your '
             f'area from a ZIP code.</p></section>')

    # --- как это решается
    B.append(f'<section class="q" id="which">'
             f'<h2>Which one applies to you?</h2>'
             f'<p class="q-lead">Your <strong>duty station</strong> decides it '
             f'— the place you physically report to, not where you live and '
             f'not where your agency is headquartered.</p>'
             f'<p>Locality pay areas are defined as lists of counties, and county '
             f'lines rarely follow anything a person would notice. A house on one '
             f'side of a line and an office on the other are paid by the office. '
             f'Telework arrangements have their own rules and can change which area '
             f'applies, so confirm with your servicing human resources office '
             f'rather than assuming.</p>'
             f'<p>A few military installations are assigned by OPM to a different '
             f'area than the county around them: the base gate can be a pay '
             f'boundary. Each area page lists its counties in full.</p>'
             f'</section>')

    # --- переезд внутри штата: вопрос, который и приводит человека сюда
    if n > 1:
        moves = []
        for a in rows[:3]:
            for b in rows[-2:]:
                if a["code"] == b["code"] or not (a["adj"] and b["adj"]):
                    continue
                raw = a["pay"] - b["pay"]
                real = a["adj"] - b["adj"]
                if raw <= 0:
                    continue
                kept = int(round(100 * real / raw)) if raw else 0
                moves.append(
                    f'<li><strong>{esc(b["name"])}</strong> to '
                    f'<strong>{esc(a["name"])}</strong>: {money(raw)} more on '
                    f'paper, {money(real)} more after prices '
                    f'— about {kept}% of what it looks like.</li>')
        if moves:
            B.append(f'<section class="q" id="moving">'
                     f'<h2>What a move inside {esc(name)} is actually worth</h2>'
                     f'<p class="q-lead">Transfers between areas in the same state '
                     f'look like a raise on the offer letter. Here is how much of '
                     f'each one survives contact with local prices.</p>'
                     f'<ul>{"".join(moves[:4])}</ul>'
                     f'<p>The percentage is the part of the headline increase that '
                     f'still buys something once the difference in what things cost '
                     f'is taken out. Where it is small, the move is a change of '
                     f'address rather than a change of income; where it is large, '
                     f'it is a genuine raise. Neither is visible on a pay '
                     f'table.</p>'
                     f'<p>Two things this does not include, and both can matter '
                     f'more than the figures above. State and local income tax is '
                     f'not modelled here at all. Nor is housing tenure: a mortgage '
                     f'signed years ago, or a house owned outright, changes the '
                     f'arithmetic in a way no published price index can see.</p>'
                     f'</section>')

    # --- штат с одной зоной: сравнивать внутри нечего, но есть что сказать
    if n == 1:
        r0 = rows[0]
        if r0["code"] == "RUS":
            B.append(f'<section class="q" id="single">'
                     f'<h2>What it means to have no named pay area</h2>'
                     f'<p class="q-lead">Eight states are in this position, and it '
                     f'is not a judgement about them. It means no part of the state '
                     f'has been designated a separate locality pay area, so the '
                     f'floor of the system applies everywhere in it.</p>'
                     f'<p>Rest of U.S. is the rate for every federal duty station '
                     f'in the country outside the 57 named areas. It is the lowest '
                     f'adjustment there is and the baseline every other area is '
                     f'measured against. At {money(rus)} for a GS-{REF_GRADE} step '
                     f'{REF_STEP}, it is {money(hi["pay"] - rus)} below nothing '
                     f'— there is nothing below it.</p>'
                     f'<p>The practical consequence is simple and worth knowing: '
                     f'inside {esc(name)}, geography does not affect your federal '
                     f'pay at all. Moving across the state for a federal job '
                     f'changes your commute and your rent, and changes your salary '
                     f'by exactly zero.</p>'
                     f'<p>New areas are added occasionally. The Federal Salary '
                     f'Council reviews candidates and recommends additions, the '
                     f'process takes years, and the recommendation is not binding. '
                     f'When an area is added the effect on the people in it is '
                     f'large and immediate: the difference between Rest of U.S. and '
                     f'the new percentage arrives overnight.</p></section>')
        else:
            gap = r0["pay"] - rus
            pct_of = int(round(100 * gap / rus)) if rus else 0
            rank_txt = (f'#{r0["nom"]} of {ranks["n"]} by the size of the paycheck'
                        if r0["nom"] else "unranked")
            adj_txt = (f' and #{r0["ka"]} once local prices are counted'
                       if r0["ka"] else "")
            B.append(f'<section class="q" id="single">'
                     f'<h2>One area, one rate, the whole state</h2>'
                     f'<p class="q-lead">{esc(name)} sits inside a single locality '
                     f'pay area, so a federal job anywhere in the state is paid from '
                     f'exactly the same table.</p>'
                     f'<p>That area is <a href="/locality/{slug(r0["name"])}/">'
                     f'{esc(r0["name"])}</a>, at {r0["pct"]:g}% above the nationwide '
                     f'base. Against the {money(rus)} paid outside every named area, '
                     f'that is {money(gap)} more on a GS-{REF_GRADE} step '
                     f'{REF_STEP} — about {pct_of}% more — and it applies '
                     f'as much to a small office as to the largest facility in the '
                     f'state.</p>'
                     f'<p>Nationally the area ranks {rank_txt}{adj_txt}. Those two '
                     f'numbers being different is the whole subject of this site: '
                     f'locality pay is set from what private employers in the region '
                     f'pay for comparable work, not from what living there costs, '
                     f'and the two do not move together reliably.</p>'
                     f'<p>The practical consequence: inside {esc(name)}, where you '
                     f'work does not change your federal pay. Crossing out of the '
                     f'state can change it a great deal, and the '
                     f'<a href="/calculator/">calculator</a> will tell you by how '
                     f'much for any grade and step.</p></section>')

    # --- города штата: их ищут, а официальные имена зон не ищет никто
    city_bits = []
    for r in rows:
        head = r["name"].split(",")[0]
        if head.startswith("Rest of") or head.startswith("State of"):
            continue
        parts = head.split("--") if "--" in head else head.split("-")
        for c in parts:
            c = c.strip()
            if c and c not in city_bits:
                city_bits.append(c)
    if city_bits:
        chips = "".join(f"<li>{esc(c)}</li>" for c in city_bits)
        B.append(f'<section class="q" id="cities">'
                 f'<h2>Cities named in the {esc(name)} pay areas</h2>'
                 f'<p class="q-lead">OPM names each area after its principal '
                 f'cities. These are the ones that appear in the areas covering '
                 f'{esc(name)}.</p>'
                 f'<ul class="chips-plain">{chips}</ul>'
                 f'<p>The list is a label rather than a boundary. An area reaches '
                 f'well past the city limits of the places it is named after, and '
                 f'plenty of towns nobody would associate with any of them are paid '
                 f'at the same rate. What decides it is the county.</p>'
                 f'<p>Some of these cities are not in {esc(name)} at all: an area '
                 f'named after a city in a neighboring state can still reach across '
                 f'the line and cover counties here. That is the point of the whole '
                 f'system — pay follows labor markets, and labor markets '
                 f'ignore state borders.</p></section>')

    # --- место штата в стране: считается, а не пересказывается
    all_pays = sorted((l["grades"][REF_GRADE][REF_STEP]["annual"]
                       for l in locs.values()), reverse=True)
    better = sum(1 for p in all_pays if p > hi["pay"])
    total_counties = sum(r["counties"] for r in rows)
    B.append(f'<section class="q" id="national">'
             f'<h2>How {esc(name)} sits against the rest of the country</h2>'
             f'<p class="q-lead">Of the {len(all_pays)} locality pay areas in the '
             f'General Schedule, {better} pay more at GS-{REF_GRADE} step '
             f'{REF_STEP} than the best-paid area in {esc(name)}.</p>')
    if total_counties:
        B.append(f'<p>The areas covering this state account for '
                 f'{total_counties} named {"county" if total_counties == 1 else "counties"} '
                 f'of the 920 that OPM lists across the whole system. Every county '
                 f'not on one of those lists falls into Rest of U.S., which is why '
                 f'a state can contain both a named area and large stretches paid '
                 f'at the floor rate.</p>')
    else:
        B.append(f'<p>OPM lists 920 counties across the whole system, and none of '
                 f'them are in {esc(name)}. Every county here falls into Rest of '
                 f'U.S. by exclusion — the area is defined as everything that '
                 f'is not named, rather than as a list of places.</p>')
    B.append(f'<p>Comparing states directly is less useful than it looks. Areas '
             f'cross state lines: several reach into three or more states at once, '
             f'and an employee moving between two of those states inside the same '
             f'area sees no change in pay whatsoever. The unit of the system is the '
             f'area, not the state, and the '
             f'<a href="/">national ranking</a> is the honest way to read it.</p>'
             f'<p>What a state page is good for is the question that brings people '
             f'here: if a federal job in this state comes up, what is it likely to '
             f'pay, and how much does the answer depend on exactly where the '
             f'building is. For {esc(name)} the answer is above.</p></section>')

    # --- куда ещё дотягиваются те же зоны. Различает штаты, накрытые ОДНОЙ
    #     зоной: у Мэна и Род-Айленда она общая, и без этого их страницы
    #     говорили почти одно и то же.
    if reach:
        bits = []
        for r in rows:
            others = sorted(x for x in reach.get(r["code"], set())
                            if x != st and x in NAMES)
            if not others:
                bits.append(
                    f'<li><strong>{esc(r["name"])}</strong> lies entirely within '
                    f'{esc(name)}: it covers {r["counties"]} '
                    f'{"county" if r["counties"] == 1 else "counties"} here and '
                    f'nowhere else.</li>')
            else:
                names_o = ", ".join(NAMES[x] for x in others)
                bits.append(
                    f'<li><strong>{esc(r["name"])}</strong> covers '
                    f'{r["counties"]} {"county" if r["counties"] == 1 else "counties"} '
                    f'in {esc(name)} and also reaches into {esc(names_o)}. A federal '
                    f'employee moving between those states inside this area sees no '
                    f'change in pay at all.</li>')
        if bits:
            B.append(f'<section class="q" id="reach">'
                     f'<h2>Where else these areas reach</h2>'
                     f'<p class="q-lead">Locality pay areas are lists of counties, '
                     f'and county lists ignore state borders entirely.</p>'
                     f'<ul>{"".join(bits)}</ul>'
                     f'<p>This is the part that surprises people transferring. A '
                     f'state line looks like a boundary and usually is one for tax, '
                     f'licensing and a dozen other things. For federal locality pay '
                     f'it is nothing: what matters is whether the county your duty '
                     f'station sits in appears on the list, and lists routinely span '
                     f'several states.</p>'
                     f'<p>It also means the cost of living on either side of such a '
                     f'border can differ while the pay does not — which is one '
                     f'more reason the figure worth watching is not the salary but '
                     f'what the salary buys.</p></section>')

    title = f"{name} GS Pay Scale {year}"
    if n > 1:
        desc = (f"{n} locality pay areas cover {name}. GS-{REF_GRADE} step "
                f"{REF_STEP} runs from {money(lo['pay'])} to {money(hi['pay'])} "
                f"depending on the county. Plus what each is worth after prices.")
    else:
        desc = (f"GS pay in {name}, {year}: {rows[0]['pct']:g}% locality pay, all "
                f"15 grades and 10 steps, and what the salary is worth once local "
                f"prices are counted.")

    rel = f"states/{slug(name)}"
    return rel, shell(
        title, desc, "\n".join(B), f"https://fedpayscale.com/{rel}/", "states",
        crumbs=[("All localities", "/"), ("States", "/states/"), (name, None)], rail=rail)


def states_index(items: list, shell, esc) -> str:
    """Указатель штатов."""
    links = "".join(f'<li><a href="/{rel}/">{esc(nm)}</a></li>' for rel, nm in items)
    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li>States</li></ol>',
         '<h1>GS pay scale by state</h1>',
         '<p class="sub">Locality pay areas do not follow state lines. Most states '
         'contain more than one, and the same grade and step can differ by tens of '
         'thousands of dollars inside a single state.</p>',
         f'<div class="chips">{links}</div>',
         '<section class="q"><h2>Why a state is not a pay area</h2>',
         '<p class="q-lead">The General Schedule knows nothing about states. It is '
         'built from 58 locality pay areas, and those are defined as lists of '
         'counties.</p>',
         '<p>Some of those areas cover parts of several states at once: the '
         'Washington-Baltimore-Arlington area reaches into five, and a federal '
         'employee crossing from Maryland into Virginia inside it sees no change in '
         'pay at all. Others split a single state into pieces that are paid very '
         'differently — Texas contains six separate areas.</p>',
         '<p>So a state page is a convenience, not a unit of the pay system. What it '
         'is good for is the question people actually have: <em>if I take a federal '
         'job somewhere in this state, what am I likely to be paid, and how much '
         'does it depend on where exactly?</em></p></section>',
         '<section class="q"><h2>Where the answer changes most</h2>',
         '<p class="q-lead">In 24 states the answer depends heavily on the county. '
         'In the rest it barely depends at all.</p>',
         '<p>Eight states contain no named locality pay area whatsoever: every '
         'federal duty station in them is paid the Rest of U.S. rate, and geography '
         'inside the state makes no difference. At the other extreme, California '
         'spans five areas and nearly twenty-five thousand dollars of difference on '
         'a single grade and step.</p>',
         '<p>Each state page below says which case it is, names the areas, and adds '
         'the figure no other reference publishes: what each salary is worth once '
         'local prices are counted. In several states the best-paid area is not the '
         'one where the money goes furthest.</p></section>',

         '<section class="q"><h2>Why the spread inside a state can be large</h2>',
         '<p class="q-lead">Locality pay follows private labor markets, and those '
         'vary far more inside a state than most people expect.</p>',
         '<p>An area is set at a percentage above the nationwide base table, and '
         'that percentage is derived from what private employers in the region pay '
         'for comparable work. A state containing both a major metropolitan labor '
         'market and a stretch of countryside will therefore contain both a '
         'high-percentage area and, in the countryside, the Rest of U.S. floor. The '
         'same grade and step, forty miles apart, on two different rates.</p>',
         '<p>This is also why the boundaries look arbitrary from inside a car. They '
         'are county lists, drawn to follow economic areas rather than anything '
         'visible: a river, a ring road or a county line can be a pay boundary, and '
         'nothing on the ground marks it.</p>',
         '<p>One consequence catches people out when they transfer. A move to a '
         'higher-percentage area inside the same state reads as a raise on the '
         'offer letter, but the regions where private pay is high are usually also '
         'the regions where things cost more. How much of the increase survives that '
         'is exactly what these pages calculate, and on some moves the answer is '
         'almost none of it.</p></section>',

         '<section class="q"><h2>What these pages do not cover</h2>',
         '<p class="q-lead">The General Schedule, and only the General Schedule.</p>',
         '<p>Roughly a third of federal employees are paid from other systems: the '
         'Federal Wage System for trades and labor positions, the Senior Executive '
         'Service, Title 38 medical positions at the Department of Veterans Affairs, '
         'and several demonstration projects. Law enforcement officers at grades '
         'GS-3 through GS-10 receive higher locality rates than the ordinary table '
         'shows, and special rate tables cover occupations where recruitment is '
         'difficult — where one applies, the employee receives the higher of '
         'the special rate and the locality rate, never both.</p>',
         '<p>Every figure here is also gross pay, before deductions. State income '
         'tax in particular can matter as much as the locality difference: several '
         'states levy none at all, and a comparison that ignores it is incomplete '
         'in a way we would rather name than paper over.</p></section>']
    return shell("GS Pay Scale by State",
                 "Which locality pay areas cover each state, what each pays, and "
                 "how much the answer depends on the county.",
                 "\n".join(B), "https://fedpayscale.com/states/", "states",
                 crumbs=[("All localities", "/"), ("States", None)])


def no_area_page(codes: list, T: dict, shell, esc, money, slug) -> str:
    """Общая страница для штатов, целиком лежащих внутри Rest of U.S.

    Их восемь, и различать их нечем: одна ставка, одна история, один ответ.
    Восемь страниц с подставленным названием — это шаблонный контент, а не
    восемь ответов.
    """
    year = T["year"]
    rus = T["localities"]["RUS"]
    pay = rus["grades"][REF_GRADE][REF_STEP]["annual"]
    names = [NAMES[c] for c in sorted(codes, key=lambda c: NAMES[c])]
    listed = ", ".join(names[:-1]) + " and " + names[-1]
    chips = "".join(f"<li>{esc(n)}</li>" for n in names)

    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li><a href="/states/">States</a></li>'
         '<li>States with no named area</li></ol>',
         f'<h1>The {len(names)} states with no named locality pay area</h1>',
         f'<p class="sub">{listed} contain no designated locality pay area at all. '
         f'Every federal duty station in them is paid the Rest of U.S. rate, and '
         f'geography inside those states changes federal pay by exactly nothing.</p>',

         f'<div class="facts">'
         f'<div class="fact"><p class="fact-k">States affected</p>'
         f'<span class="kpi">{len(names)}</span>'
         f'<span class="kpi-sub">of the 50, plus no part of the District of '
         f'Columbia.</span></div>'
         f'<div class="fact"><p class="fact-k">The rate everywhere in them</p>'
         f'<span class="kpi">{money(pay)}</span>'
         f'<span class="kpi-sub">for a GS-{REF_GRADE} step {REF_STEP} in {year}, '
         f'at {rus["locality_pct"]:g}% above the nationwide base '
         f'table.</span></div></div>',

         f'<ul class="chips-plain">{chips}</ul>',
         '<div class="ad-slot ad-band">Advertisement</div>',

         '<section class="q" id="why-one-page">',
         '<h2>Why one page and not eight</h2>',
         '<p class="q-lead">Because there would be eight identical answers.</p>',
         '<p>Everywhere else on this site, a page exists because it has something '
         'of its own to say: a percentage, a spread between areas, a ranking that '
         'reverses once prices are counted. For these states there is none of that. '
         'The rate is the same, the reasoning is the same, and the only thing that '
         'would differ between eight pages is the name at the top.</p>',
         '<p>Publishing them anyway would add eight pages to the site and nothing '
         'to your knowledge. We would rather have one page that is worth '
         'reading.</p></section>',

         '<section class="q" id="what-it-means">',
         '<h2>What being outside every named area means</h2>',
         f'<p class="q-lead">Rest of U.S. is not a leftover category. It is the '
         f'rate for every federal duty station in the country outside the 57 named '
         f'areas, and it is the floor of the whole system.</p>',
         '<p>Being outside a named area is not a statement about how rural a place '
         'is. Rest of U.S. covers plenty of substantial cities: being a '
         'metropolitan area is not the test, being a <em>designated</em> locality '
         'pay area is, and that list is decided by the Federal Salary Council and '
         'the President rather than by population.</p>',
         f'<p>The practical consequence inside these {len(names)} states is worth '
         f'stating plainly. Moving across the state for a federal job changes your '
         f'commute, your rent and your neighbors. It changes your federal salary '
         f'by nothing at all. A GS-{REF_GRADE} step {REF_STEP} is paid '
         f'{money(pay)} in every county of every one of them.</p>',
         '<p>That also cuts the other way, and in your favor more often than '
         'people expect. Locality pay is set from what private employers in a '
         'region pay, not from what living there costs — so an area with a modest '
         'percentage in a place where things are cheap can leave you better off '
         'than a high percentage in an expensive one. On our '
         '<a href="/">national ranking</a>, sorted by what the salary actually '
         'buys, several low-percentage areas finish near the top.</p></section>',

         '<section class="q" id="changing">',
         '<h2>Could that change?</h2>',
         '<p class="q-lead">Yes, and when it does the effect is immediate and '
         'large.</p>',
         '<p>New locality pay areas are added occasionally. The Federal Salary '
         'Council reviews candidate areas against the criteria and recommends '
         'additions; the recommendation is not binding, and the process takes '
         'years. But a duty station moving out of Rest of U.S. into a newly named '
         'area gains the whole difference between the two percentages overnight, '
         'with no promotion and no step increase involved.</p>',
         '<p>The number of areas has grown from 48 to 54 to 58 over the years, so '
         'this is not hypothetical. It is also why this site reads the list of '
         'areas from OPM afresh on every build rather than keeping a fixed one: a '
         'hardcoded list would silently miss a new area, and the people in it are '
         'exactly the people who would most want to know.</p></section>',

         '<section class="q" id="where-next">',
         '<h2>Where to look next</h2>',
         f'<p class="q-lead">The <a href="/locality/{slug(rus["area_name"])}/">Rest '
         f'of U.S. page</a> has the full table: all 15 grades, all 10 steps, and '
         f'what each rate is worth against national average prices.</p>',
         '<p>If you are weighing a job in one of these states against one '
         'elsewhere, the <a href="/compare/">comparison pages</a> put Rest of U.S. '
         'against each of the highest-paying areas and work out how cheap a place '
         'would have to be for the lower rate to come out ahead. For a specific '
         'grade and step in a specific place, the <a href="/calculator/">'
         'calculator</a> will find the area from a ZIP code.</p>',
         '<p>And if your duty station is in one of these states but near a border, '
         'check the county rather than assuming. Named areas cross state lines '
         'freely, and a county on the edge of one of these states can belong to an '
         'area named after a city in the next state along.</p></section>']

    return shell(f"States With No Locality Pay Area, {year}",
                 f"{len(names)} states contain no named locality pay area: every "
                 f"federal duty station in them is paid the Rest of U.S. rate. "
                 f"Which states, what it pays, and what it means.",
                 "\n".join(B), "https://fedpayscale.com/states/no-locality-area/",
                 "states",
                 crumbs=[("All localities", "/"), ("States", "/states/"),
                         ("No named area", None)])
