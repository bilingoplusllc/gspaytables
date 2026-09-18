"""Страница про следующую прибавку. Адрес ВЕЧНОЗЕЛЁНЫЙ: /pay-raise/.

Почему без года в адресе. Замер аудита: «gs pay scale 2025» держался на 25–34
пункта Trends весь год, а к августу 2026 упал до 1. Страница с годом в слаге
умирает вместе с годом. Вечнозелёный адрес накапливает вес: меняются заголовок
и данные, адрес остаётся.

Почему страница вообще есть. Замер спроса: «gs pay scale 2026» шёл на 8 пунктах
в начале ноября, 23 через неделю, 100 к середине декабря. К пику ранжирование
уже решено, поэтому страница должна стоять в индексе к 1 октября.

Что показала конкурентная разведка 26.08.2026:
  * у лидера ниши federalpay.org страницы про 2027 НЕТ вообще: /gs/2027 отдаёт
    404, а в его истории повышений последняя строка — 2026;
  * топ-10 по «2027 federal pay raise» занят новостями, профсоюзами и Reddit —
    справочников там нет;
  * Google по запросу «federal pay raise 2027 chart with locality» сам пишет
    «Missing: chart». Разреза по зонам не даёт НИКТО, а спрос на него
    подтверждён подсказками «People also search for».

Отсюда устройство страницы: не прогноз числа, а ЧЕСТНЫЙ СТАТУС плюс механика,
плюс единственный вопрос, на который при нулевом сценарии не отвечает никто, —
«изменится ли что-нибудь в январе, если прибавка нулевая».

ДАТА ПРОВЕРКИ СТАВИТСЯ РУКАМИ. Не date.today(): ежемесячная пересборка не ходит
на whitehouse.gov и не знает, отправлено ли письмо. Автоматическая дата означала
бы, что страница сама себе выписывает свежесть, которой не проверяла, — ровно
тот класс ошибки, который в этом проекте уже стоил дня работы. Гейт в render.py
роняет сборку, если дата старше срока: это заставляет перепроверить.
"""
from __future__ import annotations

from datetime import date

# --- ЧТО ПРОВЕРЕНО И КОГДА -------------------------------------------------
# Ставится руками после фактической проверки whitehouse.gov, Federal Register и
# govinfo. Меняя дату, ОБЯЗАТЕЛЬНО перечитай STATUS ниже.
CHECKED = date(2026, 9, 9)

# Сколько дней статус считается годным. За этим порогом сборка краснеет.
# 40 дней выбраны так, чтобы срок письма (31 августа) и выход указа (18–23
# декабря) не могли пройти незамеченными между двумя ежемесячными прогонами.
STALE_AFTER_DAYS = 40

# Год, о прибавке на который идёт речь: следующий после года издания.
# Выводится, а не пишется литералом.

# --- ЧТО СЛУЧИЛОСЬ РАНЬШЕ. Каждая строка — из первоисточника. --------------
# (год, база %, локалити %, итого %, дата письма, указ, дата указа)
HISTORY = [
    (2023, "4.1", "0.5", "4.6", "31 August 2022", "EO 14090", "23 December 2022"),
    (2024, "4.7", "0.5", "5.2", "31 August 2023", "EO 14113", "21 December 2023"),
    (2025, "1.7", "0.3", "2.0", "30 August 2024", "EO 14132", "23 December 2024"),
    (2026, "1.0", "0", "1.0", "28 August 2025", "EO 14368", "18 December 2025"),
]

# --- ЧТО ПРЕДЛОЖЕНО, НО ЕЩЁ НЕ СТАЛО ЗАКОНОМ ------------------------------
#
# Ключ — ГОД, НА КОТОРЫЙ письмо устанавливает ставки. Это не украшение
# структуры, а единственная защита от того, чтобы страница выдумывала
# события: год издания переворачивается 1 января сам, и всё, что набрано
# прозой через {year}, на следующем цикле становится ложным утверждением о
# президентском письме. Нет записи — нет утверждения.
#
# Сюда попадает цикл, письмо по которому УЖЕ ушло, а указа ещё нет. В день
# подписания указа строка переезжает в HISTORY, и запись отсюда убирается:
# «предложено» и «в силе» — разные состояния, и одновременно верными они не
# бывают.
PROPOSED = {
    2027: {
        # Письмо ушло 26.08.2026, за пять дней до установленного законом
        # срока 1 сентября. В день запуска сайта, через несколько часов
        # после ручной проверки — страница простояла с «пока не решено»
        # пятнадцать суток, и переходы за эти сутки упали с 29 до 2.
        "letter": "26 August 2026",
        "doc": "House Document 119-87",
        "base": "0",
        "locality": "0",
        "leo": "3.8",
        "why": "fiscal",
    },
}


SOURCES = [
    ("5 U.S.C. 5303 — the annual adjustment and the alternative plan",
     "https://www.govinfo.gov/content/pkg/USCODE-2023-title5/html/"
     "USCODE-2023-title5-partIII-subpartD-chap53-subchapI-sec5303.htm"),
    ("5 U.S.C. 5304a — the alternative level of locality pay",
     "https://www.govinfo.gov/content/pkg/USCODE-2023-title5/html/"
     "USCODE-2023-title5-partIII-subpartD-chap53-subchapI-sec5304a.htm"),
    ("The 2026 alternative pay plan letter (House Document 119-87)",
     "https://www.govinfo.gov/content/pkg/CDOC-119hdoc87/html/CDOC-119hdoc87.htm"),
    ("Executive Order 14368, the 2026 pay schedules",
     "https://www.federalregister.gov/documents/2025/12/23/2025-23844/"
     "adjustments-of-certain-rates-of-pay"),
    ("Executive Order 13866 — the 2019 raise, signed in March, backdated",
     "https://www.federalregister.gov/documents/2019/04/02/2019-06548/"
     "adjustments-of-certain-rates-of-pay"),
    ("5 CFR 531.405 — waiting periods for step increases",
     "https://www.law.cornell.edu/cfr/text/5/531.405"),
    ("OPM's own memo on the 2026 adjustments",
     "https://www.opm.gov/chcoc/latest-memos/january-2026-pay-adjustments.pdf"),
    ("OPM salary tables — where the official numbers appear",
     "https://www.opm.gov/policy-data-oversight/pay-leave/salaries-wages/"),
]


# КАЛЕНДАРЬ СОБЫТИЙ, а не счётчик дней.
#
# Гейт свежести считал дни от ручной проверки и краснел через сорок. Этого
# оказалось мало и по существу неверно: письмо об альтернативном плане ушло
# 26 августа 2026 — в ТОТ ЖЕ день, когда проверяли, — и страница простояла с
# «Status: not decided» пятнадцать суток. Сорокадневный порог не наступил бы
# до 5 октября, а вопрос года был решён 26 августа.
#
# Страница сама печатала даты, когда письма приходили в прошлые годы: 31.08.2022,
# 31.08.2023, 30.08.2024, 28.08.2025. Она предсказала день своего протухания и
# всё равно протухла, потому что будильник считал не то.
#
# Теперь гейт краснеет, когда МЕЖДУ проверкой и сегодняшним днём прошло
# календарное событие, меняющее ответ.
EVENTS = [
    (date(2026, 9, 1), "крайний срок письма об альтернативном плане на 2027"),
    (date(2026, 12, 1), "отчёт Федерального совета по окладам, 5 U.S.C. 5304a"),
    (date(2026, 12, 18), "окно подписания указа о ставках 2027 (18–23 декабря)"),
    (date(2027, 1, 11), "дата вступления ставок 2027 в силу"),
    (date(2027, 9, 1), "крайний срок письма об альтернативном плане на 2028"),
]


def missed_events(today: date | None = None) -> list:
    """События, которые прошли ПОСЛЕ последней проверки. Пустой список —
    ответ на странице всё ещё может быть верным."""
    now = today or date.today()
    return [(d_, why) for d_, why in EVENTS if CHECKED < d_ <= now]


def stale_days(today: date | None = None) -> int:
    """Сколько дней прошло с последней ручной проверки статуса."""
    return ((today or date.today()) - CHECKED).days


def eo_window() -> str:
    """Окно подписания указа — ПОСЧИТАНО по истории, а не вспомнено.

    «Между 18 и 23 декабря» стояло в прозе числом. Числа в прозе, которые
    никто не пересчитывает, живут своей жизнью: добавится год с указом от
    27 декабря — и фраза станет ложной, ничего об этом не сказав.
    """
    days = []
    for row in HISTORY:
        d = row[6].split()
        if len(d) == 3 and d[1] == "December":
            days.append(int(d[0]))
    if not days:
        raise RuntimeError("в истории нет ни одного декабрьского указа — "
                           "окно считать не из чего")
    lo, hi = min(days), max(days)
    return f"{lo} and {hi} December" if lo != hi else f"{lo} December"


def page(T: dict, shell, money) -> str:
    year = int(T["year"])
    nxt = year + 1
    checked = CHECKED.strftime("%d %B %Y").lstrip("0")
    # Цикл, о котором идёт речь. None — значит письма по нему ещё не было, и
    # страница обязана это СКАЗАТЬ, а не пересказать прошлогоднее.
    prop = PROPOSED.get(nxt)
    window = eo_window()
    in_force = next((r for r in HISTORY if r[0] == year), None)
    if in_force is None:
        raise RuntimeError(
            f"в HISTORY нет года {year}, а страница обязана назвать, что "
            f"действует СЕЙЧАС: без этой строки она пересказала бы чужой год")

    B = [f'<h1>The {nxt} federal pay raise</h1>']
    B.append(f'<p class="sub">What has been decided, what has not, and the date '
             f'each answer arrives. Checked {checked}.</p>')

    # ---- ответ первым экраном, без единого клика и без скрипта
    # Карточка .answer здесь НЕ используется: она рисует собственную тяжёлую
    # линейку сверху, а прямо над ней уже стоит издательская линейка титула —
    # получались две подряд с пустотой между ними. Карточка рассчитана на
    # место ПОСЛЕ текста, а не сразу под заголовком страницы.
    # 26 августа 2026 письмо ушло — в день запуска сайта, через несколько
    # часов после ручной проверки. Страница простояла с «Status: not decided»
    # пятнадцать суток, и ровно в эти сутки переходы упали с 29 до 2: вопрос
    # года получил ответ, а мы продолжали отвечать «пока неизвестно».
    B.append('<p class="q-lead">')
    if prop:
        _frozen = prop["base"] == "0" and prop["locality"] == "0"
        _head = ("a freeze" if _frozen
                 else f'base pay up {prop["base"]} percent')
        B.append(f'<strong>Proposed: {_head}.</strong> On {prop["letter"]} the '
                 f'President sent Congress the alternative pay plan letter for '
                 f'{nxt}. It holds base pay and locality pay for civilian '
                 f'federal employees at their {year} rates — a zero-percent '
                 f'year — and gives law enforcement {prop["leo"]} percent. '
                 f'Nothing is binding until an executive order is signed, '
                 f'which for the last {len(HISTORY)} years has happened '
                 f'between {window}. The alternative plan is usually what the '
                 f'order adopts, but it is a proposal until then.</p>'
                 if _frozen else
                 f'<strong>Proposed: {_head}.</strong> On {prop["letter"]} the '
                 f'President sent Congress the alternative pay plan letter for '
                 f'{nxt}: base pay {prop["base"]} percent, locality pay '
                 f'{prop["locality"]} percent, and {prop["leo"]} percent for '
                 f'law enforcement. Nothing is binding until an executive '
                 f'order is signed, which for the last {len(HISTORY)} years '
                 f'has happened between {window}.</p>')
    else:
        # ЧЕСТНАЯ ВЕТКА. Раньше её не было вовсе, и на следующем цикле
        # страница пересказывала прошлогоднее письмо с подставленным годом —
        # то есть сообщала о событии, которого не было. Теперь она говорит
        # ровно то, что известно: чего ещё не произошло и когда произойдёт.
        B.append(f'<strong>Not announced yet.</strong> The alternative pay '
                 f'plan letter for {nxt} has not been sent. By law the '
                 f'President has until 31 August {year} to send it, and in '
                 f'each of the last {len(HISTORY)} years the letter arrived '
                 f'within the last days of August. Until it does, nothing '
                 f'about {nxt} pay is announced — and anything published '
                 f'elsewhere as the {nxt} table is a forecast, not a rate. '
                 f'The binding step comes later still: an executive order, '
                 f'signed between {window}.</p>')
    # Это и есть то, чего нет ни у кого: при заморозке таблицы следующего года
    # ИЗВЕСТНЫ уже сейчас, потому что они равны нынешним.
    if prop and prop["base"] == "0" and prop["locality"] == "0":
        B.append('<div class="caveat">')
        B.append(f'<p><strong>If the freeze holds, the {nxt} tables are '
                 f'already known: they are the {year} tables.</strong> Base '
                 f'rates and all 58 locality percentages stay where they are. '
                 f'Every number on this site is therefore also the {nxt} '
                 f'number, unless the December order says otherwise.</p>')
        B.append('</div>')

    # ТАБЛИЦА СЛЕДУЮЩЕГО ГОДА, а не рассуждение о ней.
    #
    # Запрос «2027 gs pay scale» идёт вверх с ноября к середине декабря, и
    # отвечать на него сегодня некому: конкуренты публикуют «оценку», а у нас
    # при объявленной заморозке никакой оценки не нужно — предложенная
    # таблица 2027 года ЕСТЬ таблица 2026 года, число в число. Это и есть
    # ответ, которого ни у кого нет, и он не требует ни одного нового замера.
    #
    # Слово «proposed» стоит в заголовке таблицы и в подписи под ней: пока
    # указ не подписан, это предложение, и печатать его как закон нельзя.
    grades = T['base']['grades']
    rows = ''
    for g in sorted(grades, key=int):
        s = grades[g]
        rows += (f'<tr><th>GS-{g}</th>'
                 f'<td class="num">{money(s["1"]["annual"])}</td>'
                 f'<td class="num">{money(s["5"]["annual"])}</td>'
                 f'<td class="num">{money(s["10"]["annual"])}</td></tr>')
    B.append(f'<h2>The {nxt} GS base table, as proposed</h2>')
    B.append(f'<p>Because the alternative pay plan holds rates where they are, the {nxt} base table is the {year} base table. These are the rates before locality pay; your own figure is base plus your area percentage, and the <a href="/calculator/">calculator</a> does that for you.</p>')
    B.append('<div class="scroll" tabindex="0" role="region" aria-label="Scrollable table"><table>')
    B.append(f'<caption>General Schedule base rates, {nxt} as proposed &mdash; identical to {year}</caption>')
    B.append('<thead><tr><th>Grade</th><th class="num">Step 1</th>'
             '<th class="num">Step 5</th><th class="num">Step 10</th></tr></thead>')
    B.append(f'<tbody>{rows}</tbody></table></div>')
    B.append(f'<p class="ex-note">Proposed, not law. The executive order '
             f'signed between {window} is what sets {nxt} rates; until then '
             f'this table is what the alternative pay plan asks for. Law '
             f'enforcement is the one group the letter treats differently, at '
             f'{prop["leo"]} percent. Locality percentages are unchanged too, '
             f'so every locality page on this site also holds for {nxt} under '
             f'the proposal.</p>')

    # ---- три статуса, которые все смешивают
    B.append('<h2>Three different things get called "the raise"</h2>')
    B.append('<p>Most of the confusion in this subject comes from mixing three '
             'states that look alike in a headline and are not alike at all. '
             'Here is where each one stands.</p>')

    B.append('<figure class="ex">')
    B.append('<p class="ex-kicker">In force</p>')
    # ЧТО ДЕЙСТВУЕТ СЕЙЧАС — из строки истории за этот год, а не из памяти.
    # Здесь стояли «1.0 percent» и «Executive Order 14368, signed 18 December»
    # прозой: на следующем цикле год подставлялся, а номер указа и процент
    # оставались прошлогодними, и страница приписывала новому году чужой указ.
    _y, _base, _loc, _tot, _letter, _eo, _eod = in_force
    _locpart = ("locality frozen" if _loc == "0"
                else f"locality up {_loc} percent")
    B.append(f'<p class="ex-title">{year}: base pay up {_base} percent, '
             f'{_locpart}</p>')
    B.append(f'<p class="ex-note">Executive Order {_eo.replace("EO ", "")}, '
             f'signed {_eod}. Base rates rose {_base} percent; locality '
             f'percentages '
             + (f'were held at their {year - 1} levels' if _loc == "0"
                else f'rose {_loc} percent')
             + f'. The rates took effect on the first day of the first pay '
             f'period beginning on or after 1 January {year} — 11 January '
             f'{year} in practice. These are the numbers on this site, and '
             f'they are the only ones that are law.</p>')
    B.append('</figure>')

    B.append('<figure class="ex">')
    B.append('<p class="ex-kicker">Announced</p>')
    if prop:
        B.append(f'<p class="ex-title">{nxt}: base and locality frozen at '
                 f'{year} rates, {prop["leo"]} percent for law '
                 f'enforcement</p>')
        B.append(f'<p class="ex-note">The alternative pay plan letter went to '
                 f'Congress on {prop["letter"]}, before the 1 September '
                 f'deadline. The President may set aside the statutory formula '
                 f'this way, and every President has used that power every '
                 f'year since 1994. The letter says base pay and locality pay '
                 f'for civilian employees will not change from {year} rates; '
                 f'the stated reason is {prop["why"]}. Law enforcement is the '
                 f'single exception at {prop["leo"]} percent. Announced is not '
                 f'in force: the December executive order is what makes rates '
                 f'law.</p>')
    else:
        B.append(f'<p class="ex-title">{nxt}: nothing announced</p>')
        B.append(f'<p class="ex-note">No alternative pay plan letter for '
                 f'{nxt} has been sent to Congress, and no executive order '
                 f'has been signed. This row will name both the day the '
                 f'letter arrives. Until then there is nothing here to '
                 f'report, and a page that reported something would be '
                 f'reporting an event that has not happened.</p>')
    B.append('</figure>')

    B.append('<figure class="ex">')
    B.append('<p class="ex-kicker">Proposed</p>')
    B.append(f'<p class="ex-title">{nxt}: a budget with no civilian raise, and a '
             f'bill that has not moved</p>')
    B.append('<p class="ex-note">The budget request published on 3 April 2026 '
             'contains no pay raise for civilian federal employees. Its only pay '
             'proposal is military: 7 percent for E-5 and below, 6 percent '
             'through O-3, 5 percent above that. Separately, the FAIR Act '
             '(H.R. 7480 and S. 3823, both introduced 10 February 2026) would '
             'give 3.1 percent to base pay and about 1 percent to locality. Both '
             'bills are sitting in committee. A budget request is a request and '
             'a bill is a bill; neither changes anyone’s pay.</p>')
    B.append('</figure>')

    # ---- ГЛАВНЫЙ ВОПРОС ЧИТАТЕЛЯ, на который не отвечает ни один конкурент
    B.append('<h2>If the raise is zero, does anything change in January?</h2>')
    B.append('<p>For most people, yes — and this is the part that gets lost every '
             'time the word <em>freeze</em> appears in a headline. The annual '
             'adjustment moves the table. A step increase moves you down the '
             'table you are already on. They are separate authorities, and a '
             'freeze on one is not a freeze on the other.</p>')
    B.append('<p>Step increases run on time served, not on the calendar year: '
             '52 weeks of creditable service to reach steps 2, 3 and 4, then '
             '104 weeks for steps 5, 6 and 7, then 156 weeks for steps 8, 9 and '
             '10, with performance at an acceptable level (5 CFR 531.405). When '
             'pay was frozen for 2011 and 2012, what froze was the table: OPM '
             'published it under the heading <em>rates frozen at 2010 levels</em>. '
             'Movement within the table is a different action entirely.</p>')

    B.append('<div class="caveat">')
    B.append('<p>The exception is real and worth naming: if you are already at '
             'step 10 of your grade, there is nowhere left to move. For you a '
             'zero-percent year is exactly zero until you change grade. That is '
             'also the group for whom a promotion is worth the least — the jump '
             'from step 10 is the smallest one on the ladder.</p>')
    B.append('</div>')

    B.append(f'<p>What a promotion is actually worth at your grade and step is '
             f'set out on the <a href="/promotion/">promotion pages</a>, and '
             f'what your current cell pays in your area is on the '
             f'<a href="/calculator/">calculator</a>.</p>')

    # ---- механика: что даёт формула
    B.append('<h2>What the formula gives if nobody intervenes</h2>')
    B.append('<p>There is a statutory default, and it is not a guess. Base pay '
             'rises by the increase in the Employment Cost Index — wages and '
             'salaries, private industry workers — for the twelve months ending '
             'in September, less half a percentage point, rounded to a tenth '
             '(5 U.S.C. 5303(a)). The measurement window closes fifteen months '
             'before the money moves, so the input is already known.</p>')
    B.append(f'<p>For January {nxt} the window is September 2024 to September '
             f'2025. The Bureau of Labor Statistics reported an increase of '
             f'3.6 percent. Subtract half a point and the formula gives '
             f'<strong>3.1 percent</strong> for base pay. The same arithmetic '
             f'applied to the previous cycle gives the figure the Federal Salary '
             f'Council itself published for {year}: an ECI of 3.8 percent, a base '
             f'increase of 3.3 percent.</p>')
    B.append('<p>That is what the formula produces, not what anyone has decided. '
             'It has been set aside every year since 1994, which is why the '
             'letter matters more than the arithmetic.</p>')
    B.append('<p>Locality is not a formula in the same sense. The law asks it to '
             'close the gap between federal and non-federal pay in each labor '
             'market down to a residual 5 percent, and it never has: on the last '
             'published measurement the gap was 56.57 percent, closing it would '
             'have taken 49.11 percent, and what was actually paid was 25.54 '
             'percent. There is no published figure for what full locality would '
             'cost in ' + str(nxt) + '. For ' + str(year) + ' the President’s '
             'own letter put it at an average of 18.88 percent and 24 billion '
             'dollars in the first year — which is the plainest available '
             'statement of why the formula keeps getting set aside.</p>')

    # ---- почему база и локалити не одно и то же
    B.append('<h2>Base and locality are two levers, not one</h2>')
    B.append('<p>Locality is a percentage applied to base pay, so the two '
             'interact in a way that catches people out. A frozen locality '
             'percentage does not mean frozen locality dollars — if base pay '
             'rises, the same percentage pays more. And the reverse: a frozen '
             'base freezes the locality dollars too, however generous the '
             'percentage looks. In ' + str(year) + ' base pay rose 1.0 percent '
             'and locality percentages did not move, so every locality payment '
             'in the country rose by exactly 1.0 percent and not a cent more.</p>')
    B.append('<p>The clearest proof of that is printed on the tables themselves. '
             'The area with the highest locality percentage in the country and '
             'the one with the lowest carry the same line at the top: <em>total '
             'increase, 1 percent</em>. A locality percentage that does not move '
             'adds nothing, however large it is.</p>')
    B.append('<p>Which percentage applies to you, and why it is a labor-market '
             'measure rather than a cost-of-living one, is set out in '
             '<a href="/how-locality-pay-works/">how locality pay works</a>.</p>')

    # ---- история
    B.append('<h2>What the last four years actually did</h2>')
    rows = "".join(
        f'<tr><th>{y}</th><td class="num">{b}%</td><td class="num">{l}%</td>'
        f'<td class="num">{tot}%</td><td>{letter}</td><td>{eo}, {eod}</td></tr>'
        for y, b, l, tot, letter, eo, eod in HISTORY)
    B.append('<div class="scroll" tabindex="0" role="region" '
             'aria-label="Federal pay raises by year">'
             '<table><thead><tr><th>Year</th><th>Base</th><th>Locality</th>'
             '<th>Overall</th><th>Letter sent</th><th>Order signed</th></tr>'
             f'</thead><tbody>{rows}</tbody></table></div>')
    # Обычный абзац, а НЕ .tlegend: механизм полей уносит легенды на боковое
    # поле, и на этой странице она оказалась в начале колонки, за экран до
    # своей таблицы.
    B.append('<p>Base and locality are announced separately in the President’s '
             'letter and fixed together in the executive order. The overall figure '
             'is the government-wide average, not anybody’s actual raise: what '
             'you get depends on your locality area.</p>')

    # ---- календарь
    B.append('<h2>When the answer arrives</h2>')
    B.append('<p>Three dates decide this, and they arrive in the same order every '
             'year.</p>')
    B.append('<p><strong>Before 1 September.</strong> The alternative pay plan '
             'letter goes to Congress. Recent ones landed on 31 August 2022, '
             '31 August 2023, 30 August 2024 and 28 August 2025 — in practice, '
             'the last days of the month.</p>')
    B.append('<p><strong>Early December.</strong> If the President sets a '
             'different level of locality pay, 5 U.S.C. 5304a requires that '
             'report at least a month before the payments would otherwise start. '
             'It is a separate deadline from the August one and it is often '
             'missed by commentators.</p>')
    B.append(f'<p><strong>Mid to late December.</strong> The executive order. The '
             f'last five were signed on 22 December 2021, 23 December 2022, '
             f'21 December 2023, 23 December 2024 and 18 December 2025. OPM '
             f'publishes the tables within days, and this site rebuilds from '
             f'them.</p>')
    B.append(f'<p><strong>10 January {nxt}.</strong> New rates take effect on the '
             f'first day of the first pay period beginning on or after 1 January '
             f'— which is why the raise almost never shows up in the first '
             f'paycheck of the year. For {year} that date was 11 January.</p>')

    # ---- прецедент
    B.append('<h2>The letter is not the last word</h2>')
    B.append('<p>A President can announce one thing in August and be overruled '
             'before January. For 2019 a freeze was announced; Congress put a '
             '1.9 percent raise into an appropriations act instead, and Executive '
             'Order 13866 was signed on 28 March 2019 — three months into the '
             'year, backdated. If you are reading this after the letter has gone '
             'out and the number in it disappoints, that precedent is the reason '
             'the subject stays open until the order is signed.</p>')

    # ---- где проверить
    B.append('<h2>Check it yourself</h2>')
    B.append('<p>Every claim on this page comes from one of these. Not one '
             'of them is this site.</p>')
    B.append('<ul>')
    for label, url in SOURCES:
        B.append(f'<li><a href="{url}">{label}</a></li>')
    B.append('</ul>')

    B.append(f'<p>This page is checked by hand, not by a clock. The date at the '
             f'top is when a person last looked at the primary sources; the build '
             f'refuses to publish if that date gets older than '
             f'{STALE_AFTER_DAYS} days, so a stale status cannot quietly ship.</p>')

    return shell(
        # Слово, которое человек набирает, обязано стоять в заголовке. Пока
        # там было «what is decided and when», страница отвечала на вопрос,
        # который уже никто не задаёт: ответ известен, спрашивают про него.
        f"{nxt} Federal Pay Raise: Frozen at {year} Rates | GS Pay Tables",
        f"The {nxt} pay plan freezes base and locality pay at {year} "
        f"rates, with 3.8 percent for law enforcement. What it means, and "
        f"the December date that decides it.",
        "\n".join(B), f"{DOMAIN}/pay-raise/", "raise")


# Адрес сайта приходит из render.py на старте сборки, как и в остальных модулях.
DOMAIN = ""
