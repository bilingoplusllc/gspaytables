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


def home(T: dict, R: dict, ranks: dict, L: dict, shell, esc, money, slug) -> str:
    year = T["year"]
    locs = T["localities"]
    rows = ranks["rows"]

    B = [f'<h1>2026 GS pay scale, by locality</h1>']
    B.append(f'<p class="sub">Every General Schedule rate for all {len(locs)} locality '
             f'pay areas, recomputed from the official tables and checked cell by cell. '
             f'Plus the thing the tables do not tell you: what each salary is actually '
             f'worth once local prices are taken into account.</p>')

    top = rows[0]
    nom_top = max(rows, key=lambda r: r["nominal"])
    B.append('<div class="answer">')
    B.append('<span class="what">The finding most people miss</span>')
    B.append(f'<p style="margin-top:0">At GS-{12} step {5}, the highest-paying locality '
             f'on paper is <strong>{esc(nom_top["name"])}</strong> at '
             f'{money(nom_top["nominal"])}. But once local prices are counted, the '
             f'salary that goes furthest belongs to <strong>{esc(top["name"])}</strong> '
             f'— {money(top["adjusted"])} of purchasing power from a salary of '
             f'{money(top["nominal"])}.</p>')
    B.append(f'<p>Locality pay tracks what private employers in a region pay, not what '
             f'life there costs. The two are related, but not the same, and the gap is '
             f'large enough to reverse the ranking.</p></div>')

    # --- таблица всех зон
    body = []
    for i, r in enumerate(rows, 1):
        code = r["code"]
        pct = locs[code]["locality_pct"]
        nrank = ranks["nominal"][code]
        # Движение между двумя рейтингами — это и есть тезис экспоната.
        # Голый «ранг на бумаге» заставлял читателя вычитать в уме.
        delta = nrank - i
        move = f"+{delta}" if delta > 0 else (f"−{-delta}" if delta < 0 else "—")
        move_cls = "up" if delta > 0 else ("down" if delta < 0 else "flat")
        body.append(
            f'<tr><td class="rank">{i}</td>'
            f'<th scope="row"><a href="/locality/{slug(r["name"])}/">{esc(r["name"])}</a></th>'
            f'<td class="num">{pct:g}%</td>'
            f'<td class="num">{money(r["nominal"])}</td>'
            f'<td class="num">{r["rpp"]:.1f}</td>'
            f'<td class="num">{money(r["adjusted"])}</td>'
            f'<td class="num {move_cls}">{move}</td></tr>')

    # зоны без данных о ценах — показываем отдельно, а не прячем
    missing = [c for c in locs if c not in ranks["adjusted"]]
    extra = []
    for code in missing:
        loc = locs[code]
        cell = loc["grades"]["12"]["5"]
        extra.append(
            f'<tr><td class="rank">—</td>'
            f'<th scope="row"><a href="/locality/{slug(loc["area_name"])}/">'
            f'{esc(loc["area_name"])}</a></th>'
            f'<td class="num">{loc["locality_pct"]:g}%</td>'
            f'<td class="num">{money(cell["annual"])}</td>'
            f'<td class="num">—</td><td class="num">—</td>'
            f'<td class="num flat">—</td></tr>')

    B.append(f"""<figure class="ex">
<div class="ex-kicker">Exhibit 1 · all {len(locs)} localities</div>
<div class="ex-title">Ranked by what a GS-12 step 5 salary actually buys</div>
<p class="ex-note">Sorted by purchasing power, not by the size of the cheque. The price
column is the BEA Regional Price Parity for {R['bea_year']}, where 100 is the national
average — below 100 is cheaper than average. The last column is the one to read: it
shows how many places the area moves when you stop ranking by the size of the cheque and
start ranking by what the cheque buys.</p>
<div class="scroll"><table>
<thead><tr><th class="rank">#</th><th>Locality</th><th class="num">Locality pay</th>
<th class="num">On paper</th><th class="num">Prices</th><th class="num">What it buys</th>
<th class="num">Rank shift</th></tr></thead>
<tbody>{''.join(body)}{''.join(extra)}</tbody>
</table></div>
<figcaption>Sources: OPM {year} General Schedule salary tables; BEA Regional Price
Parities {R['bea_year']}. Alaska, Hawaii and Rest of U.S. have no single metropolitan
price index, so they are listed without an adjusted figure rather than given an
invented one.</figcaption>
</figure>""")

    B.append('<h2>Browse by grade</h2>')
    B.append('<p>Each grade page shows that grade in every locality at once, which is '
             'the comparison people actually need when weighing a move.</p>')
    chips = "".join(f'<a href="/gs-{g}/">GS-{g}</a>' for g in sorted(T["base"]["grades"], key=int))
    B.append(f'<div class="chips">{chips}</div>')

    return shell(f"2026 GS Pay Scale by Locality — all {len(locs)} areas | FedPay",
                 f"Complete {year} General Schedule pay tables for all {len(locs)} "
                 f"locality pay areas, ranked by what each salary buys after local "
                 f"prices, not just by the headline number.",
                 "\n".join(B), "https://fedpayscale.com/", "home")


def grade_page(g: str, T: dict, R: dict, ranks: dict, shell, esc, money, slug) -> str:
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
<p class="ex-note">Sorted by the number on the cheque. The last column divides that
number by the local price level, so it is comparable in what it buys. Cells marked ▲
have been cut to the {money(cap)} statutory ceiling.</p>
<div class="scroll"><table>
<thead><tr><th class="rank">#</th><th>Locality</th><th class="num">Salary</th>
<th class="num">Prices</th><th class="num">What it buys</th></tr></thead>
<tbody>{''.join(body)}</tbody>
</table></div>
<figcaption>The best-paid GS-{g} on paper is in {esc(hi['name'])} at {money(hi['pay'])}.
The best-off GS-{g} in practice is in {esc(best_adj['name'])}, where {money(best_adj['pay'])}
buys what {money(best_adj['adj'])} buys at national average prices. Alaska, Hawaii and
Rest of U.S. have no single metropolitan price index, so their last two columns are left
empty rather than filled with a guess. Sources: OPM {year} salary tables; BEA Regional
Price Parities {R['bea_year']}.</figcaption>
</figure>""")

    B.append(f'<h2>All ten steps of GS-{g}</h2>')
    B.append(f'<p>These are base rates before any locality adjustment. Multiply by your '
             f'area\'s percentage — or open your locality page, where the arithmetic is '
             f'already done.</p>')
    cells = "".join(f'<td class="num">{money(base[str(s)]["annual"])}</td>'
                    for s in range(1, 11))
    heads = "".join(f'<th class="num">{s}</th>' for s in range(1, 11))
    B.append(f'<div class="scroll"><table><thead><tr><th>Step</th>{heads}</tr></thead>'
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
    B.append(f'<div class="scroll"><table><thead><tr><th>Reaching</th>'
             f'<th class="num">Wait (years)</th><th class="num">Years from start</th>'
             f'<th class="num">Base increase</th></tr></thead>'
             f'<tbody>{"".join(rows2)}</tbody></table></div>')
    B.append('<p>A promotion to a higher grade restarts that clock, which is why a '
             'promotion arriving a month before a step increase can be worth less in '
             'the first year than it appears. The waiting period also pauses during '
             'periods of non-pay status beyond a threshold, so long unpaid absences '
             'push the next increase further out.</p>')

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
                         (f"GS-{g}", None)])


def how_it_works(T: dict, shell, money) -> str:
    year, cap = T["year"], T["ex_iv_cap"]
    B = ['<h1>How locality pay actually works</h1>']
    B.append('<p class="sub">The rules behind the number, including the three that '
             'surprise people most: locality is not cost of living, steps are not '
             'evenly spaced, and raises stop counting once you hit the ceiling.</p>')

    B.append('<h2>It is a labour-market adjustment, not a cost-of-living one</h2>')
    B.append('<p>Locality pay exists because of the Federal Employees Pay Comparability '
             'Act of 1990, which set out to close the gap between federal and '
             'non-federal salaries in the same labour market. The comparison is against '
             '<em>what other employers in that region pay for similar work</em>, '
             'measured by the Bureau of Labor Statistics. It is not a measure of what '
             'housing, food or childcare cost there.</p>')
    B.append('<p>The practical consequence runs through this whole site: an area can pay '
             'a large adjustment and still leave you with less, because a strong '
             'private labour market and expensive living usually travel together but '
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
                 "Locality pay is a labour-market adjustment, not a cost-of-living "
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
         '<p>This site uses Google Analytics 4 to count visits and see which pages are '
         'read. It records the page you viewed, where you arrived from, your approximate '
         'location derived from your IP address, and your browser and device type. '
         'Google Analytics 4 does not log or store IP addresses. We never see your name, '
         'your email or anything that identifies you personally.</p>',
         '<p>Outside the European Economic Area, the United Kingdom and Switzerland, '
         'Analytics sets its own cookies to tell a returning visit from a new one. '
         'Inside those regions analytics storage is switched off by default, so no '
         'analytics cookie is set at all unless you choose otherwise. You can block '
         'Analytics everywhere with Google\'s official '
         '<a href="https://tools.google.com/dlpage/gaoptout">opt-out browser add-on</a>.</p>',
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
    return shell("Page not found — FedPay",
                 "That address does not match anything on this site.",
                 "\n".join(B), "")


def sitemap(urls: list[str], domain: str) -> str:
    today = date.today().isoformat()
    body = "".join(f"<url><loc>{domain}{u}</loc><lastmod>{today}</lastmod></url>"
                   for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f'{body}</urlset>')


def grades_index(T: dict, ranks: dict, shell, esc, money) -> str:
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
<div class="scroll"><table>
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
                         ("All grades", None)])
