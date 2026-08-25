"""Структурные страницы FedPay: главная, грейды, правила, служебные.

Главная и страницы грейдов — это второй вход в сайт: по данным Keyword Planner
семья «gs pay scale» держит 10–100 тыс. запросов в месяц и стабильна год к году,
тогда как «gs 13 step 5 salary» Google уже отвечает сам. Поэтому смысловой центр
здесь — таблица и сравнение, а не одно число.

Служебные страницы (about, privacy, terms, 404) — прямые требования рекламных
сетей и AdSense: без контактов, политики и внятного «кто это делает» заявку не
рассматривают. Дисклеймер о неаффилированности с OPM обязателен на каждой
странице: FTC Impersonation Rule, штраф до $53 088.

Только стандартная библиотека — D-009.
"""
from __future__ import annotations

from datetime import date


import names


def home(T: dict, R: dict, ranks: dict, L: dict, shell, esc, money, slug,
         widget: str = "", js: str = "") -> str:
    year = T["year"]
    locs = T["localities"]
    rows = ranks["rows"]
    top = rows[0]
    nom_top = max(rows, key=lambda r: r["nominal"])
    gap = top["adjusted"] - (nom_top["nominal"] / (nom_top["rpp"] / 100.0))

    B = [f'<h1>{year} GS pay scale, ranked by what the salary actually buys</h1>']
    B.append(f'<p class="sub">All {len(locs)} locality pay areas, checked cell by '
             f'cell against the official OPM tables.</p>')

    # --- 1. ответ первым, до всякой прозы: человек пришёл за своим числом
    B.append(f'<section class="q" id="find">{widget}</section>')

    # --- 2. находка
    B.append('<section class="q" id="reversal">')
    B.append('<h2>The highest-paying area is not the one where you end up '
             'richest</h2>')
    B.append(f'<p class="q-lead">At GS-12 step 5 the biggest paycheck in the General '
             f'Schedule is written in <strong>{esc(nom_top["name"])}</strong>. The '
             f'salary that goes furthest belongs to '
             f'<strong>{esc(top["name"])}</strong>, and the gap between them is '
             f'<strong>{money(gap)} a year</strong>.</p>')
    # Обе карточки теперь в ОДНИХ единицах — покупательной способности. Раньше
    # слева стояла зарплата, справа покупательная способность, одинаковым
    # кеглем: беглый читатель сравнивал 126 817 с 121 175 и делал вывод,
    # обратный тезису секции.
    nom_buys = nom_top["nominal"] / (nom_top["rpp"] / 100.0)
    B.append(f'<div class="facts">'
             f'<div class="fact"><p class="fact-k">Biggest paycheck, and what it buys</p>'
             f'<span class="kpi">{money(nom_buys)}</span>'
             f'<span class="kpi-sub">{esc(nom_top["name"])} pays '
             f'{money(nom_top["nominal"])}, the most in the country. Local prices '
             f'stand at {nom_top["rpp"]:.1f} against a national average of 100, '
             f'which is what the salary comes down to.</span></div>'
             f'<div class="fact"><p class="fact-k">Goes furthest, and what it pays</p>'
             f'<span class="kpi">{money(top["adjusted"])}</span>'
             f'<span class="kpi-sub">{esc(top["name"])} pays '
             f'{money(top["nominal"])} \u2014 '
             f'{money(nom_top["nominal"] - top["nominal"])} less on paper, and '
             f'{money(gap)} more once prices are counted.</span></div></div>')
    B.append('<p>Locality pay is calculated from what <em>private employers in the '
             'same region pay for comparable work</em>. It is not a cost-of-living '
             'adjustment, and OPM says so plainly. The two are related, but not the '
             'same thing, and the gap between them is large enough to turn the '
             'ranking upside down.</p>')
    B.append('<p>That is what the table below measures, and it is the one thing no '
             'other reference site publishes. Every other column comes straight from '
             'the official table; the last two are ours.</p>')
    B.append('</section>')

    B.append('<div class="ad-slot ad-band">Advertisement</div>')

    # --- 3. таблица всех зон
    B.append('<section class="q" id="table">')
    B.append(f'<h2>All {len(locs)} locality pay areas, ranked by what the salary '
             f'buys</h2>')
    B.append(f'<p class="q-lead">Dollar figures are a <strong>GS-12, step 5</strong> '
             f'\u2014 the middle of the schedule, used here so that every area is '
             f'compared on the same cell. Change the grade above and the table '
             f'follows. <strong>Click any column heading</strong> to sort by '
             f'it.</p>')
    B.append(_home_table(T, R, ranks, L, esc, money, slug))
    B.append('</section>')

    B.append('<div class="ad-slot ad-band">Advertisement</div>')

    # --- 4. грейды: ссылка с суммой внутри, а не «Browse by grade»
    B.append('<section class="q" id="grades">')
    B.append('<h2>Or start from a grade</h2>')
    B.append('<p class="q-lead">Each grade page shows that grade in every area at '
             'once \u2014 the comparison people actually need when weighing a '
             'move. Figures below are base rates, before any locality '
             'adjustment.</p>')
    base = T["base"]["grades"]
    chips = "".join(
        f'<a href="/gs-{g}/"><b>GS-{g}</b>'
        f'<span>{money(base[str(g)]["1"]["annual"])}</span></a>'
        for g in sorted((int(k) for k in base), key=int))
    B.append(f'<div class="chips-pay">{chips}</div>')
    B.append('<p>There are also <a href="/compare/">side-by-side comparisons</a> of '
             'the highest-paying areas against each other and against Rest of U.S., '
             'a page for <a href="/promotion/">every promotion</a> from one grade to '
             'the next, and a <a href="/calculator/">full calculator</a> that will '
             'find your area from a ZIP code.</p>')
    B.append('</section>')

    # --- 5. откуда числа
    B.append('<section class="q" id="method">')
    B.append('<h2>Where these numbers come from</h2>')
    B.append(f'<p class="q-lead">Every rate on this site was recomputed from the '
             f'published base table and the locality percentage, then checked against '
             f'the official OPM figure. All 8,700 cells match to the dollar.</p>')
    B.append(f'<p>Salary tables and locality percentages: U.S. Office of Personnel '
             f'Management, {year} General Schedule salary tables. Locality pay area '
             f'definitions: OPM, {year}. Price levels: U.S. Bureau of Economic '
             f'Analysis Regional Price Parities, {R["bea_year"]}, shown to one decimal '
             f'place though computed from the published three. ZIP-code-to-county '
             f'relationships: U.S. Census Bureau 2020 ZCTA file. All are works of the '
             f'United States government and in the public domain.</p>')
    B.append('<p>The order of operations matters and is fixed by law: the percentage '
             'is applied to the base rate, the result is rounded, and only then is it '
             'checked against the statutory ceiling. Doing those steps in a different '
             'order changes the answer at the top of the schedule, which is one '
             'reason published figures sometimes disagree between reference '
             'sites. <a href="/how-locality-pay-works/">How locality pay works</a> '
             'sets out the rules in full.</p>')
    B.append('</section>')

    return shell(f"{year} GS Pay Scale by Locality \u2014 all {len(locs)} areas",
                 f"Complete {year} General Schedule pay tables for all {len(locs)} "
                 f"locality pay areas, ranked by what each salary buys after local "
                 f"prices, not just by the headline number.",
                 "\n".join(B), "https://fedpayscale.com/", "home",
                 js=js, wide=True)


def _home_table(T, R, ranks, L, esc, money, slug) -> str:
    """Таблица всех зон. Сортируется по любому столбцу."""
    locs = T["localities"]
    rows = ranks["rows"]
    body = []
    for i, r in enumerate(rows, 1):
        code = r["code"]
        pct = locs[code]["locality_pct"]
        nrank = ranks["nominal"][code]
        delta = nrank - i
        move = (f"+{delta}" if delta > 0
                else (f"\u2212{-delta}" if delta < 0 else "\u2014"))
        cls = "up" if delta > 0 else ("down" if delta < 0 else "flat")
        body.append(
            f'<tr data-code="{code}">'
            f'<td class="rank" data-v="{i}">{i}</td>'
            f'<th scope="row" data-v="{esc(r["name"])}">'
            f'<a href="/locality/{slug(r["name"])}/">'
            f'{esc(names.short_name(r["name"]))}</a>'
            f'<span class="full">{esc(r["name"])}</span></th>'
            f'<td class="num" data-v="{pct}">{pct:g}%</td>'
            f'<td class="num" data-v="{r["nominal"]}">{money(r["nominal"])}</td>'
            f'<td class="num" data-v="{r["rpp"]}">{r["rpp"]:.1f}</td>'
            f'<td class="num" data-v="{int(r["adjusted"])}">{money(r["adjusted"])}</td>'
            f'<td class="num {cls}" data-v="{delta}">{move}</td></tr>')

    extra = []
    for code in (c for c in locs if c not in ranks["adjusted"]):
        loc = locs[code]
        cell = loc["grades"]["12"]["5"]
        extra.append(
            f'<tr data-code="{code}">'
            f'<td class="rank" data-v="99">\u2014</td>'
            f'<th scope="row" data-v="{esc(loc["area_name"])}">'
            f'<a href="/locality/{slug(loc["area_name"])}/">'
            f'{esc(names.short_name(loc["area_name"]))}</a>'
            f'<span class="full">{esc(loc["area_name"])}</span></th>'
            f'<td class="num" data-v="{loc["locality_pct"]}">'
            f'{loc["locality_pct"]:g}%</td>'
            f'<td class="num" data-v="{cell["annual"]}">{money(cell["annual"])}</td>'
            f'<td class="num" data-v="">\u2014</td>'
            f'<td class="num" data-v="">\u2014</td>'
            f'<td class="num flat" data-v="">\u2014</td></tr>')

    heads = [("PP rank", "rank", False), ("Locality", "", False),
             ("Locality pay", "num", True), ("On paper", "num", True),
             ("Prices", "num", True), ("What it buys", "num", True),
             ("Rank shift", "num", True)]
    th = "".join(
        f'<th class="{c}" scope="col" data-sort="{n}" aria-sort="none"'
        f'{" data-desc" if d else ""}>'
        f'<button type="button">{lbl}</button></th>'
        for n, (lbl, c, d) in enumerate(heads))
    return (f'<div class="scroll" tabindex="0" role="region" '
            f'aria-label="All locality pay areas ranked by purchasing power">'
            f'<table data-sortable data-home>'
            f'<thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body)}{"".join(extra)}</tbody></table></div>'
            f'<p class="tlegend"><span>Sorted by purchasing power. The price column '
            f'is the BEA Regional Price Parity for {R["bea_year"]}, where 100 is the '
            f'national average \u2014 below 100 is cheaper.</span>'
            f'<span>Rank shift: how many places the area moves when you stop ranking '
            f'by the paycheck and start ranking by what it buys. The first '
            f'column is that same purchasing-power rank, so it stays with its '
            f'area when you sort by something else.</span></p>')


def grade_page(g: str, T: dict, R: dict, ranks: dict, shell, esc, money, slug,
               rail: str = "", widget: str = "", js: str = "") -> str:
    year = T["year"]
    cap = T["ex_iv_cap"]
    base = T["base"]["grades"][g]
    locs = T["localities"]

    # Строим по ВСЕМ зонам, а не только по тем, у которых есть индекс цен.
    # Раньше брались ranks["rows"] (55 зон), и «Rest of U.S.» — самая
    # многочисленная зона федеральной службы — не попадала на страницу вовсе,
    # а заявленный разброс зарплат был занижен, потому что нижняя граница
    # системы как раз в ней.
    priced = {r["code"]: r for r in ranks["rows"]}
    rows = []
    for code, loc in locs.items():
        cell = loc["grades"][g]["5"]
        pr = priced.get(code)
        rows.append({"code": code, "name": loc["area_name"],
                     "pay": cell["annual"], "capped": cell["capped"],
                     "rpp": pr["rpp"] if pr else None,
                     "adj": cell["annual"] / (pr["rpp"] / 100.0) if pr else None})
    rows.sort(key=lambda x: -x["pay"])

    n_capped = sum(1 for x in rows if x["capped"])
    lo, hi = rows[-1], rows[0]
    spread = hi["pay"] - lo["pay"]

    B = [f'<ol class="crumbs"><li><a href="/">All localities</a></li>'
         f'<li><a href="/grades/">All grades</a></li>'
         f'<li>GS-{g}</li></ol>']
    B.append(f'<h1>GS-{g} salary in {year}, by locality</h1>')
    B.append(f'<p class="sub">What a GS-{g} earns in each of the {len(rows)} locality '
             f'pay areas, and what that salary is worth once local prices are counted. '
             f'The same grade and step ranges from {money(lo["pay"])} to '
             f'{money(hi["pay"])} depending only on where the desk is.</p>')

    B.append('<div class="answer">')
    B.append(f'<span class="what">GS-{g} step 5, base rate before locality</span>')
    B.append(f'<span class="big">{money(base["5"]["annual"])}</span>')
    B.append(f'<p>Nobody is actually paid this. It is the nationwide starting point, and '
             f'every duty station adds a locality percentage on top — from '
             f'{min(l["locality_pct"] for l in locs.values()):g}% to '
             f'{max(l["locality_pct"] for l in locs.values()):g}%. The spread that '
             f'creates is <strong>{money(spread)}</strong> for identical work.</p>')
    if n_capped:
        B.append(f'<p>In {n_capped} localities a GS-{g} step 5 has already hit the '
                 f'{money(cap)} statutory ceiling, so the printed figure is lower than '
                 f'the formula gives and further step increases add nothing.</p>')
    B.append('</div>')

    body = []
    for i, r in enumerate(rows, 1):
        mark = ' class="capped num"' if r["capped"] else ' class="num"'
        # Считаем до f-строки: вложенные одинаковые кавычки внутри f-строки
        # разрешены только с Python 3.12, а сборочная машина может быть старее.
        rpp_txt = "%.1f" % r["rpp"] if r["rpp"] else "—"
        adj_txt = money(r["adj"]) if r["adj"] else "—"
        body.append(
            f'<tr><td class="rank">{i}</td>'
            f'<th scope="row"><a href="/locality/{slug(r["name"])}/">{esc(r["name"])}</a></th>'
            f'<td{mark}>{money(r["pay"])}</td>'
            f'<td class="num">{rpp_txt}</td>'
            f'<td class="num">{adj_txt}</td></tr>')

    best_adj = max((x for x in rows if x["adj"]), key=lambda x: x["adj"])
    B.append(f"""<figure class="ex">
<div class="ex-kicker">Exhibit 1</div>
<div class="ex-title">GS-{g} step 5 in every locality</div>
<p class="ex-note">Sorted by the number on the paycheck. The last column divides that
number by the local price level, so it is comparable in what it buys. Cells marked ▲
have been cut to the {money(cap)} statutory ceiling.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Scrollable table"><table>
<thead><tr><th class="rank">#</th><th>Locality</th><th class="num">Salary</th>
<th class="num">Prices</th><th class="num">What it buys</th></tr></thead>
<tbody>{''.join(body)}</tbody>
</table></div>
<figcaption>The best-paid GS-{g} on paper is in {esc(hi['name'])} at {money(hi['pay'])}.
The best-off GS-{g} in practice is in {esc(best_adj['name'])}, where {money(best_adj['pay'])}
buys what {money(best_adj['adj'])} buys at national average prices. Rest of U.S. is a
residual drawn from every state at once and has no price index of its own, so its last
two columns are left empty rather than filled with a guess. Sources: OPM {year} salary
tables; BEA Regional Price Parities {R['bea_year']}.</figcaption>
</figure>""")

    B.append(f'<h2>All ten steps of GS-{g}</h2>')
    B.append(f'<p>These are base rates before any locality adjustment. Multiply by your '
             f'area\'s percentage — or open your locality page, where the arithmetic is '
             f'already done.</p>')
    cells = "".join(f'<td class="num">{money(base[str(s)]["annual"])}</td>'
                    for s in range(1, 11))
    heads = "".join(f'<th class="num">{s}</th>' for s in range(1, 11))
    B.append(f'<div class="scroll" tabindex="0" role="region" aria-label="Scrollable table"><table><thead><tr><th>Step</th>{heads}</tr></thead>'
             f'<tbody><tr><th scope="row">Base</th>{cells}</tr></tbody></table></div>')

    # Расписание ступеней считается арифметически и у каждого грейда своё
    # в деньгах — это и полезно, и уникально: у конкурентов расчёта нет,
    # только текстовое описание правила.
    B.append(f'<h2>How long to the top of GS-{g}</h2>')
    waits = [(2, 1), (3, 1), (4, 1), (5, 2), (6, 2), (7, 2), (8, 3), (9, 3), (10, 3)]
    cum, rows2 = 0, []
    for step, yrs in waits:
        cum += yrs
        gain = base[str(step)]["annual"] - base[str(step - 1)]["annual"]
        rows2.append(f'<tr><th scope="row">Step {step}</th>'
                     f'<td class="num">{yrs}</td><td class="num">{cum}</td>'
                     f'<td class="num">+{money(gain)}</td></tr>')
    total_gain = base["10"]["annual"] - base["1"]["annual"]
    B.append(f'<p>Step increases arrive on a fixed schedule as long as performance is '
             f'acceptable: one year each for steps 2 to 4, two years each for steps 5 to '
             f'7, and three years each for steps 8 to 10. Starting at step 1, reaching '
             f'the top of GS-{g} takes <strong>{cum} years</strong> and adds '
             f'{money(total_gain)} to the base rate before any locality payment.</p>')
    B.append(f'<div class="scroll" tabindex="0" role="region" aria-label="Scrollable table"><table><thead><tr><th>Reaching</th>'
             f'<th class="num">Wait (years)</th><th class="num">Years from start</th>'
             f'<th class="num">Base increase</th></tr></thead>'
             f'<tbody>{"".join(rows2)}</tbody></table></div>')
    B.append('<p>A promotion to a higher grade restarts that clock, which is why a '
             'promotion arriving a month before a step increase can be worth less in '
             'the first year than it appears. The waiting period also pauses during '
             'periods of non-pay status beyond a threshold, so long unpaid absences '
             'push the next increase further out.</p>')

    # Инструмент: грейд уже выбран, меняется зона — ровно то, ради чего сюда
    # приходят («сколько GS-13 платят там-то»).
    if widget:
        B.append(widget)

    B.append('<h2>Moving between grades</h2>')
    gi = int(g)
    nxt = str(gi + 1) if str(gi + 1) in T["base"]["grades"] else None
    prv = str(gi - 1) if str(gi - 1) in T["base"]["grades"] else None
    bits = []
    if prv:
        d = base["5"]["annual"] - T["base"]["grades"][prv]["5"]["annual"]
        bits.append(f'a promotion from GS-{prv} is worth about {money(d)} at step 5')
    if nxt:
        d = T["base"]["grades"][nxt]["5"]["annual"] - base["5"]["annual"]
        bits.append(f'the step up to GS-{nxt} adds about {money(d)}')
    if bits:
        B.append(f'<p>On base rates, {" and ".join(bits)}. A grade promotion also resets '
                 f'the waiting clock for your next step increase, which is why the '
                 f'timing of a promotion can matter as much as its size.</p>')
    links = "".join(f'<a href="/gs-{x}/">GS-{x}</a>'
                    for x in sorted(T["base"]["grades"], key=int) if x != g)
    B.append(f'<div class="chips">{links}</div>')

    return shell(f"GS-{g} Pay Scale {year} — salary in every locality | FedPay",
                 f"What a GS-{g} earns in {year} in each of the {len(rows)} locality pay "
                 f"areas, from {money(lo['pay'])} to {money(hi['pay'])}, with each "
                 f"salary adjusted for local prices.",
                 "\n".join(B), f"https://fedpayscale.com/gs-{g}/", "grades",
                 crumbs=[("All localities", "/"),
                         ("All grades", "/grades/"),
                         (f"GS-{g}", None)], js=js, rail=rail)


def how_it_works(T: dict, shell, money) -> str:
    year, cap = T["year"], T["ex_iv_cap"]
    B = ['<h1>How locality pay actually works</h1>']
    B.append('<p class="sub">The rules behind the number, including the three that '
             'surprise people most: locality is not cost of living, steps are not '
             'evenly spaced, and raises stop counting once you hit the ceiling.</p>')

    B.append('<h2>It is a labor-market adjustment, not a cost-of-living one</h2>')
    B.append('<p>Locality pay exists because of the Federal Employees Pay Comparability '
             'Act of 1990, which set out to close the gap between federal and '
             'non-federal salaries in the same labor market. The comparison is against '
             '<em>what other employers in that region pay for similar work</em>, '
             'measured by the Bureau of Labor Statistics. It is not a measure of what '
             'housing, food or childcare cost there.</p>')
    B.append('<p>The practical consequence runs through this whole site: an area can pay '
             'a large adjustment and still leave you with less, because a strong '
             'private labor market and expensive living usually travel together but '
             'not in the same proportion.</p>')

    B.append('<h2>Your duty station decides, not your address</h2>')
    B.append('<p>Locality follows the official duty station — the place you are assigned '
             'to report to. Living in a cheaper county nearby does not reduce your pay, '
             'and living in an expensive one does not raise it. Remote and telework '
             'arrangements are the common source of confusion here, because the rules '
             'depend on how the position is formally documented rather than on where '
             'you happen to open a laptop.</p>')

    B.append('<h2>Steps, and the waiting periods between them</h2>')
    B.append('<p>Within a grade, step increases come on a fixed schedule as long as '
             'performance is acceptable: one year each for steps 2 through 4, two years '
             'each for steps 5 through 7, and three years each for steps 8 through 10. '
             'Reaching step 10 from step 1 therefore takes eighteen years without a '
             'promotion.</p>')
    B.append('<p>A promotion to a higher grade restarts that clock. That is worth '
             'knowing when a promotion lands shortly before a step increase would have.</p>')

    B.append('<h2>The ceiling</h2>')
    B.append(f'<p>By law no General Schedule rate may exceed Level IV of the Executive '
             f'Schedule, which is {money(cap)} in {year}. Where the formula would '
             f'produce more, the payable rate is cut back to that figure. In the '
             f'highest-paying localities this happens well before the top of the '
             f'schedule, so several consecutive step increases can arrive with no change '
             f'in pay at all.</p>')

    B.append('<h2>What this site does not cover</h2>')
    B.append('<p>Roughly a third of federal employees are not on the General Schedule. '
             'Wage Grade trades, Senior Executive Service, and agency-specific systems '
             'such as FAA\'s FV bands, TSA, VA Title 38 medical positions, and various '
             'demonstration projects all use different tables. Special rate schedules '
             'can also override the General Schedule for particular occupations and '
             'locations — where one applies, the employee receives the higher of the '
             'special rate and the locality rate, never the two added together.</p>')

    B.append('<h2>What happens every January</h2>')
    B.append('<p>The pay adjustment for the coming year is normally set in late December '
             'by executive order, after which OPM publishes the new tables \u2014 one '
             'nationwide base table and one for each locality pay area. The adjustment '
             'has two parts that are frequently confused: an across-the-board increase '
             'applied to the base schedule, and a separate locality component that '
             'differs by area. A headline figure of, say, two percent is the average of '
             'the two, and almost nobody receives exactly the average.</p>')
    B.append('<p>The President may also submit an alternative pay plan, which sets the '
             'adjustment aside and substitutes a different figure \u2014 including zero. '
             'This has happened repeatedly, and it is the mechanism by which locality '
             'percentages have been frozen while the base schedule still moved. When '
             'that happens the locality percentages carry over unchanged from the '
             'previous year, so an area\u2019s relative position stays put even as the '
             'dollar figures rise.</p>')
    B.append('<p>New locality pay areas are added occasionally, and the effect on the '
             'people in them is large: a duty station moving out of Rest of U.S. into a '
             'named metropolitan area gains the difference between the two percentages '
             'overnight. The Federal Salary Council reviews candidate areas and '
             'recommends additions, but the process takes years and the recommendation '
             'is not binding.</p>')

    B.append('<h2>Reading a pay table correctly</h2>')
    B.append('<p>Two mistakes account for most of the confusion we see. The first is '
             'adding the locality percentage to a figure that already includes it \u2014 '
             'the tables OPM publishes per locality are final rates, not base rates '
             'awaiting an adjustment. The second is assuming the ten steps are evenly '
             'spaced. They are not, particularly at the bottom of the schedule, and '
             'extrapolating from the gap between step 1 and step 2 produces numbers that '
             'are wrong by hundreds of dollars.</p>')
    B.append('<p>There is also a rounding question that changes results at the top of '
             'the schedule. The locality percentage is applied to the base rate and the '
             'result rounded, and only then is the statutory ceiling applied. Doing it '
             'in the other order gives different figures for capped cells, which is one '
             'reason published numbers occasionally disagree between sites. Every figure '
             'on this site was recomputed in the correct order and checked against the '
             'official table cell by cell.</p>')

    return shell("How Locality Pay Works — the rules behind the GS number",
                 "Locality pay is a labor-market adjustment, not a cost-of-living "
                 "one. How duty station, waiting periods and the statutory ceiling "
                 "set a federal salary.",
                 "\n".join(B), "https://fedpayscale.com/how-locality-pay-works/", "how")


def about(shell) -> str:
    B = ['<h1>About FedPay</h1>']
    B.append('<p class="sub">Who builds this, how the numbers get here, and what to do '
             'if one of them is wrong.</p>')
    B.append('<h2>What this is</h2>')
    B.append('<p>FedPay publishes the federal General Schedule pay tables with the parts '
             'that the published tables leave out: what each salary is worth after local '
             'prices, where the statutory ceiling quietly stops raises, and which '
             'counties belong to which locality.</p>')
    B.append('<h2>Where the numbers come from</h2>')
    B.append('<p>Pay figures come from the Office of Personnel Management\'s published '
             'salary tables. Rather than copying them, the build recomputes every rate '
             'from the nationwide base table and the locality percentage, applies the '
             'statutory ceiling, and then compares its own result against the published '
             'figure — all 8,700 of them. If a single cell disagrees by a dollar, the '
             'site does not publish.</p>')
    B.append('<p>Price levels are Regional Price Parities from the Bureau of Economic '
             'Analysis. They lag the pay tables by about two years, and metropolitan '
             'boundaries do not line up exactly with locality boundaries, so the nearest '
             'metropolitan area is used as a proxy and labelled as such.</p>')
    B.append('<h2>Corrections</h2>')
    B.append('<p>If a figure here is wrong, say which page and what you expected. '
             'Corrections are made against the source data, not against the page.</p>')
    B.append('<h2>What this is not</h2>')
    B.append('<p>This is an independent reference, not a government service and not '
             'financial or employment advice. For an official figure, go to OPM. For '
             'your own pay, go to your HR office — special rates, agency systems and '
             'individual circumstances all change the answer.</p>')
    return shell("About FedPay — how the numbers are built and checked",
                 "FedPay recomputes every federal pay rate from the OPM source tables "
                 "and verifies all 8,700 of them before publishing.",
                 "\n".join(B), "https://fedpayscale.com/about/", "about")


def privacy(shell) -> str:
    B = ['<h1>Privacy</h1>',
         '<p class="sub">What this site collects, and what it does not.</p>',
         '<h2>What we collect</h2>',
         '<p>This site is a set of static pages. It has no accounts, no logins, no '
         'comment system and no newsletter, and it never asks you for personal '
         'information. The hosting provider keeps standard server request logs for '
         'security and to see which pages are used.</p>',
         '<h2>Analytics</h2>',
         '<p>This site runs <strong>no analytics of any kind</strong>. There is '
         'no Google Analytics, no tag manager, no pixel and no third-party '
         'script of any sort. You can check that yourself: open the network tab '
         'of your browser and every request a page makes goes to this domain '
         'and nowhere else.</p>',
         '<p>The only record of your visit is the standard request log kept by '
         'the hosting provider for security and capacity. If analytics is ever '
         'added, this page will be rewritten <em>before</em> the code goes live, '
         'not after. A privacy notice describes what your browser actually '
         'loads, not what the publisher intends to do later.</p>',
         '<h2>Advertising</h2>',
         '<p>This site does not yet carry advertising and sets no advertising cookies. '
         'When advertising is added, partners may set cookies or use similar technology. '
         'Visitors in the European Economic Area and the United Kingdom will be shown a '
         'consent choice before any non-essential cookie is set. This page will be '
         'updated on the day that happens.</p>',
         '<h2 id="us-state-rights">US state privacy rights</h2>',
         '<p>Residents of states with comprehensive privacy laws have rights to access, '
         'correct and delete personal information, and to opt out of its sale or of '
         'targeted advertising. This site does not sell or share personal information '
         'and runs no advertising today.</p>']
    return shell("Privacy — FedPay", "What FedPay collects and what it does not.",
                 "\n".join(B), "https://fedpayscale.com/privacy/")


def terms(shell) -> str:
    B = ['<h1>Terms</h1>',
         f'<p class="sub">Last updated {date.today().isoformat()}.</p>',
         '<h2>What this site is</h2>',
         '<p>An information reference compiled from public United States government '
         'records. It is published for general information and is not advice — not '
         'financial, not legal, not employment advice. Decisions about accepting a '
         'position, relocating, or negotiating pay are yours.</p>',
         '<h2>Accuracy</h2>',
         '<p>Figures are computed automatically from OPM and BEA data and verified '
         'against the source before publication. Even so, records may be incomplete or '
         'superseded, special rate schedules and agency-specific systems override the '
         'General Schedule in ways this site does not always capture, and our processing '
         'may contain errors of its own. For an authoritative figure, consult OPM or '
         'your servicing HR office.</p>',
         '<h2>Reuse</h2>',
         '<p>The underlying OPM and BEA data are works of the United States government '
         'and in the public domain. Text and derived figures generated by this site are '
         'licensed CC BY 4.0: reuse them with attribution and a link.</p>',
         '<h2>No government affiliation</h2>',
         '<p>FedPay is not affiliated with, endorsed by, or connected to the U.S. Office '
         'of Personnel Management or any other government agency, and does not claim to '
         'be an official source.</p>']
    return shell("Terms — FedPay", "Terms of use for FedPay.",
                 "\n".join(B), "https://fedpayscale.com/terms/")


def not_found(shell) -> str:
    B = ['<h1>Page not found</h1>',
         '<p class="sub">That address does not match anything on this site.</p>',
         '<p>If you were looking for a locality or a grade, start from the '
         '<a href="/">list of all localities</a> — every page on this site is linked '
         'from there.</p>']
    # Пустой canonical хуже отсутствующего: он валиден и указывает на текущий
    # адрес, то есть 404 само-канонизируется на любой запрошенный мусор.
    return shell("Page not found — FedPay",
                 "That address does not match anything on this site.",
                 "\n".join(B), "", noindex=True)


def sitemap(urls: list[str], domain: str, lastmod: str = "") -> str:
    """Дата — по отпечатку ДАННЫХ, а не по времени сборки.

    Ежемесячный прогон по расписанию ничего не меняет; сообщать поисковику,
    что обновились все 104 страницы, — то же враньё, что и «обновлено вчера»
    в подвале, только адресованное машине."""
    stamp = lastmod or date.today().isoformat()
    body = "".join(f"<url><loc>{domain}{u}</loc><lastmod>{stamp}</lastmod></url>"
                   for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f'{body}</urlset>')


def grades_index(T: dict, ranks: dict, shell, esc, money,
                 rail: str = "") -> str:
    """Хаб по грейдам. Нужен и по смыслу, и потому что на него ведёт меню:
    гейт битых ссылок поймал отсутствие этой страницы на 78 страницах сразу."""
    year, cap = T["year"], T["ex_iv_cap"]
    base = T["base"]["grades"]
    locs = T["localities"]
    lo_pct = min(l["locality_pct"] for l in locs.values())
    hi_pct = max(l["locality_pct"] for l in locs.values())

    rows = []
    for g in sorted(base, key=int):
        b5 = base[g]["5"]["annual"]
        pays = [locs[c]["grades"][g]["5"]["annual"] for c in locs]
        capped = sum(1 for c in locs for s in locs[c]["grades"][g].values() if s["capped"])
        rows.append(
            f'<tr><th scope="row"><a href="/gs-{g}/">GS-{g}</a></th>'
            f'<td class="num">{money(base[g]["1"]["annual"])}</td>'
            f'<td class="num">{money(b5)}</td>'
            f'<td class="num">{money(base[g]["10"]["annual"])}</td>'
            f'<td class="num">{money(min(pays))}</td>'
            f'<td class="num">{money(max(pays))}</td>'
            f'<td class="num">{capped or "—"}</td></tr>')

    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li>All grades</li></ol>',
         '<h1>Every General Schedule grade in 2026</h1>']
    B.append(f'<p class="sub">Fifteen grades, ten steps each, and a locality adjustment '
             f'between {lo_pct:g}% and {hi_pct:g}% on top. This page shows the base '
             f'range for each grade and how far apart the same job can be paid depending '
             f'only on the duty station.</p>')
    B.append(f"""<figure class="ex">
<div class="ex-kicker">Exhibit 1</div>
<div class="ex-title">Base rates and the spread locality creates</div>
<p class="ex-note">The first three columns are nationwide base rates before any locality
payment — nobody is paid these. The next two show the lowest and highest actual
step-5 salary across all {len(locs)} localities. The last column counts how many cells in
that grade are pinned to the {money(cap)} statutory ceiling somewhere in the country.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Scrollable table"><table>
<thead><tr><th>Grade</th><th class="num">Base step 1</th><th class="num">Base step 5</th>
<th class="num">Base step 10</th><th class="num">Lowest actual</th>
<th class="num">Highest actual</th><th class="num">At ceiling</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></div>
<figcaption>Source: OPM {year} General Schedule salary tables, all 8,700 cells
independently recomputed and matched to the published figures.</figcaption>
</figure>""")
    B.append('<h2>Which grade is which</h2>')
    B.append('<p>Grades roughly track responsibility and entry requirements rather than '
             'job title. GS-5 to GS-7 is where most degree-holding entrants start, GS-9 '
             'to GS-12 covers most working-level professional roles, GS-13 to GS-15 '
             'covers senior specialists and supervisors, and above that sits the Senior '
             'Executive Service on an entirely different table.</p>')
    B.append('<p>Promotion between grades resets the waiting period for the next step '
             'increase, so a promotion that lands just before a step was due can be '
             'worth less in the first year than it looks.</p>')

    B.append('<h2>How a job lands on a grade</h2>')
    B.append('<p>Grades are assigned to the position, not to the person. A classifier '
             'evaluates the duties against published standards \u2014 how much '
             'independent judgement the work requires, how broad its impact is, how '
             'much supervision it receives \u2014 and the grade follows from that. Two '
             'people doing visibly similar work in different agencies can sit on '
             'different grades because their position descriptions differ, which is a '
             'common source of frustration and a legitimate thing to raise with HR.</p>')
    B.append('<p>Entry grades are governed by qualification standards rather than by '
             'negotiation. A bachelor\u2019s degree typically qualifies for GS-5, a '
             'degree with superior academic achievement or one year of graduate study '
             'for GS-7, a master\u2019s for GS-9, and a doctorate for GS-11. Experience '
             'substitutes for education at a defined rate, and one year at the '
             'next-lower grade is the usual requirement for promotion.</p>')

    B.append('<h2>Career ladders</h2>')
    B.append('<p>Many federal positions are advertised as a ladder \u2014 GS-7/9/11, '
             'say \u2014 meaning the successful candidate enters at the lowest grade '
             'and is promoted non-competitively to the next as soon as the time-in-grade '
             'requirement is met and performance is acceptable. The advertised '
             '\u201cfull performance level\u201d is the top of that ladder, and it is '
             'the number worth paying attention to when comparing offers: the entry '
             'grade is temporary, the full performance level is where the job settles.</p>')
    B.append('<p>Above the full performance level, further promotion generally requires '
             'competing for a different position. That is why the jump from GS-12 to '
             'GS-13 is such a visible barrier in federal careers \u2014 for many '
             'occupational series GS-12 is where the ladder ends.</p>')

    B.append('<h2>What the base table is not</h2>')
    B.append('<p>The rates on this page are base rates. Nobody receives them: every duty '
             'station in the United States falls inside a locality pay area, and the '
             'lowest of those still adds a double-digit percentage. The base table '
             'exists as the arithmetic starting point and as the reference for a handful '
             'of pay rules, not as anyone\u2019s salary.</p>')
    B.append('<p>Roughly a third of federal employees are not paid from this table at '
             'all. Wage Grade trades positions use locality wage schedules built from '
             'local prevailing rates; the Senior Executive Service, the Federal Aviation '
             'Administration, the Transportation Security Administration, Department of '
             'Veterans Affairs Title 38 medical positions and several demonstration '
             'projects all run their own systems. Special rate schedules add another '
             'layer: where one covers an occupation and location, the employee receives '
             'the higher of the special rate and the locality rate \u2014 never both '
             'added together.</p>')
    return shell(f"GS Pay Scale {year} — all 15 grades and what they pay | FedPay",
                 f"All fifteen General Schedule grades for {year}: base rates, the "
                 f"lowest and highest actual salary across every locality, and where "
                 f"the statutory ceiling bites.",
                 "\n".join(B), "https://fedpayscale.com/grades/", "grades",
                 crumbs=[("All localities", "/"),
                         ("All grades", None)], rail=rail)


def calculator(T: dict, R: dict, shell, esc, money, widget, js: str,
               rail: str = "") -> str:
    """Инструмент и текст на одной странице."""
    year = T["year"]
    cap = T["ex_iv_cap"]
    locs = T["localities"]
    lo = min(l["locality_pct"] for l in locs.values())
    hi = max(l["locality_pct"] for l in locs.values())
    base5 = T["base"]["grades"]["12"]["5"]["annual"]

    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li>Pay calculator</li></ol>']
    B.append(f'<h1>GS pay calculator, {year}</h1>')
    B.append(f'<p class="sub">Enter a ZIP code, a grade and a step. The answer is '
             f'the annual, biweekly, hourly and overtime rate for that duty station, '
             f'plus the one thing other calculators leave out: what the salary is '
             f'worth once local prices are counted.</p>')

    B.append(widget)

    B.append('<h2>What this works out</h2>')
    B.append(f'<p>Every General Schedule salary is one base rate multiplied by one '
             f'locality percentage. The base table is the same everywhere in the '
             f'country; the percentage depends only on the duty station, and in '
             f'{year} it runs from {lo:g}% to {hi:g}%. A GS-12 step 5 starts from a '
             f'base of {money(base5)} and finishes somewhere between '
             f'{money(round(base5 * (1 + lo / 100)))} and '
             f'{money(round(base5 * (1 + hi / 100)))} depending on nothing but '
             f'geography.</p>')
    B.append(f'<p>The order matters and is fixed by law. The percentage is applied '
             f'to the base rate, the result is rounded to the nearest dollar, and '
             f'only then is it checked against the statutory ceiling of '
             f'{money(cap)} \u2014 Level IV of the Executive Schedule. Doing those '
             f'steps in a different order changes the answer at the top of the '
             f'schedule, which is one reason published figures sometimes disagree '
             f'between reference sites. Every rate this calculator produces was '
             f'checked against the published OPM table cell by cell: all 8,700 of '
             f'them match to the dollar.</p>')

    B.append('<h2>What it does not include</h2>')
    B.append('<p>This is <strong>gross pay</strong> \u2014 what the job pays before '
             'anything is taken out. It is not take-home pay. Federal deductions '
             'depend on choices and circumstances this page knows nothing about: '
             'your FERS contribution tier, which depends on when you were first '
             'hired; how much you put into the Thrift Savings Plan and whether it is '
             'traditional or Roth; which FEHB plan you carry and at what enrollment '
             'level; FEGLI; your filing status; and the income tax of the state you '
             'live in, which is not always the state you work in.</p>')
    B.append('<p>We would rather show one number that is exactly right than a '
             'take-home estimate built on half a dozen assumptions we invented for '
             'you. Every figure here comes from a published federal table.</p>')

    B.append('<h2>Why the ZIP code sometimes fails</h2>')
    B.append('<p>Locality is decided by your <strong>duty station</strong> \u2014 '
             'the place you physically report to \u2014 and duty stations are '
             'assigned to counties, not to ZIP codes. To answer by ZIP we join the '
             'Census Bureau\u2019s ZIP-code-to-county file to the OPM list of '
             'counties in each locality pay area. That works for the great majority '
             'of ZIPs and fails in three situations worth knowing about.</p>')
    B.append('<p>Some ZIP codes serve post office boxes or a single large building '
             'and have no territory of their own; they are absent from the Census '
             'file, and the calculator says so rather than guessing at a neighbor. '
             'Some ZIP codes straddle a county line, and occasionally the two '
             'counties sit in different locality pay areas \u2014 about 1,400 of the '
             '33,791 do. In that case we return the area covering the larger share '
             'of the ZIP\u2019s land, which is right far more often than not but is '
             'not a guarantee. And a few military installations are assigned by OPM '
             'to a different locality than the county around them; the base gate can '
             'be a pay boundary.</p>')
    B.append('<p>When the answer matters \u2014 a job offer, a relocation, a '
             'grievance \u2014 confirm it with your servicing HR office. What this '
             'page can tell you exactly is what each locality pays. Which locality '
             'you are in is a question about your paperwork.</p>')

    B.append('<h2>The line other calculators do not print</h2>')
    B.append(f'<p>Locality pay is calculated from what <em>private employers in the '
             f'same region pay for comparable work</em>. It is not a cost-of-living '
             f'adjustment, and OPM says so plainly. The two are related but they are '
             f'not the same thing, and the gap between them is large enough to '
             f'reverse the ranking of the highest-paying areas.</p>')
    B.append(f'<p>So alongside the salary this calculator divides it by the local '
             f'price level \u2014 the Bureau of Economic Analysis Regional Price '
             f'Parity for {R["bea_year"]}, where 100 is the national average, '
             f'shown here to one decimal place though computed from the '
             f'published three \u2014 '
             f'and tells you where that leaves you against the other localities. On '
             f'paper the best-paid GS-12 in the country works in San Jose\u2013San '
             f'Francisco\u2013Oakland. Once prices are counted, the salary that goes '
             f'furthest belongs to Laredo, Texas.</p>')
    B.append('<p>Two cautions on that comparison. The price index is published a '
             'year or more behind the pay tables, and metropolitan boundaries do not '
             'match locality boundaries exactly, so the nearest metropolitan area is '
             'used as the proxy. Where two areas come out within one percent of each '
             'other, the calculator says they are the same rather than pretending to '
             'a precision the data does not have.</p>')

    B.append('<h2>Overtime, and why it is often worth less than you expect</h2>')
    B.append('<p>For most federal employees an overtime hour is paid at one and a '
             'half times the hourly rate. Above a threshold it is not. Under '
             '5 U.S.C. 5542, once your own hourly rate exceeds the hourly rate for '
             'GS-10 step 1 in your locality, the overtime hour is paid at the '
             '<em>greater</em> of your own rate and one and a half times that GS-10 '
             'step 1 rate \u2014 whichever is larger, not both.</p>')
    B.append('<p>The practical effect surprises people. A GS-13 or GS-14 working an '
             'extra hour is frequently paid exactly their ordinary hourly rate for '
             'it, with no premium at all, because their own rate has already '
             'overtaken the capped figure. The calculator prints the overtime rate '
             'for the cell you chose and says plainly when it has stopped being a '
             'premium.</p>')

    B.append('<h2>When the next step arrives</h2>')
    B.append('<p>Step increases are not a raise you negotiate; they arrive on a '
             'fixed schedule as long as performance is acceptable. One year each to '
             'reach steps 2, 3 and 4; two years each to reach steps 5, 6 and 7; '
             'three years each to reach steps 8, 9 and 10. From step 1 to step 10 is '
             'eighteen years at the same grade.</p>')
    B.append('<p>A promotion to a higher grade restarts that clock, which is why a '
             'promotion landing a month before a step increase was due can be worth '
             'less in the first year than it looks. Long periods in non-pay status '
             'push the waiting period out as well.</p>')

    B.append('<h2>Pay systems this calculator does not cover</h2>')
    B.append('<p>Roughly a third of federal employees are not paid from the General '
             'Schedule at all. Wage Grade trades and labor positions use locality '
             'wage schedules built from local prevailing rates. The Senior Executive '
             'Service, the Federal Aviation Administration, the Transportation '
             'Security Administration, Department of Veterans Affairs Title 38 '
             'medical positions and several demonstration projects each run their own '
             'systems.</p>')
    B.append('<p>Two adjustments sit on top of the General Schedule and are not '
             'modelled here. <strong>Special rate tables</strong> cover occupations '
             'where the government struggles to recruit; where one applies, the '
             'employee receives the higher of the special rate and the locality rate '
             '\u2014 never the two added together. <strong>Law enforcement '
             'officers</strong> at grades GS-3 through GS-10 are entitled to higher '
             'locality rates than the ordinary table shows. If either applies to you, '
             'the figure here is a floor rather than an answer.</p>')

    B.append('<h2>Where the numbers come from</h2>')
    B.append(f'<p>Salary tables and locality percentages: U.S. Office of Personnel '
             f'Management, {year} General Schedule salary tables. Locality pay area '
             f'definitions: OPM, {year}. Price levels: U.S. Bureau of Economic '
             f'Analysis Regional Price Parities, {R["bea_year"]}. ZIP-code-to-county '
             f'relationships: U.S. Census Bureau, 2020 ZCTA relationship file. All '
             f'are works of the United States government and in the public '
             f'domain.</p>')

    return shell(f"GS Pay Calculator {year} \u2014 by ZIP code, with locality",
                 f"Work out any {year} General Schedule salary by ZIP code, grade and "
                 f"step. Annual, biweekly, hourly and overtime, plus what it is worth "
                 f"after local prices.",
                 "\n".join(B), "https://fedpayscale.com/calculator/", "calc",
                 crumbs=[("All localities", "/"), ("Pay calculator", None)], js=js, rail=rail)


def contact(shell, contact_email: str, owner: str) -> str:
    """Одна страница, один адрес, читает человек."""
    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li>Contact</li></ol>',
         '<h1>Contact FedPay</h1>',
         '<p class="sub">One address, read by a person. There is no support queue, '
         'no ticket number and no chatbot.</p>',

         '<section class="q"><h2>Write to us</h2>',
         f'<p class="q-lead"><a href="mailto:{contact_email}">{contact_email}</a></p>',
         f'<p>FedPay is published by {owner}, a limited liability company registered '
         f'in the State of Wyoming. Postal correspondence can be sent through the '
         f'company\u2019s registered agent; write to the address above and we will '
         f'provide the details.</p>',
         '<p>We read everything and answer anything that needs an answer. What we '
         'do not do is send marketing: there is no mailing list to join and no '
         'reason for us to write to you unprompted.</p></section>',

         '<section class="q"><h2>If a number here is wrong</h2>',
         '<p class="q-lead">Tell us, and include the page and the figure you think '
         'is incorrect.</p>',
         '<p>Every rate on this site is recomputed from the published OPM base '
         'table and the locality percentage, in the order the law sets, and checked '
         'against the official table cell by cell \u2014 all 8,700 of them. So a '
         'genuine discrepancy means one of two things: the source has changed, or '
         'we have a defect. Both matter, and both get fixed.</p>',
         '<p>Corrections are made on the page itself, and the change moves the '
         '"data last changed" date in the footer. We do not quietly edit a figure '
         'and leave the date where it was.</p></section>',

         '<section class="q"><h2>What a reference site cannot do</h2>',
         '<p class="q-lead">Three things people write to ask, and the honest answer '
         'to each.</p>',
         '<p><strong>Which locality pay area am I in?</strong> We cannot tell you. '
         'Locality follows your official duty station, which is a fact about your '
         'paperwork, not about geography \u2014 telework arrangements, military '
         'installations and county lines all complicate it. Our '
         '<a href="/calculator/">calculator</a> will find the area a ZIP code sits '
         'in, and that is right far more often than not, but the authority is your '
         'servicing human resources office.</p>',
         '<p><strong>Should I take this job, or this transfer?</strong> We cannot '
         'advise you. FedPay publishes public federal data and arithmetic performed '
         'on it. It is not a licensed adviser of any kind, nothing here is advice, '
         'and the parts of that decision that matter most are usually not about '
         'money at all.</p>',
         '<p><strong>Can you change a rate?</strong> No. If a published rate looks '
         'wrong to you, the authority is the U.S. Office of Personnel Management, '
         'not this site. We report what OPM publishes; where we disagree with our '
         'own arithmetic, the build stops.</p></section>',

         '<section class="q"><h2>Press, researchers and data use</h2>',
         '<p>The underlying data \u2014 OPM salary tables, OPM locality pay area '
         'definitions, BEA Regional Price Parities and the Census Bureau '
         'ZIP-code-to-county file \u2014 are works of the United States government '
         'and in the public domain. You need nobody\u2019s permission to use them, '
         'and for anything serious you should go to the source rather than to '
         'us.</p>',
         '<p>What is ours is the arrangement of this site, its wording, and the '
         'purchasing-power comparison that sits at the center of it. If you want to '
         'quote or reproduce that, write to the address above. We answer, and the '
         'answer is usually yes.</p></section>']
    return shell("Contact FedPay",
                 "How to reach FedPay, how to report a figure you think is wrong, "
                 "and what a reference site can and cannot answer.",
                 "\n".join(B), "https://fedpayscale.com/contact/", "contact",
                 crumbs=[("All localities", "/"), ("Contact", None)])


def methodology(T: dict, R: dict, shell, money, owner: str, contact_email: str) -> str:
    """Как получается каждое число и что останавливает публикацию."""
    year, cap = T["year"], T["ex_iv_cap"]
    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li>Methodology</li></ol>',
         '<h1>How these numbers are made</h1>',
         '<p class="sub">Every figure on this site can be traced to a published '
         'federal source and reproduced from it. This page says exactly how, and '
         'what stops publication when something does not add up.</p>',

         '<section class="q"><h2>Who publishes this</h2>',
         f'<p class="q-lead">FedPay is published by {owner}, a limited liability '
         f'company registered in the State of Wyoming.</p>',
         '<p>It is a small independent publisher. It is not a newsroom, not a '
         'consultancy, not a government body and not connected to one. Nobody pays '
         'to appear here and there is no sponsored content of any kind. When '
         'advertising is added it will be visually separated and labelled, and it '
         'will have no influence on any figure or any wording on this site.</p>',
         f'<p>The reason to trust a number here is not who wrote it. It is that you '
         f'can check it: the source is named, the arithmetic is described, and the '
         f'result is reproducible. Where you find that we are wrong, '
         f'<a href="/contact/">tell us</a> \u2014 corrections are made on the page '
         f'and move the date in the footer.</p></section>',

         '<section class="q"><h2>Where every number comes from</h2>',
         '<p class="q-lead">Four public datasets, all works of the United States '
         'government and all in the public domain.</p>',
         f'<p><strong>Salary tables and locality percentages.</strong> U.S. Office '
         f'of Personnel Management, {year} General Schedule salary tables, taken '
         f'from the machine-readable files OPM publishes rather than retyped from a '
         f'PDF. The list of locality codes is read from OPM\u2019s own index page '
         f'each time, never hardcoded: the number of areas has changed from 48 to 54 '
         f'to 58, and a fixed list would silently miss a new one.</p>',
         f'<p><strong>Locality pay area definitions.</strong> OPM, {year}. These are '
         f'the counties and military installations that make up each area \u2014 '
         f'920 counties across 57 areas, with Rest of U.S. defined by exclusion.</p>',
         f'<p><strong>Price levels.</strong> U.S. Bureau of Economic Analysis '
         f'Regional Price Parities for {R["bea_year"]}, at metropolitan level for the '
         f'55 metropolitan areas and at state level for Alaska and Hawaii, where the '
         f'locality area is the whole state and the state index is therefore an '
         f'exact match rather than a proxy.</p>',
         '<p><strong>ZIP code relationships.</strong> U.S. Census Bureau 2020 ZCTA '
         'to county relationship file, used only to answer "which area is this ZIP '
         'in".</p></section>',

         '<section class="q"><h2>The arithmetic, in the order the law sets it</h2>',
         '<p class="q-lead">Locality rate = base rate, multiplied by one plus the '
         'locality percentage, rounded to the nearest dollar, and only then checked '
         'against the statutory ceiling.</p>',
         f'<p>That order matters. No General Schedule rate may exceed Level IV of '
         f'the Executive Schedule, {money(cap)} in {year}. Applying the ceiling '
         f'before rounding rather than after gives different figures at the top of '
         f'the schedule, which is one reason published numbers occasionally disagree '
         f'between reference sites. In {year} the ceiling binds 97 cells across 37 '
         f'areas.</p>',
         '<p>Two derived figures follow the same discipline. The hourly rate is the '
         'annual rate divided by 2,087 hours, rounded to the cent. The biweekly rate '
         'is the hourly rate multiplied by 80 \u2014 not the annual rate divided by '
         '26, which gives a different and wrong answer. The overtime rate follows '
         '5 U.S.C. 5542: one and a half times your hourly rate while that rate stays '
         'at or below the GS-10 step 1 rate for your area, and above it the greater '
         'of your own rate and one and a half times GS-10 step 1.</p>',
         '<p>Each of those three rules was derived from the published data itself '
         'and then checked against all 8,700 published cells. Not one disagrees.'
         '</p></section>',

         '<section class="q"><h2>What the purchasing-power figure is, and is not</h2>',
         '<p class="q-lead">It is the salary divided by the local price level. '
         'Nothing more elaborate than that, and nothing hidden.</p>',
         '<p>Locality pay is calculated from what private employers in the same '
         'region pay for comparable work. It is not a cost-of-living adjustment, and '
         'OPM says so plainly. Dividing the salary by the BEA price index, where 100 '
         'is the national average, gives a figure that is comparable across the '
         'country: what the salary would have to be, at average U.S. prices, to buy '
         'the same things.</p>',
         '<p>Three limits are stated on every page that uses it. The price index is '
         'published a year or more behind the pay tables. Metropolitan boundaries do '
         'not match locality pay area boundaries exactly, so the nearest '
         'metropolitan area is used as the proxy and named. And where two areas come '
         'out within one percent of each other, we say they are the same rather than '
         'pretending to a precision the data does not have.</p>',
         '<p>Rest of U.S. is left without a figure entirely. It is a residual drawn '
         'from every state at once, no single price index describes it, and putting '
         '100 there would be an invention.</p></section>',

         '<section class="q"><h2>What stops publication</h2>',
         '<p class="q-lead">The build fails, and nothing ships, when any of sixteen '
         'checks finds a problem in the finished pages.</p>',
         '<p>The first is the strictest: every rate is recomputed independently from '
         'the base table and the percentage and compared with the figure OPM '
         'published. A single cell out by a dollar stops the build. On the '
         f'{year} tables all 8,700 match.</p>',
         '<p>The rest examine the rendered HTML rather than the source, because the '
         'defects that matter are the ones that survive a correct-looking build: a '
         'page that contradicts itself about whether an area gains or loses ground; '
         'an area silently missing from a table; a broken internal link; text that '
         'reaches the reader as an escape sequence instead of a character; a class '
         'with no styling behind it; a request to a third-party domain. Each check '
         'exists because that exact mistake was made here at least once.</p>',
         '<p>Every check is proved by deliberately breaking the source and '
         'confirming the build goes red. A check that has never failed proves '
         'nothing.</p>',
         '<p>Separately, the whole site is rebuilt from an empty directory before '
         'release, so that "it builds on my machine" cannot pass for "it '
         'builds".</p></section>',

         '<section class="q"><h2>What this site deliberately does not do</h2>',
         '<p class="q-lead">Take-home pay, tax, and advice.</p>',
         '<p>Every figure here is gross pay: what the job pays before anything is '
         'taken out. Take-home depends on your FERS tier, your Thrift Savings Plan '
         'contribution and its type, your health and life insurance elections, your '
         'filing status and the income tax of the state you live in \u2014 which is '
         'not always the state you work in. We would rather publish one number that '
         'is exactly right than a take-home estimate resting on half a dozen '
         'assumptions invented on your behalf.</p>',
         '<p>Nor does this site cover the Federal Wage System, the Senior Executive '
         'Service, Title 38 medical positions, law enforcement officer rates or '
         'special rate tables. Where one of those applies to you, the figure here is '
         'a floor rather than an answer, and every page that could mislead you says '
         'so.</p>',
         f'<p>And nothing here is advice. FedPay publishes public federal data and '
         f'arithmetic performed on it. Questions about your own pay belong to your '
         f'servicing human resources office. Questions about this site belong to '
         f'<a href="mailto:{contact_email}">{contact_email}</a>.</p></section>']
    return shell("How FedPay Makes Its Numbers",
                 "The sources, the arithmetic in the order the law sets it, the "
                 "sixteen checks that stop publication, and what this site "
                 "deliberately does not do.",
                 "\n".join(B), "https://fedpayscale.com/methodology/", "method",
                 crumbs=[("All localities", "/"), ("Methodology", None)])
