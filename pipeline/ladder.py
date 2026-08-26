"""Страницы «лестница грейдов»: что даёт повышение с одного грейда на следующий.

Зачем. «Сколько лет от GS-12 до GS-13» и «на какую ступень я попаду после
повышения» — сформированный вопросный спрос: подсказки Google выдают его для
всех соседних пар. При этом типа страницы под него нет НИ У ОДНОГО из проверенных
конкурентов. Они публикуют таблицы; на вопрос «что со мной будет» не отвечает
никто.

Что мы можем, чего не может таблица. Правило 5 CFR 531.214 (стандартный метод)
считается арифметически: прибавить две ступени текущего грейда, затем взять
низшую ступень нового грейда, не меньшую полученного. Данные у нас есть, значит
ответ можно дать точно, а не «зависит от обстоятельств».

И это вскрывает вещь, которую мало кто держит в голове: величина прибавки ПАДАЕТ
по мере роста ступени. Повышение с GS-12 ступени 1 даёт 14 462 доллара, с
ступени 10 — 614. Не потому, что повышение хуже, а потому что грейды
перекрываются: на десятой ступени вы уже почти зарабатываете как новичок
следующего грейда. Ценность повышения там не в сегодняшней прибавке, а в том,
что поднимается потолок.

Оговорка о точности. Считаем по БАЗОВОЙ таблице, как и делает сам стандартный
метод для обычного случая, а надбавку локалити применяем после. Существуют
исключения — спецставки, альтернативный метод, сохранённая ставка, — и страница
называет их вслух, а не делает вид, что их нет.
"""
from __future__ import annotations

import ads

# Адрес сайта живёт одной константой в render.py и подставляется
# сюда на старте сборки. Домен ещё не выбран, и он обязан
# меняться одной строкой, а не обходом шести файлов.
DOMAIN = ""

# 5 CFR 531.405: сроки до следующей ступени.
WAITS = [1, 1, 1, 2, 2, 2, 3, 3, 3]


def promo_step(base: dict, g: int, s: int) -> tuple:
    """Стандартный метод 5 CFR 531.214: (новая ступень, новая ставка, промежуточная).

    Две ступени текущего грейда, затем низшая ступень нового грейда, которая не
    меньше полученного. Выше десятой ступени не поднимаемся: её и не бывает.
    """
    cur = base[str(g)][str(s)]["annual"]
    bumped = base[str(g)][str(min(s + 2, 10))]["annual"]
    for ns in range(1, 11):
        if base[str(g + 1)][str(ns)]["annual"] >= bumped:
            return ns, base[str(g + 1)][str(ns)]["annual"], bumped, cur
    return 10, base[str(g + 1)]["10"]["annual"], bumped, cur


def ladder_page(g: int, T: dict, R: dict, ranks: dict, shell, esc, money, slug,
                rail: str = "") -> tuple:
    """Возвращает (относительный адрес, HTML) для пары g -> g+1."""
    year = T["year"]
    base = T["base"]["grades"]
    nxt = g + 1

    rows = []
    for s in range(1, 11):
        ns, newpay, bumped, cur = promo_step(base, g, s)
        rows.append({"s": s, "cur": cur, "ns": ns, "new": newpay,
                     "gain": newpay - cur})

    first, last = rows[0], rows[-1]
    top_g = base[str(g)]["10"]["annual"]
    top_n = base[str(nxt)]["10"]["annual"]
    years_to_top = sum(WAITS)

    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li><a href="/promotion/">Promotions</a></li>'
         f'<li>GS-{g} to GS-{nxt}</li></ol>']
    B.append(f'<h1>GS-{g} to GS-{nxt}: what the promotion is actually worth</h1>')
    B.append(f'<p class="sub">The step you land on is decided by a rule, not by '
             f'negotiation — and the raise it produces shrinks the longer you '
             f'wait. From step 1 the promotion adds {money(first["gain"])} to base '
             f'pay; from step 10 it adds {money(last["gain"])}.</p>')

    B.append(f'<div class="facts">'
             f'<div class="fact"><p class="fact-k">Minimum time in grade</p>'
             f'<span class="kpi">52 weeks</span>'
             f'<span class="kpi-sub">at GS-{g} before you are eligible for GS-{nxt}. '
             f'That is a legal minimum, not a schedule.</span></div>'
             f'<div class="fact"><p class="fact-k">Biggest jump</p>'
             f'<span class="kpi">{money(first["gain"])}</span>'
             f'<span class="kpi-sub">promoted from step 1, which lands you on '
             f'GS-{nxt} step {first["ns"]}.</span></div>'
             f'<div class="fact"><p class="fact-k">Smallest jump</p>'
             f'<span class="kpi">{money(last["gain"])}</span>'
             f'<span class="kpi-sub">promoted from step 10, which lands you on '
             f'GS-{nxt} step {last["ns"]}. The grades overlap.</span></div>'
             f'<div class="fact"><p class="fact-k">Ceiling raised by</p>'
             f'<span class="kpi">{money(top_n - top_g)}</span>'
             f'<span class="kpi-sub">GS-{nxt} step 10 against GS-{g} step 10. This '
             f'is where the value of a promotion actually sits.</span></div>'
             f'</div>')
    B.append(ads.slot("band"))

    # --- главная таблица
    body = "".join(
        f'<tr><th scope="row">Step {r["s"]}</th>'
        f'<td class="num">{r["cur"]:,}</td>'
        f'<td class="num">Step {r["ns"]}</td>'
        f'<td class="num">{r["new"]:,}</td>'
        f'<td class="num up">+{r["gain"]:,}</td></tr>' for r in rows)
    B.append(f'<section class="q" id="which-step">'
             f'<h2>Which step will I land on?</h2>'
             f'<p class="q-lead">There is a rule for this and it leaves nothing to '
             f'discretion. Find your current step on the left.</p>'
             f'<div class="scroll" tabindex="0" role="region" '
             f'aria-label="Scrollable table"><table><thead><tr>'
             f'<th>At GS-{g}</th><th class="num">Base rate now</th>'
             f'<th class="num">Becomes</th><th class="num">New base rate</th>'
             f'<th class="num">Base increase</th></tr></thead>'
             f'<tbody>{body}</tbody></table></div>'
             f'<p>These are <strong>base rates</strong>, before locality pay. Your '
             f'actual figures are these multiplied by your area’s percentage, '
             f'and the increase scales with it: in an area at 30% the numbers above '
             f'are roughly a third larger. The '
             f'<a href="/calculator/">calculator</a> will do it for your area.</p>'
             f'</section>')

    # Человек с ПЕРВЫМ оффером приходит сюда по запросу про ступень и читает
    # «вы не начинаете со ступени 1» — про повышение это верно, про его случай
    # прямо наоборот. Разводим два случая явным блоком, а не оговоркой.
    B.append('<aside class="caveat"><p><strong>Coming into federal service, '
             'not moving up inside it?</strong> Then this page is about '
             'somebody else. A first appointment is set at step 1 of the '
             'grade unless the agency uses the superior qualifications '
             'authority (5 U.S.C. 5333; 5 CFR 531.212). Everything below '
             'describes what happens to someone already on the General '
             'Schedule.</p></aside>')

    # --- как работает правило
    B.append(f'<section class="q" id="rule">'
             f'<h2>The rule behind it</h2>'
             f'<p class="q-lead">Two within-grade increases first, then the lowest '
             f'step in the new grade that matches.</p>'
             f'<p>Under 5 CFR 531.214 the standard method works in two moves. Your '
             f'current rate is raised by two within-grade increases of your '
             f'<em>current</em> grade — so a GS-{g} step 4 is first treated as '
             f'a GS-{g} step 6. Then the agency finds the lowest step of GS-{nxt} '
             f'that is at least that amount, and that is where you land.</p>'
             f'<p>Two consequences follow, and both surprise people. The first is '
             f'that you never land on step 1 unless you were near the bottom of the '
             f'old grade: promotion carries your position up with you. The second is '
             f'that the increase gets smaller the higher your step, because the two '
             f'grades overlap — at GS-{g} step 10 you are already earning close '
             f'to what GS-{nxt} pays in its lower steps.</p>'
             f'<p>Exceptions exist and matter. If a special rate table covers your '
             f'occupation, or if you are on a retained rate, or if the agency uses '
             f'the alternate method, the arithmetic changes. Your servicing human '
             f'resources office computes the official figure; this page tells you '
             f'what to expect and what to ask about.</p></section>')

    # --- время
    B.append(f'<section class="q" id="timing">'
             f'<h2>How long does it take?</h2>'
             f'<p class="q-lead">Fifty-two weeks at GS-{g} is the legal minimum. '
             f'Whether anything happens at fifty-three is a different question.</p>'
             f'<p>Time-in-grade is a floor, not a promise. On a career ladder — '
             f'a position advertised as GS-{g}/{nxt}, or with GS-{nxt} named as the '
             f'full performance level — promotion is non-competitive: once the '
             f'year is served and performance is acceptable, it happens. Off a '
             f'ladder, GS-{nxt} is a different position and you compete for it like '
             f'anyone else.</p>'
             f'<p>That distinction is worth more than any number on this page. Read '
             f'the vacancy announcement for the <strong>full performance '
             f'level</strong>: it tells you where the job actually ends up, and the '
             f'entry grade is temporary by design.</p>'
             f'<p>Promotion also resets the step clock. Whatever time you had '
             f'accumulated toward your next within-grade increase at GS-{g} is gone; '
             f'the wait starts again at your new step. A promotion arriving a month '
             f'before a step increase was due is therefore worth less in the first '
             f'year than it looks — you get the promotion increase but lose the '
             f'step increase you had almost earned.</p></section>')

    # --- почему потолок важнее прибавки
    gap_top = top_n - top_g
    B.append(f'<section class="q" id="ceiling">'
             f'<h2>Why the ceiling matters more than the raise</h2>'
             f'<p class="q-lead">From step 10 the promotion adds '
             f'{money(last["gain"])} today and {money(gap_top)} to where you can '
             f'eventually get.</p>'
             f'<p>GS-{g} tops out at {money(top_g)} in base pay. GS-{nxt} tops out at '
             f'{money(top_n)}. Someone promoted late in the grade sees almost nothing '
             f'in the first paycheck and a great deal over the following years, '
             f'because every remaining step increase is now being earned on the '
             f'higher schedule.</p>'
             f'<p>From step 1 the arithmetic is the opposite: {money(first["gain"])} '
             f'arrives immediately. Neither is better in general. Which one you are '
             f'looking at depends on where you are in the grade, and it is worth '
             f'knowing before you read a promotion offer as a disappointment.</p>'
             f'<p>Reaching step 10 from step 1 takes {years_to_top} years at one '
             f'grade, so in practice most people are promoted somewhere in the '
             f'middle and see something in between.</p></section>')

    # --- что это значит в дорогих зонах
    top_areas = sorted(T["localities"].items(),
                       key=lambda kv: -kv[1]["grades"][str(nxt)]["5"]["annual"])[:5]
    bits = []
    for code, loc in top_areas:
        a = loc["grades"][str(g)]["5"]["annual"]
        b = loc["grades"][str(nxt)]["5"]["annual"]
        bits.append(f'<tr><th scope="row">'
                    f'<a href="/locality/{slug(loc["area_name"])}/">'
                    f'{esc(loc["area_name"])}</a></th>'
                    f'<td class="num">{loc["locality_pct"]:g}%</td>'
                    f'<td class="num">{a:,}</td><td class="num">{b:,}</td>'
                    f'<td class="num up">+{b - a:,}</td></tr>')
    B.append(f'<section class="q" id="where">'
             f'<h2>What it is worth where the rates are highest</h2>'
             f'<p class="q-lead">The same promotion is worth more in a '
             f'high-percentage area, because the percentage multiplies the gap as '
             f'well as the salary. Step 5 to step 5, for comparison.</p>'
             f'<div class="scroll" tabindex="0" role="region" '
             f'aria-label="Scrollable table"><table><thead><tr>'
             f'<th>Locality pay area</th><th class="num">Locality pay</th>'
             f'<th class="num">GS-{g} step 5</th><th class="num">GS-{nxt} step 5</th>'
             f'<th class="num">Difference</th></tr></thead>'
             f'<tbody>{"".join(bits)}</tbody></table></div>'
             f'<p>That is the figure on the payslip, not the figure in your pocket. '
             f'The areas paying the most are frequently the areas where things cost '
             f'the most, and our <a href="/">national ranking</a> sorts every area '
             f'by what the salary actually buys rather than by its size. On that '
             f'measure the order changes considerably.</p></section>')

    title = f"GS-{g} to GS-{nxt} Promotion: Step, Raise and Timing"
    # Влезать обязано при ЛЮБОМ грейде: суммы растут с грейдом, и описание,
    # подобранное на удачном, вылезало за 160 знаков на двенадцати из
    # четырнадцати страниц.
    desc = (f"GS-{g} to GS-{nxt}: which step you land on, and what the promotion "
            f"is worth. From step 1 it adds {money(first['gain'])} to base pay; "
            f"from step 10, {money(last['gain'])}.")
    rel = f"promotion/gs-{g}-to-gs-{nxt}"
    return rel, shell(
        title, desc, "\n".join(B), f"{DOMAIN}/{rel}/", "promotion",
        crumbs=[("All localities", "/"), ("Promotions", "/promotion/"),
                (f"GS-{g} to GS-{nxt}", None)],
        rail=rail)


def ladder_index(items: list, T: dict, shell, esc, money) -> str:
    """Указатель по всем парам."""
    base = T["base"]["grades"]
    links = "".join(f'<li><a href="/{rel}/">{esc(t)}</a></li>' for rel, t in items)

    sample = []
    for g in (7, 9, 11, 12, 13):
        ns, newpay, _, cur = promo_step(base, g, 1)
        _, lastpay, _, lastcur = promo_step(base, g, 10)
        sample.append(f'<tr><th scope="row">GS-{g} to GS-{g + 1}</th>'
                      f'<td class="num up">+{newpay - cur:,}</td>'
                      f'<td class="num">+{lastpay - lastcur:,}</td>'
                      f'<td class="num">{base[str(g + 1)]["10"]["annual"] - base[str(g)]["10"]["annual"]:,}</td></tr>')

    B = ['<ol class="crumbs"><li><a href="/">All localities</a></li>'
         '<li>Promotions</li></ol>',
         '<h1>What a General Schedule promotion is worth</h1>',
         '<p class="sub">The step you land on after a promotion is decided by a '
         'rule, and the raise it produces is smaller the longer you waited. These '
         'pages work out both, for every pair of adjacent grades.</p>',
         f'<div class="chips">{links}</div>',

         '<section class="q"><h2>The short version</h2>',
         '<p class="q-lead">Two within-grade increases of your current grade, then '
         'the lowest step of the new grade that matches or exceeds it.</p>',
         '<p>That is the standard method under 5 CFR 531.214, and it explains the '
         'two things people find surprising about promotion pay. You do not restart '
         'at step 1 — your position in the old grade carries over. And the '
         'increase shrinks as your step rises, because adjacent grades overlap: near '
         'the top of one grade you are already earning what the next grade pays near '
         'its bottom.</p>',
         f'<div class="scroll" tabindex="0" role="region" '
         f'aria-label="Scrollable table"><table><thead><tr><th>Promotion</th>'
         f'<th class="num">From step 1</th><th class="num">From step 10</th>'
         f'<th class="num">Ceiling raised by</th></tr></thead>'
         f'<tbody>{"".join(sample)}</tbody></table></div>',
         '<p>All figures are base rates before locality pay. In an area paying 30% '
         'above base every number is roughly a third larger, and the '
         '<a href="/calculator/">calculator</a> will do it for a specific '
         'area.</p></section>',

         '<section class="q"><h2>Time in grade is a floor, not a schedule</h2>',
         '<p class="q-lead">Fifty-two weeks at the next-lower grade makes you '
         'eligible. It does not make anything happen.</p>',
         '<p>On a career ladder the promotion is non-competitive: the position was '
         'advertised with a full performance level above your entry grade, and once '
         'the year is served and performance is acceptable you move up. Off a '
         'ladder, the higher grade is a separate position and you compete for it.</p>',
         '<p>The number to look for in a vacancy announcement is therefore the full '
         'performance level, not the grade being filled. The entry grade is '
         'temporary by design; the full performance level is where the job settles, '
         'and it is the figure worth comparing between offers.</p>',
         '<p>One more thing that catches people: promotion resets the waiting period '
         'for your next within-grade increase. Time accumulated toward the next step '
         'is lost. A promotion landing a month before a step increase was due is '
         'worth less in that first year than it appears.</p></section>',

         '<section class="q"><h2>Where this stops applying</h2>',
         '<p class="q-lead">Special rates, retained rates and the alternate method '
         'all change the arithmetic.</p>',
         '<p>Where a special rate table covers your occupation and location, the '
         'promotion is computed against the higher of the special and locality rate '
         'ranges, and the result can differ from the figures here. Employees on a '
         'retained rate are a separate case again. Agencies may also use the '
         'alternate method under the same regulation, which produces a different '
         'result in some situations.</p>',
         '<p>Your servicing human resources office computes the official figure and '
         'is the authority on it. What these pages give you is the expectation to '
         'walk in with, and the vocabulary to ask about it — which is more than '
         'a pay table on its own will do.</p></section>',

         '<section class="q"><h2>Two grades at once, and why it happens</h2>',
         '<p class="q-lead">Some ladders skip a grade: GS-7 to GS-9 to GS-11 rather '
         'than every step of the way.</p>',
         '<p>Professional and administrative positions frequently advance in '
         'two-grade intervals, because the work changes substantially between one '
         'level and the next rather than incrementally. Where that applies, the same '
         'rule still governs the landing step — two within-grade increases '
         'first, then the lowest matching step — but it is applied against the '
         'grade two levels up, and the resulting jump is correspondingly larger.</p>',
         '<p>Whether your occupational series advances in one-grade or two-grade '
         'intervals is set by the qualification standard for that series, not by '
         'your agency. It is worth knowing which one you are on before you count '
         'years: on a two-grade ladder the same span of time covers more '
         'ground.</p></section>',

         '<section class="q"><h2>What a promotion does not change</h2>',
         '<p class="q-lead">The statutory ceiling, and the arithmetic of local '
         'prices.</p>',
         '<p>No General Schedule rate may exceed Level IV of the Executive Schedule. '
         'In the highest-paying localities that ceiling is reached inside the '
         'published table, and a promotion into the affected band produces a '
         'smaller increase than the base figures suggest — sometimes none at '
         'all. Each locality page marks exactly which of its 150 cells are '
         'affected.</p>',
         '<p>And a promotion does not move you to a different place. If you are '
         'weighing a promotion against a transfer, the two are not comparable on '
         'salary alone: a higher grade in an expensive area can leave you worse off '
         'than the grade you have in a cheaper one. That comparison is what the '
         '<a href="/compare/">area pages</a> are for.</p></section>']
    return shell("GS Promotion Pay: Which Step You Land On",
                 "What a promotion between General Schedule grades is worth, which "
                 "step you land on, and why the raise shrinks the longer you wait.",
                 "\n".join(B), f"{DOMAIN}/promotion/", "promotion",
                 crumbs=[("All localities", "/"), ("Promotions", None)])
