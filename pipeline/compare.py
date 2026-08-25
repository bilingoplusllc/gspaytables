"""Страницы сравнения двух зон.

Зачем. Человек не спрашивает «сколько платят в Вашингтоне». Он спрашивает
«Вашингтон или Сан-Франциско» — потому что перед ним два предложения о работе
или предложение о переводе. Это отдельное поисковое намерение, и у растущего
конкурента gstakehomepay.com под него есть целый раздел (dc-vs-san-francisco,
california-vs-texas), а у нас не было ничего.

Почему у нас получится лучше. Конкурент сравнивает суммы на бумаге. Мы можем
ответить на вопрос, который человек на самом деле задаёт: где он окажется
богаче. Плюс две вещи, которых нет ни у кого:

* точка равновесия — какой грейд в дешёвой зоне даёт ту же покупательную
  способность, что и рассматриваемый грейд в дорогой;
* потолок — в дорогой зоне ступени перестают приносить деньги раньше, и при
  сравнении карьеры это важнее разовой разницы в окладе.

Пары не выдумываются: берутся зоны с наибольшими ставками (именно туда зовут
на работу) плюс Rest of U.S. — самая многочисленная зона, с которой сравнивают
переезд чаще всего.
"""
from __future__ import annotations

REF_GRADE, REF_STEP = "12", "5"


def pairs(T: dict, ranks: dict, top: int = 6) -> list:
    """Пары для сравнения: самые высокооплачиваемые зоны и остаток США."""
    by_pay = sorted(
        T["localities"].items(),
        key=lambda kv: -kv[1]["grades"][REF_GRADE][REF_STEP]["annual"])
    picked = [c for c, _ in by_pay[:top]]
    if "RUS" not in picked:
        picked.append("RUS")
    out = []
    for i, a in enumerate(picked):
        for b in picked[i + 1:]:
            out.append((a, b))
    return out


def _adj(pay: float, rpp) -> float | None:
    return pay / (rpp / 100.0) if rpp else None


def compare_page(a: str, b: str, T: dict, R: dict, ranks: dict,
                 L: dict, shell, esc, money, slug) -> tuple:
    """Возвращает (относительный адрес, HTML)."""
    year, cap = T["year"], T["ex_iv_cap"]
    la, lb = T["localities"][a], T["localities"][b]
    na, nb = la["area_name"], lb["area_name"]
    ra = R["areas"].get(a, {}).get("rpp")
    rb = R["areas"].get(b, {}).get("rpp")

    pa = la["grades"][REF_GRADE][REF_STEP]["annual"]
    pb = lb["grades"][REF_GRADE][REF_STEP]["annual"]
    aa, ab = _adj(pa, ra), _adj(pb, rb)

    # Порядок в заголовке — по ставке на бумаге: так его и набирают в поиске.
    if pb > pa:
        a, b = b, a
        la, lb = lb, la
        na, nb = nb, na
        ra, rb = rb, ra
        pa, pb = pb, pa
        aa, ab = ab, aa

    short_a, short_b = _short(na), _short(nb)
    rel = f"compare/{slug(short_a)}-vs-{slug(short_b)}"

    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li><a href="/compare/">Compare</a></li>'
         f'<li>{esc(short_a)} vs {esc(short_b)}</li></ol>']
    B.append(f'<h1>{esc(short_a)} vs {esc(short_b)}: GS pay compared, {year}</h1>')

    gap = pa - pb
    B.append(f'<p class="sub">The same grade and step pays {money(gap)} more a year '
             f'in {esc(short_a)}. Whether that leaves you better off is a different '
             f'question, and this page answers it.</p>')

    # --- вердикт
    B.append('<div class="answer">')
    B.append(f'<span class="what">GS-{REF_GRADE} step {REF_STEP}, {year}</span>')
    B.append('<div class="body">')
    if aa and ab:
        winner, loser = (short_a, short_b) if aa > ab else (short_b, short_a)
        diff = abs(aa - ab)
        material = diff >= max(pa, pb) * 0.01
        B.append(f'<span class="big">{money(diff)}</span>')
        if material:
            B.append(f'<p>That is how much more a GS-{REF_GRADE} step {REF_STEP} is '
                     f'worth in <strong>{esc(winner)}</strong> than in '
                     f'{esc(loser)}, once local prices are counted — even '
                     f'though {esc(short_a)} pays {money(gap)} more on paper.</p>'
                     if winner == short_b else
                     f'<p>That is how much more a GS-{REF_GRADE} step {REF_STEP} is '
                     f'worth in <strong>{esc(winner)}</strong> than in '
                     f'{esc(loser)} once local prices are counted. Here the bigger '
                     f'cheque and the better outcome point the same way.</p>')
        else:
            B.append(f'<p>That is the difference in purchasing power between the two '
                     f'— less than one percent of the salary, which is inside '
                     f'the error of the price data. On the money these are the same '
                     f'place, and the choice belongs to everything else.</p>')
    else:
        B.append(f'<span class="big">{money(gap)}</span>')
        B.append(f'<p>That is the gap on paper. One of these areas has no published '
                 f'metropolitan price index, so the purchasing-power comparison '
                 f'cannot be made without inventing a number, and we will not.</p>')

    rows = [
        ("Salary on paper", money(pa), money(pb)),
        ("Locality pay", f'{la["locality_pct"]:g}%', f'{lb["locality_pct"]:g}%'),
        ("Local price level", f"{ra:.1f}" if ra else "—",
         f"{rb:.1f}" if rb else "—"),
        ("What it buys", money(aa) if aa else "—",
         money(ab) if ab else "—"),
        ("Rank on paper", f'#{ranks["nominal"].get(a, "—")}',
         f'#{ranks["nominal"].get(b, "—")}'),
        ("Rank by what it buys", f'#{ranks["adjusted"].get(a, "—")}',
         f'#{ranks["adjusted"].get(b, "—")}'),
    ]
    cells = "".join(
        f'<tr><th scope="row">{lbl}</th><td class="num">{va}</td>'
        f'<td class="num">{vb}</td></tr>' for lbl, va, vb in rows)
    B.append(f'<div class="scroll" tabindex="0" role="region" '
             f'aria-label="Scrollable table"><table><thead><tr><th></th>'
             f'<th class="num">{esc(short_a)}</th>'
             f'<th class="num">{esc(short_b)}</th></tr></thead>'
             f'<tbody>{cells}</tbody></table></div>')
    B.append('</div></div>')

    # --- по всем грейдам
    body = []
    for g in range(1, 16):
        ca = la["grades"][str(g)][REF_STEP]
        cb = lb["grades"][str(g)][REF_STEP]
        xa, xb = _adj(ca["annual"], ra), _adj(cb["annual"], rb)
        mark_a = ' class="num capped"' if ca["capped"] else ' class="num"'
        mark_b = ' class="num capped"' if cb["capped"] else ' class="num"'
        if xa and xb:
            d = xa - xb
            sign = "+" if d > 0 else ("−" if d < 0 else "")
            cls = "up" if d > 0 else ("down" if d < 0 else "flat")
            delta = f'<td class="num {cls}">{sign}{money(abs(d))[1:]}</td>'
        else:
            delta = '<td class="num flat">—</td>'
        body.append(
            f'<tr><th scope="row">GS-{g}</th>'
            f'<td{mark_a}>{ca["annual"]:,}</td><td{mark_b}>{cb["annual"]:,}</td>'
            f'{delta}</tr>')

    B.append(f"""<figure class="ex">
<div class="ex-kicker">Exhibit 1 &middot; every grade at step {REF_STEP}</div>
<div class="ex-title">What each grade is worth in the two areas</div>
<p class="ex-note">The first two columns are the salaries as published. The last
column is the difference in what those salaries buy after local prices &mdash;
positive means {esc(short_a)} comes out ahead, negative means {esc(short_b)} does.
Cells marked &#9650; have been cut to the {money(cap)} statutory ceiling.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Scrollable table">
<table><thead><tr><th>Grade</th>
<th class="num">{esc(short_a)}</th><th class="num">{esc(short_b)}</th>
<th class="num">Difference after prices</th></tr></thead>
<tbody>{"".join(body)}</tbody></table></div>
<figcaption>Sources: OPM {year} General Schedule salary tables; BEA Regional Price
Parities {R['bea_year']}. Step {REF_STEP} is used throughout so the grades are
comparable; the full tables for each area are linked below.</figcaption>
</figure>""")

    B.append(_threshold(short_a, short_b, la, lb, ra, rb, R, money, esc))
    B.append(_steps(short_a, short_b, la, lb, ra, rb, money, esc))
    B.append(_overtime(short_a, short_b, la, lb, money, esc))
    B.append(_breakeven(short_a, short_b, la, lb, ra, rb, money, esc, cap))
    B.append(_ceiling(short_a, short_b, la, lb, cap, money, esc, year))
    B.append(_places(short_a, short_b, na, nb, L.get(a, {}), L.get(b, {}),
                     money, esc, slug))

    title = f"{short_a} vs {short_b} GS Pay {year}"
    desc = (f"GS-{REF_GRADE} step {REF_STEP} pays {money(pa)} in {short_a} and "
            f"{money(pb)} in {short_b}{_dot(short_b)} Which one leaves you better "
            f"off after local prices, grade by grade.")
    return rel, shell(
        title, desc, "\n".join(B), f"https://fedpayscale.com/{rel}/", "compare",
        crumbs=[("All localities", "/"), ("Compare", "/compare/"),
                (f"{short_a} vs {short_b}", None)])


def _dot(name: str) -> str:
    """Точка, если имя ею ещё не кончается. «Rest of U.S.» — кончается."""
    return "" if name.rstrip().endswith(".") else "."


def _short(name: str) -> str:
    """Короткое имя для заголовка: первый город плюс код штата."""
    head, _, tail = name.partition(",")
    if head.startswith("State of"):
        return head.replace("State of", "").strip()
    if head.startswith("Rest of"):
        return "Rest of U.S."
    first = (head.split("--") if "--" in head else head.split("-"))[0].strip()
    state = tail.strip().split("-")[0].strip() if tail else ""
    return f"{first}, {state}" if state else first


def _threshold(sa, sb, la, lb, ra, rb, R, money, esc) -> str:
    """Порог цены для зоны без индекса.

    Когда у одной стороны индекса нет, вопрос «где богаче» не имеет ответа.
    Зато имеет ответ обратный: НАСКОЛЬКО дешёвым должно быть место, чтобы
    меньшая ставка сравнялась с большей. Считается из двух опубликованных
    ставок и одного опубликованного индекса — ничего не выдумано.
    """
    if ra and rb:
        return ""
    if ra:
        known_n, known_r, known = sa, ra, la
        unknown_n, unknown = sb, lb
    elif rb:
        known_n, known_r, known = sb, rb, lb
        unknown_n, unknown = sa, la
    else:
        return ""

    pk = known["grades"][REF_GRADE][REF_STEP]["annual"]
    pu = unknown["grades"][REF_GRADE][REF_STEP]["annual"]
    buys = pk / (known_r / 100.0)
    # Индекс цен, при котором меньшая ставка даёт ту же покупательную способность.
    need = pu / buys * 100.0

    levels = sorted(v["rpp"] for v in R["areas"].values() if v.get("rpp"))
    cheaper = sum(1 for v in levels if v <= need)

    out = ['<h2>How cheap would it have to be?</h2>']
    out.append(f'<p>{esc(unknown_n)} has no metropolitan price index of its own, so '
               f'the straight purchasing-power comparison cannot be made \u2014 and '
               f'we are not going to invent a number for it. The question turns '
               f'round, though, and in that form it has an exact answer.</p>')
    out.append(f'<p>A GS-{REF_GRADE} step {REF_STEP} in {esc(known_n)} earns '
               f'{money(pk)} where prices stand at {known_r:.1f} against a national '
               f'average of 100. That buys what <strong>{money(buys)}</strong> buys '
               f'at average U.S. prices. The same grade on the {esc(unknown_n)} rate '
               f'earns {money(pu)}. For those two to come out equal, the place you '
               f'live on the {esc(unknown_n)} rate would need a price level of '
               f'<strong>{need:.1f}</strong> or below.</p>')
    if need >= 100:
        out.append(f'<p>That is above the national average, which means the '
                   f'{esc(unknown_n)} rate comes out ahead almost anywhere: even an '
                   f'averagely expensive place clears the bar. Of the '
                   f'{len(levels)} localities with published price data, '
                   f'<strong>{cheaper}</strong> sit at or below that level.</p>')
    elif cheaper == 0:
        out.append(f'<p>Not one of the {len(levels)} measured localities is that '
                   f'cheap. On this comparison {esc(known_n)} wins outright, and it '
                   f'is not close.</p>')
    else:
        out.append(f'<p>Of the {len(levels)} localities with published price data, '
                   f'<strong>{cheaper}</strong> sit at or below that level \u2014 '
                   f'so the bar is reachable, but it rules out the expensive half of '
                   f'the country. If the job can be done from anywhere, this is the '
                   f'number that decides where.</p>')
    out.append(f'<p>One caution on reading it. The price index describes what things '
               f'cost now, not what they cost you: a mortgage signed years ago, or a '
               f'house owned outright, changes the arithmetic in a way no published '
               f'index can see.</p>')
    return "\n".join(out)


def _steps(sa, sb, la, lb, ra, rb, money, esc) -> str:
    """Разрыв по ступеням внутри одного грейда.

    Разница между двумя предложениями редко бывает в одном грейде: обычно
    сравнивают «GS-13 шаг 1 там» против «GS-12 шаг 7 здесь». Строка по всем
    десяти ступеням отвечает на это без арифметики в уме.
    """
    g = REF_GRADE
    rows = []
    for s in range(1, 11):
        va = la["grades"][g][str(s)]["annual"]
        vb = lb["grades"][g][str(s)]["annual"]
        rows.append(f'<tr><th scope="row">Step {s}</th>'
                    f'<td class="num">{va:,}</td><td class="num">{vb:,}</td>'
                    f'<td class="num">{va - vb:,}</td></tr>')
    lo1 = la["grades"][g]["1"]["annual"]
    hi10 = lb["grades"][g]["10"]["annual"]
    out = [f'<h2>Step by step at GS-{g}</h2>']
    if lo1 > hi10:
        out.append(f'<p>The gap is wide enough that it swallows the whole grade: a '
                   f'GS-{g} at <strong>step 1</strong> in {esc(sa)} is paid more '
                   f'than a GS-{g} at <strong>step 10</strong> in {esc(sb)} '
                   f'\u2014 eighteen years of step increases, undone by the duty '
                   f'station alone.</p>')
    else:
        out.append(f'<p>Comparing offers rarely means comparing the same cell. This '
                   f'is GS-{g} across all ten steps in both areas, so a step 3 offer '
                   f'in one can be read against a step 7 offer in the other without '
                   f'arithmetic.</p>')
    out.append(f'<div class="scroll" tabindex="0" role="region" '
               f'aria-label="Scrollable table"><table><thead><tr><th>GS-{g}</th>'
               f'<th class="num">{esc(sa)}</th><th class="num">{esc(sb)}</th>'
               f'<th class="num">Gap</th></tr></thead>'
               f'<tbody>{"".join(rows)}</tbody></table></div>')
    if ra and rb:
        adj_a = la["grades"][g]["5"]["annual"] / (ra / 100.0)
        adj_b = lb["grades"][g]["5"]["annual"] / (rb / 100.0)
        raw_gap = la["grades"][g]["5"]["annual"] - lb["grades"][g]["5"]["annual"]
        real_gap = adj_a - adj_b
        kept = 0 if raw_gap == 0 else int(round(100 * real_gap / raw_gap))
        out.append(f'<p>The gap in the last column is the one on the offer letter. '
                   f'After local prices, {money(raw_gap)} of extra salary at step 5 '
                   f'is worth {money(real_gap)} of extra purchasing power \u2014 '
                   f'about <strong>{kept}%</strong> of what it looks like. The rest '
                   f'is absorbed by the difference in what things cost.</p>')
    return "\n".join(out)


def _overtime(sa, sb, la, lb, money, esc) -> str:
    """Порог переработки у двух зон разный, и это редко кто печатает."""
    ta = la["grades"]["10"]["1"]
    tb = lb["grades"]["10"]["1"]
    ref_a = la["grades"][REF_GRADE][REF_STEP]
    ref_b = lb["grades"][REF_GRADE][REF_STEP]
    out = ['<h2>Overtime is capped, and the cap differs</h2>']
    out.append(f'<p>Under 5 U.S.C. 5542 an overtime hour is paid at one and a half '
               f'times your hourly rate only while that rate stays at or below the '
               f'hourly rate of GS-10 step 1 in your own locality. Above it, the '
               f'hour is paid at the greater of your own rate and one and a half '
               f'times that GS-10 step 1 figure \u2014 not both.</p>')
    out.append(f'<p>That threshold is a local number, so it differs between these '
               f'two areas: ${ta["hourly"]:,.2f} an hour in {esc(sa)} against '
               f'${tb["hourly"]:,.2f} in {esc(sb)}{_dot(sb)} A GS-{REF_GRADE} step '
               f'{REF_STEP} earns ${ref_a["hourly"]:,.2f} an hour in {esc(sa)} and '
               f'${ref_b["hourly"]:,.2f} in {esc(sb)}, and is paid '
               f'${ref_a["overtime"]:,.2f} and ${ref_b["overtime"]:,.2f} '
               f'respectively for an overtime hour.</p>')
    flat_a = ref_a["overtime"] <= ref_a["hourly"]
    flat_b = ref_b["overtime"] <= ref_b["hourly"]
    if flat_a and flat_b:
        out.append('<p>In both areas that is the ordinary hourly rate with no '
                   'premium at all: at this grade the overtime cap has already '
                   'overtaken the employee. If overtime is a real part of the job, '
                   'it is worth knowing that it stops being worth more at this '
                   'level in either place.</p>')
    elif flat_a or flat_b:
        flat, keeps = (sa, sb) if flat_a else (sb, sa)
        out.append(f'<p>In {esc(flat)} that is the ordinary hourly rate with no '
                   f'premium at all, while in {esc(keeps)} the hour still carries '
                   f'one. The higher-paying area is the one that loses the premium '
                   f'first \u2014 another way the headline salary overstates the '
                   f'difference.</p>')
    else:
        out.append('<p>In both areas the overtime hour still carries a genuine '
                   'premium at this grade. It stops doing so higher up the '
                   'schedule, and sooner in the better-paid area.</p>')
    return "\n".join(out)


def _breakeven(sa, sb, la, lb, ra, rb, money, esc, cap) -> str:
    """Какой грейд в дешёвой зоне даёт ту же покупательную способность."""
    if not (ra and rb):
        return ""
    hi, lo = (la, lb) if ra > rb else (lb, la)
    hi_n, lo_n = (sa, sb) if ra > rb else (sb, sa)
    hi_r, lo_r = (ra, rb) if ra > rb else (rb, ra)

    out = ['<h2>The same money, a grade lower</h2>']
    lines = []
    for g in (11, 12, 13, 14):
        target = hi["grades"][str(g)][REF_STEP]["annual"] / (hi_r / 100.0)
        match = None
        for g2 in range(1, 16):
            for s2 in range(1, 11):
                v = lo["grades"][str(g2)][str(s2)]["annual"] / (lo_r / 100.0)
                if v >= target:
                    match = (g2, s2)
                    break
            if match:
                break
        if match:
            lines.append(f'<li>A GS-{g} step {REF_STEP} in {esc(hi_n)} is matched '
                         f'by a <strong>GS-{match[0]} step {match[1]}</strong> in '
                         f'{esc(lo_n)}.</li>')
    if not lines:
        return ""
    out.append(f'<p>Prices in {esc(hi_n)} are higher, so a salary there does less '
               f'work. The question that follows is obvious: what would you have to '
               f'earn in {esc(lo_n)} to be equally well off? These are the '
               f'equivalents, at the same step:</p>')
    out.append(f'<ul>{"".join(lines)}</ul>')
    out.append(f'<p>Read that in the other direction and it is a negotiating fact: '
               f'a move from {esc(lo_n)} to {esc(hi_n)} at the same grade is not a '
               f'raise, whatever the offer letter says.</p>')
    return "\n".join(out)


def _ceiling(sa, sb, la, lb, cap, money, esc, year) -> str:
    """Где ступени перестают приносить деньги раньше."""
    ca = sum(1 for st in la["grades"].values() for c in st.values() if c["capped"])
    cb = sum(1 for st in lb["grades"].values() for c in st.values() if c["capped"])
    if not (ca or cb):
        return (f'<h2>Neither area runs into the ceiling</h2>'
                f'<p>No General Schedule rate may exceed Level IV of the Executive '
                f'Schedule, {money(cap)} in {year}. In both of these areas every '
                f'cell of the table stays below it, so every step increase is worth '
                f'its full face value all the way to GS-15 step 10. That is not true '
                f'of the highest-paying localities.</p>')
    more, fewer = (sa, sb) if ca > cb else (sb, sa)
    n_more, n_few = max(ca, cb), min(ca, cb)
    out = ['<h2>Where raises stop counting</h2>']
    out.append(f'<p>No General Schedule rate may exceed Level IV of the Executive '
               f'Schedule, {money(cap)} in {year}. Inside that band a step increase '
               f'produces a bigger number in the formula, the law cuts it back, and '
               f'the payslip does not move.</p>')
    if n_few:
        out.append(f'<p>{esc(more)} has <strong>{n_more} of its 150 cells</strong> '
                   f'pinned to the ceiling; {esc(fewer)} has {n_few}. The '
                   f'higher-paying area runs out of room first, which matters more '
                   f'over a career than the difference in any single year.</p>')
    else:
        out.append(f'<p>{esc(more)} has <strong>{n_more} of its 150 cells</strong> '
                   f'pinned to the ceiling. {esc(fewer)} has none: every step '
                   f'increase there is worth its full face value. Over a career at '
                   f'the top grades that reverses part of the headline gap.</p>')
    return "\n".join(out)


def _places(sa, sb, na, nb, pa, pb, money, esc, slug) -> str:
    """Что каждая зона покрывает, и ссылки на полные таблицы."""
    ca = len([p for p in pa.get("places", []) if p["kind"] == "county"])
    cb = len([p for p in pb.get("places", []) if p["kind"] == "county"])
    out = []

    # Rest of U.S. — не «прочее», а зона, определённая исключением, и на
    # страницах сравнения с ней это ровно та часть, которой не хватает: у неё
    # нет ни городов, ни округов, потому что она — всё остальное.
    if na.startswith("Rest of") or nb.startswith("Rest of"):
        other = sb if na.startswith("Rest of") else sa
        out.append('<h2>What Rest of U.S. actually means</h2>')
        out.append('<p>Rest of U.S. is not a place and not a leftover category for '
                   'small towns. It is the rate that applies to every federal duty '
                   'station in the country that does not sit inside one of the 57 '
                   'named locality pay areas \u2014 and that includes plenty of '
                   'substantial cities. Being a metropolitan area is not the test. '
                   'Being a <em>named</em> locality pay area is, and the list is '
                   'decided by the Federal Salary Council and the President, not by '
                   'population.</p>')
        out.append('<p>It is also the floor of the whole system: the lowest '
                   'adjustment there is, and the number every other locality is '
                   'measured against. When people talk about the size of locality '
                   'pay, this is the baseline they mean.</p>')
        out.append(f'<p>That makes this particular comparison the one people run '
                   f'most often, and usually in one direction: an offer in '
                   f'{esc(other)} against staying where you are. The salary '
                   f'difference is real. What the table above adds is how much of '
                   f'it survives contact with local prices \u2014 which is the '
                   f'part the offer letter does not mention.</p>')
        out.append('<p>One practical warning that applies only to this pairing. '
                   'Telework and remote arrangements do not automatically keep you '
                   'on the Rest of U.S. rate, and they do not automatically move '
                   'you onto a metropolitan one either. Locality follows the '
                   'official duty station recorded on your paperwork, which is a '
                   'question for your servicing HR office rather than for a '
                   'reference site.</p>')

    out.append('<h2>What each area covers</h2>')
    if ca and cb:
        out.append(f'<p>{esc(sa)} is the {esc(na)} locality pay area, {ca} counties. '
                   f'{esc(sb)} is the {esc(nb)} area{_dot(nb)} {cb} counties. Locality '
                   f'follows your <strong>duty station</strong>, not your home '
                   f'address and not your agency headquarters, so a house on the '
                   f'wrong side of a county line does not change the rate — '
                   f'the building you report to does.</p>')
    else:
        out.append(f'<p>{esc(sa)} is the {esc(na)} area; {esc(sb)} is the '
                   f'{esc(nb)} area{_dot(nb)} Locality follows your '
                   f'<strong>duty station</strong>, not your home address.</p>')
    out.append(f'<p>The full {esc(na)} table: '
               f'<a href="/locality/{slug(na)}/">every grade and step</a>. '
               f'The full {esc(nb)} table: '
               f'<a href="/locality/{slug(nb)}/">every grade and step</a>. '
               f'To put your own grade and step against either, use the '
               f'<a href="/calculator/">pay calculator</a>.</p>')
    return "\n".join(out)


def compare_index(items: list, shell, esc) -> str:
    """Указатель сравнений."""
    links = "".join(f'<li><a href="/{rel}/">{esc(t)}</a></li>' for rel, t in items)
    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li>Compare</li></ol>',
         '<h1>Compare two locality pay areas</h1>',
         '<p class="sub">Two job offers, or an offer and a transfer. These pages '
         'put the salaries side by side and then answer the question the salaries '
         'do not: which one leaves you better off once local prices are counted.</p>',
         '<p>The areas below are the highest-paying localities in the General '
         'Schedule, plus Rest of U.S. — the rate that applies to every duty '
         'station outside a named area, and the one people most often weigh a move '
         'against. Each page compares every grade at step 5, works out the grade in '
         'the cheaper area that matches the more expensive one, and shows which of '
         'the two runs into the statutory ceiling first.</p>',
         f'<ul class="chips-plain">{links}</ul>',
         '<h2>Why the bigger salary is not always the better offer</h2>',
         '<p>Locality pay is set from what private employers in the same region pay '
         'for comparable work. It is not a cost-of-living adjustment, and OPM says '
         'so plainly. Regions where private salaries are high tend also to be '
         'expensive, so the two move together — but not by the same amount, and '
         'not reliably. The gap between them is large enough to reverse the ranking '
         'of the highest-paying areas outright.</p>',
         '<p>That is what these pages measure. The salary comes from the published '
         'OPM table. The price level comes from the Bureau of Economic Analysis '
         'Regional Price Parities, where 100 is the national average. These pages '
         'show the index to one decimal place and compute from the published '
         'three, so recomputing from the printed figure lands a few dollars '
         'away. Dividing one '
         'by the other gives a figure that is comparable across the country: what '
         'the salary would have to be, at average U.S. prices, to buy the same '
         'things.</p>',
         '<p>Two cautions. The price index is published a year or more behind the '
         'pay tables, and metropolitan boundaries do not line up exactly with '
         'locality pay areas, so the nearest metropolitan area is used as the proxy. '
         'Where two areas land within one percent of each other, these pages say '
         'they are the same rather than pretending to a precision the data does not '
         'have.</p>',
         '<h2>What these pages deliberately leave out</h2>',
         '<p>State and local income tax is not modelled here, and for some of these '
         'pairs it is the single biggest remaining difference: Texas, Washington and '
         'Florida levy no state income tax, while California and New York do. '
         'Neither is housing tenure — the price index describes what things '
         'cost now, not what a mortgage signed a decade ago costs you. Nor is the '
         'value of being near the agency headquarters, which is a career fact rather '
         'than a pay fact.</p>',
         '<p>What these pages do is remove the one distortion that is both large and '
         'invisible on a pay table, and leave the rest to you.</p>',
         '<h2>How to read a pair</h2>',
         '<p>Start at the top. The first figure is the difference in purchasing '
         'power at GS-12 step 5, and the sentence under it says which way it '
         'points. Where the answer contradicts the salaries \u2014 the '
         'lower-paying area leaving you better off \u2014 the page says so '
         'outright, because that is the case worth knowing about and the one no '
         'pay table will ever show you.</p>',
         '<p>The exhibit below it repeats the comparison for all fifteen grades at '
         'step 5. The last column is the one to read: it is the difference in what '
         'the two salaries buy, not what they are. A positive number means the '
         'first area comes out ahead. Watch for the sign changing partway down the '
         'grades \u2014 it happens, and it means the better choice depends on the '
         'grade you are being offered.</p>',
         '<p>Then three sections that answer the questions that follow. The '
         'step-by-step table lets a step 3 offer in one area be read against a step '
         '7 offer in the other. The overtime section matters if overtime is a real '
         'part of the job, because the threshold at which it stops being paid at a '
         'premium is a local figure and differs between the two. And the '
         'equivalence section turns the comparison into a negotiating number: the '
         'grade you would have to reach in the cheaper area to match the more '
         'expensive one.</p>',
         '<h2>If your pair is not here</h2>',
         '<p>These pages cover the highest-paying localities, where most '
         'competitive offers are made, plus Rest of U.S. For any other combination, '
         'open either locality page: each one ranks its own area against all the '
         'others by purchasing power and names the neighbours immediately above and '
         'below it. The <a href=\"/calculator/\">pay calculator</a> will do the '
         'same for any grade, step and area, and will find your area from a ZIP '
         'code if you are not sure which one you are in.</p>']
    return shell("Compare GS Pay Between Localities",
                 "Two locality pay areas side by side: the salaries, and which one "
                 "leaves you better off once local prices are counted.",
                 "\n".join(B), "https://fedpayscale.com/compare/", "compare",
                 crumbs=[("All localities", "/"), ("Compare", None)])
