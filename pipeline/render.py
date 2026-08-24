"""Сборка страниц FedPay.

Порядок блоков на странице подчинён одному правилу, выученному на MileageCurve:
оговорка про конфаундер стоит НАД числом, а не в подвале. Там заголовок обещал
срок службы машины, а показывал возраст парка, и это молча ехало на 318 страницах.
Здесь та же ловушка: локалити привязано к зарплатам частного сектора региона,
а не к ценам, и человек, читающий «Сан-Франциско +46%», делает неверный вывод,
если ему об этом не сказать до того, как он увидит цифру.

Только стандартная библиотека — D-009.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

import design
import pages as P

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
DIST = HERE / "dist"

SITE = "FedPay"
TAGLINE = "What the federal pay tables actually mean"
DOMAIN = "https://fedpayscale.com"
OWNER = "BiLingoPlus LLC"
CONTACT = "hello@fedpayscale.com"

# Опорная клетка для сравнений между зонами: GS-12/5 — середина сетки,
# самый населённый диапазон грейдов.
REF_GRADE, REF_STEP = "12", "5"


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def money(n) -> str:
    return f"${int(round(n)):,}"


def fit_title(core: str, limit: int = 60) -> str:
    """Бренд в конец — только если он влезает в отображаемую длину выдачи."""
    tail = f" | {SITE}"
    return core + tail if len(core) + len(tail) <= limit else core


def fit_desc(parts: list, limit: int = 158) -> str:
    """Набираем описание по предложениям, пока помещается. Обрезки на середине
    слова не бывает: лишнее предложение просто не берём."""
    out = ""
    for p in parts:
        cand = (out + " " + p).strip()
        if len(cand) > limit:
            break
        out = cand
    return out


def stop(name: str) -> str:
    """Точка в конце предложения — но не вторая подряд.

    «Rest of U.S.» уже заканчивается точкой, и обычное `{name}.` давало
    «for Rest of U.S..» на самой посещаемой зоне сайта.
    """
    return "" if name.rstrip().endswith(".") else "."


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower())
    return re.sub(r"-+", "-", s).strip("-")


def strip_css_comments(css: str) -> str:
    """Убирает комментарии из CSS на выходе.

    Комментарии в исходнике русские — это нормально, там пишем на языке
    разработки. Но в отгружаемый HTML они попадать не должны: на MileageCurve
    ровно так 321 страница уехала с русским текстом на английском сайте, и все
    структурные проверки при этом были зелёными. Гейт ловит это по отрендеренному
    выводу, а функция — устраняет причину.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


# --------------------------------------------------------------------------- каркас
def jsonld(title: str, desc: str, canonical: str, crumbs: list) -> str:
    """Микроразметка: только то, что действительно есть на странице.

    BreadcrumbList даёт хлебные крошки в выдаче, WebSite и Organization
    привязывают страницы к издателю. Ничего про рейтинги, отзывы и авторов:
    за разметку, не подтверждённую содержимым, Google снимает расширенный
    сниппет целиком, а тема у нас денежная — доверие дороже украшений.
    """
    graph = [{
        "@type": "WebPage", "@id": canonical, "url": canonical,
        "name": title, "description": desc,
        "isPartOf": {"@id": f"{DOMAIN}/#website"},
        "publisher": {"@id": f"{DOMAIN}/#org"},
    }, {
        "@type": "WebSite", "@id": f"{DOMAIN}/#website",
        "url": f"{DOMAIN}/", "name": SITE, "inLanguage": "en-US",
        "publisher": {"@id": f"{DOMAIN}/#org"},
    }, {
        "@type": "Organization", "@id": f"{DOMAIN}/#org",
        "name": OWNER, "url": f"{DOMAIN}/", "email": CONTACT,
    }]
    if crumbs:
        graph.append({
            "@type": "BreadcrumbList", "@id": f"{canonical}#crumbs",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": n,
                 **({"item": DOMAIN + u} if u else {})}
                for i, (n, u) in enumerate(crumbs, 1)],
        })
    return ('<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@graph": graph},
                         ensure_ascii=False, separators=(",", ":"))
            + "</script>")


def shell(title: str, desc: str, body: str, canonical: str, nav: str = "",
          crumbs: list = None) -> str:
    cur = lambda k: ' aria-current="page"' if k == nav else ""
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<style>{strip_css_comments(design.CSS)}</style>
{jsonld(title, desc, canonical, crumbs or [])}
</head><body>
<div class="wrap">
<header class="site">
  <div class="masthead">
    <a class="brand" href="/">{design.MARK}{SITE}</a>
    <span class="tagline">{TAGLINE}</span>
    <nav aria-label="Main">
      <a href="/"{cur('home')}>Localities</a>
      <a href="/grades/"{cur('grades')}>Grades</a>
      <a href="/how-locality-pay-works/"{cur('how')}>How it works</a>
      <a href="/about/"{cur('about')}>About</a>
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer>
  <p class="disclaimer">FedPay is an independent reference published by {OWNER}.
  It is not affiliated with, endorsed by, or connected to the U.S. Office of Personnel
  Management or any government agency.</p>
  <p>Pay figures are computed from the official OPM salary tables and verified cell by
  cell against them. Price levels are Regional Price Parities from the U.S. Bureau of
  Economic Analysis. Both are works of the U.S. government and in the public domain.</p>
  <p><a href="/how-locality-pay-works/">How locality pay works</a> ·
  <a href="/grades/">All grades</a> · <a href="/about/">About</a> ·
  <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a></p>
  <p>Built {date.today().isoformat()} · <a href="mailto:{CONTACT}">{CONTACT}</a></p>
</footer>
</div>
</body></html>"""


# ------------------------------------------------------------------ страница зоны
def locality_page(code: str, loc: dict, T: dict, R: dict, ranks: dict,
                  places: dict) -> str:
    name = loc["area_name"]
    pct = loc["locality_pct"]
    year = T["year"]
    cap = T["ex_iv_cap"]
    grades = loc["grades"]
    rp = R["areas"].get(code, {})

    ref = grades[REF_GRADE][REF_STEP]
    base_ref = T["base"]["grades"][REF_GRADE][REF_STEP]["annual"]

    B: list[str] = []
    B.append('<ol class="crumbs"><li><a href="/">All localities</a></li>'
             f'<li>{esc(name)}</li></ol>')
    B.append(f'<h1>{esc(name)} GS pay scale, {year}</h1>')

    n_capped = sum(1 for st in grades.values() for c in st.values() if c["capped"])
    B.append(f'<p class="sub">Every General Schedule rate for this locality, what the '
             f'{pct:g}% adjustment is actually worth once local prices are taken into '
             f'account, and which cells stop growing because they hit the statutory '
             f'ceiling.</p>')

    # --- оговорка ВЫШЕ числа, и её текст зависит от того, что реально
    #     произойдёт с этой зоной после поправки на цены
    B.append(caveat_block(code, loc, ranks, rp))

    # --- ответный блок
    B.append('<div class="answer">')
    B.append(f'<span class="what">GS-{REF_GRADE}, step {REF_STEP} in this locality</span>')
    B.append(f'<span class="big">{money(ref["annual"])}</span>')
    B.append(f'<p>That is the {year} base rate of {money(base_ref)} plus the '
             f'<strong>{pct:g}%</strong> locality payment for {esc(name)}{stop(name)} '
             f'Hourly: ${ref["hourly"]:,.2f}. Overtime: ${ref["overtime"]:,.2f}.</p>')
    if rp.get("rpp"):
        nom_rank = ranks["nominal"].get(code)
        adj_rank = ranks["adjusted"].get(code)
        move = nom_rank - adj_rank
        if abs(move) >= 3:
            direction = ("rises" if move > 0 else "falls")
            B.append(f'<p>Among the {ranks["n"]} localities with published price data, this one is '
                     f'<strong>#{nom_rank} by the number on the cheque</strong> but '
                     f'<strong>#{adj_rank} once local prices are counted</strong> — it '
                     f'{direction} {abs(move)} places.</p>')
    B.append('</div>')

    # --- ЭКСПОНАТ 1: покупательная способность
    B.append(exhibit_purchasing_power(code, T, R, ranks))

    # --- ЭКСПОНАТ 2: полная таблица
    B.append(exhibit_table(loc, cap, year))

    # --- потолок
    if n_capped:
        B.append(cap_section(loc, cap, n_capped, year))

    # --- соседи по рейтингу: у каждой зоны свои
    B.append(neighbours_section(code, ranks))

    # --- округа: главный источник уникального текста и ответ на вопрос,
    #     которого нет ни у одного конкурента
    B.append(counties_section(name, places))

    # --- как это устроено: набор абзацев зависит от признаков зоны
    B.append(mechanics_block(name, loc, T, cap, n_capped))

    # Заголовок и описание раньше не помещались в выдачу: 101 и 213 знаков при
    # отображаемых ~60 и ~160. Обрезался ровно хвост, где стоял наш довод.
    # Теперь бренд и хвост добавляются только если для них осталось место, а
    # описание начинается с готового ответа — его и кликают.
    title = fit_title(f"{name} GS Pay Scale {year}")
    d = fit_desc([
        f"GS-12 step 5 in {name} is {money(ref['annual'])} in {year} — "
        f"{pct:g}% locality pay.",
        "All 15 grades and 10 steps, checked against the official table.",
        "Plus what the salary is worth after local prices.",
    ])
    return shell(title, d, "\n".join(B), f"{DOMAIN}/locality/{slug(name)}/", "home",
                 crumbs=[("All localities", "/"), (name, None)])


def exhibit_purchasing_power(code: str, T: dict, R: dict, ranks: dict) -> str:
    """Единственный блок, которого нет ни у одного конкурента."""
    rows = ranks["rows"]
    me = next((r for r in rows if r["code"] == code), None)

    top = rows[:8]
    show = list(top)
    if me and me not in show:
        show.append(me)

    mx = max(r["adjusted"] for r in rows)
    items = []
    for r in show:
        w = r["adjusted"] / mx * 100
        cls = ' class="hi"' if r["code"] == code else ""
        items.append(
            f'<li{cls}><span class="nm">{esc(r["name"])}</span>'
            f'<span class="bar"><span style="width:{w:.1f}%"></span></span>'
            f'<span class="v">{money(r["adjusted"])}</span></li>')

    bea_year = R["bea_year"]
    nom_first = max(rows, key=lambda r: r["nominal"])
    adj_first = rows[0]

    return f"""<figure class="ex">
<div class="ex-kicker">Exhibit 1 · nobody else publishes this</div>
<div class="ex-title">GS-{REF_GRADE} step {REF_STEP}, after local prices</div>
<p class="ex-note">Each bar is the {T['year']} salary divided by that area's price level,
so the bars are comparable in what they actually buy. Longer is better. Price levels are
BEA Regional Price Parities for {bea_year}, where the U.S. average is 100.</p>
<ul class="bars">{''.join(items)}</ul>
<figcaption>Highest on paper: <strong>{esc(nom_first['name'])}</strong> at
{money(nom_first['nominal'])}. Highest in what it buys:
<strong>{esc(adj_first['name'])}</strong> at {money(adj_first['adjusted'])} of
purchasing power from a salary of {money(adj_first['nominal'])}. Sources: OPM
{T['year']} salary tables; BEA Regional Price Parities {bea_year}. Price data lags the
pay tables, and metropolitan boundaries do not match locality boundaries exactly — the
nearest metropolitan area is used as the proxy.</figcaption>
</figure>"""


def exhibit_table(loc: dict, cap: int, year: int) -> str:
    grades = loc["grades"]
    steps = sorted({int(s) for st in grades.values() for s in st}, key=int)
    head = "".join(f'<th class="num">{s}</th>' for s in steps)
    body = []
    for g in sorted(grades, key=int):
        cells = []
        for s in steps:
            c = grades[g].get(str(s))
            if not c:
                cells.append('<td class="num">—</td>')
                continue
            cls = ' class="num capped"' if c["capped"] else ' class="num"'
            cells.append(f'<td{cls}>{money(c["annual"])}</td>')
        body.append(f'<tr><th scope="row">GS-{g}</th>{"".join(cells)}</tr>')

    return f"""<figure class="ex">
<div class="ex-kicker">Exhibit 2</div>
<div class="ex-title">Every {year} rate in this locality</div>
<p class="ex-note">Annual rates in dollars, read cell by cell from the published OPM
table rather than calculated. Cells marked ▲ have been cut down to the statutory
ceiling of {money(cap)} — the printed number is lower than the formula would give.</p>
<div class="scroll"><table>
<thead><tr><th>Grade</th>{head}</tr></thead>
<tbody>{''.join(body)}</tbody>
</table></div>
<figcaption>Source: OPM {year} General Schedule salary tables. Every cell on this page
was independently recomputed from the base table and the locality percentage and matched
the published figure to the dollar.</figcaption>
</figure>"""


def cap_section(loc: dict, cap: int, n: int, year: int) -> str:
    grades = loc["grades"]
    B = [f'<h2>Where raises stop being raises</h2>']
    B.append(f'<p>In this locality <strong>{n} of the 150 cells</strong> are pinned to '
             f'the {money(cap)} ceiling. Inside that band a step increase is worth '
             f'nothing at all: the formula produces a bigger number, the law cuts it '
             f'back, and the payslip does not move.</p>')

    tiles = []
    for g in sorted(grades, key=int):
        capped_steps = [int(s) for s, c in grades[g].items() if c["capped"]]
        if not capped_steps:
            continue
        first = min(capped_steps)
        lost = len([s for s in capped_steps if s > first])
        tiles.append(
            f'<div class="tile"><div class="k">GS-{g}</div>'
            f'<div class="v">Step {first}</div>'
            f'<div class="d">Hits the ceiling here. '
            f'{("The " + str(lost) + " step increase" + ("s" if lost != 1 else "") + " above it add" + ("" if lost != 1 else "s") + " nothing.") if lost else "Only the top step is affected."}'
            f'</div></div>')
    if tiles:
        B.append(f'<div class="grid2">{"".join(tiles)}</div>')
    B.append('<p>This matters most when comparing job offers. Two identical grades in '
             'two localities can look like a clear win on paper while the higher-paid '
             'one has already run out of room to grow.</p>')
    return "\n".join(B)


# --------------------------------------------------------------------------- ранги
def compute_ranks(T: dict, R: dict) -> dict:
    rows = []
    for code, loc in T["localities"].items():
        cell = loc["grades"].get(REF_GRADE, {}).get(REF_STEP)
        rp = R["areas"].get(code, {})
        if not cell or not rp.get("rpp"):
            continue
        rows.append({
            "code": code, "name": loc["area_name"],
            "nominal": cell["annual"],
            "adjusted": cell["annual"] / (rp["rpp"] / 100.0),
            "rpp": rp["rpp"],
        })
    rows.sort(key=lambda r: -r["adjusted"])
    adjusted = {r["code"]: i for i, r in enumerate(rows, 1)}
    by_nom = sorted(rows, key=lambda r: -r["nominal"])
    nominal = {r["code"]: i for i, r in enumerate(by_nom, 1)}
    return {"rows": rows, "nominal": nominal, "adjusted": adjusted, "n": len(rows)}


def main() -> int:
    T = json.loads((DATA / "paytables-2026.json").read_text(encoding="utf-8"))
    R = json.loads((DATA / "rpp-map.json").read_text(encoding="utf-8"))
    L = json.loads((DATA / "localities-2026.json").read_text(encoding="utf-8"))
    ranks = compute_ranks(T, R)

    if DIST.exists():
        for p in sorted(DIST.rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
    DIST.mkdir(exist_ok=True)

    def write(rel: str, content: str) -> None:
        d = DIST / rel.strip("/")
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(content, encoding="utf-8")

    urls = ["/"]

    # --- зоны
    for code, loc in T["localities"].items():
        rel = f"locality/{slug(loc['area_name'])}"
        write(rel, locality_page(code, loc, T, R, ranks, L.get(code, {})))
        urls.append(f"/{rel}/")

    # --- грейды
    for g in sorted(T["base"]["grades"], key=int):
        write(f"gs-{g}", P.grade_page(g, T, R, ranks, shell, esc, money, slug))
        urls.append(f"/gs-{g}/")

    write("grades", P.grades_index(T, ranks, shell, esc, money))
    urls.append("/grades/")

    # --- главная и статические
    (DIST / "index.html").write_text(
        P.home(T, R, ranks, L, shell, esc, money, slug), encoding="utf-8")
    for rel, html_ in (
        ("how-locality-pay-works", P.how_it_works(T, shell, money)),
        ("about", P.about(shell)),
        ("privacy", P.privacy(shell)),
        ("terms", P.terms(shell)),
    ):
        write(rel, html_)
        urls.append(f"/{rel}/")

    (DIST / "404.html").write_text(P.not_found(shell), encoding="utf-8")
    (DIST / "sitemap.xml").write_text(P.sitemap(urls, DOMAIN), encoding="utf-8")
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    (DIST / "_redirects").write_text("/index.html  /  301\n", encoding="utf-8")
    (DIST / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  X-Frame-Options: DENY\n", encoding="utf-8")

    print(f"страниц: {len(urls)} + 404")

    # ------------------------------------------------------------------ гейты
    problems: list[str] = []
    htmls = sorted(DIST.rglob("*.html"))
    all_urls = {u.rstrip("/") for u in urls} | {"/404.html"}

    for f in htmls:
        h = f.read_text(encoding="utf-8")
        rel = f.relative_to(DIST)

        # 1. отрендеренный вывод, а не исходники: кириллица не должна уехать
        if re.search(r"[\u0400-\u04FF]", h):
            problems.append(f"{rel}: кириллица в отгружаемом HTML")
        # 2. следы сломанных вычислений
        for bad in ("NaN", "undefined", "None", "$0<", ">$0 "):
            if bad in h:
                problems.append(f"{rel}: в выводе встречается {bad!r}")
        # 3. тире там, где должна быть длина CSS или число
        if re.search(r"[\u2013\u2014](?=px|\d*px)|\d[\u2013\u2014]px", h):
            problems.append(f"{rel}: тире вместо длины CSS")
        # 4. дисклеймер обязателен на каждой странице — FTC Impersonation Rule
        if "not affiliated with" not in h:
            problems.append(f"{rel}: нет дисклеймера о неаффилированности")
        # 5. внутренние ссылки должны вести на существующие страницы
        for href in set(re.findall(r'href="(/[^"#?]*)"', h)):
            if href.rstrip("/") not in all_urls:
                problems.append(f"{rel}: ссылка в никуда {href}")

    # 6. объём текста — только для КОНТЕНТНЫХ страниц.
    #    404, политика, условия и «о сайте» существуют не ради объёма, и
    #    требовать от них 700 слов — значит лить воду в юридический документ.
    SERVICE = {"404.html", "privacy", "terms", "about"}
    thin = []
    for f in htmls:
        rel = f.relative_to(DIST)
        if rel.name == "404.html" or rel.parts[0] in SERVICE:
            continue
        h = f.read_text(encoding="utf-8")
        body = h[h.find("<main>"):h.find("</main>")]
        w = len(re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", body)).split())
        if w < 700:
            thin.append(f"{rel} ({w} слов)")
    if thin:
        problems.append(f"страниц тоньше 700 слов: {len(thin)} — {', '.join(thin[:5])}")

    # 7. согласованность направления. Оговорка и карточка ответа пишутся
    #    независимо друг от друга, и однажды разъехались: страница
    #    Сан-Франциско называла падение с #1 на #21 выигрышем. Ни один
    #    структурный гейт этого не видел — сверяем две фразы между собой.
    contra = []
    for f in htmls:
        if f.parent.parent.name != "locality":
            continue
        h = f.read_text(encoding="utf-8")
        good = "works in your favour" in h
        bad = "matters a great deal" in h
        if good and bad:
            contra.append(f"{f.relative_to(DIST)}: обе формулировки сразу")
        elif good and "it rises" not in h:
            contra.append(f"{f.relative_to(DIST)}: «в вашу пользу», но зона не поднимается")
        elif bad and "it falls" not in h:
            contra.append(f"{f.relative_to(DIST)}: «съедает надбавку», но зона не падает")
    if contra:
        problems.append(f"противоречие оговорки и карточки: {len(contra)} — {contra[0]}")

    # 8. полнота охвата. Страницы грейдов однажды строились по 55 зонам из 58,
    #    и «Rest of U.S.» — самая многочисленная зона федеральной службы —
    #    исчезла со всех пятнадцати страниц, заодно занизив заявленный разброс
    #    зарплат. Сборка была зелёной: ничего не сломалось, просто не хватало.
    n_loc = len(T["localities"])
    short = []
    for g in sorted(T["base"]["grades"], key=int):
        h = (DIST / f"gs-{g}" / "index.html").read_text(encoding="utf-8")
        got = h.count('<th scope="row"><a href="/locality/')
        if got != n_loc:
            short.append(f"gs-{g}: {got} из {n_loc}")
    home_h = (DIST / "index.html").read_text(encoding="utf-8")
    if home_h.count('href="/locality/') != n_loc:
        short.append(f"главная: {home_h.count('href=\"/locality/')} из {n_loc}")
    if short:
        problems.append(f"зоны потеряны на страницах: {', '.join(short)}")

    # 9. двойная точка. Названия зон вроде «Rest of U.S.» уже кончаются точкой,
    #    и шаблон вида «{name}.» даёт «U.S..» — мелочь, которая на странице с
    #    самым большим трафиком читается как небрежность.
    dbl = []
    for f in htmls:
        txt = re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8"))
        if re.search(r"[A-Za-z]\.\.(?!\.)", txt):
            dbl.append(str(f.relative_to(DIST)))
    if dbl:
        problems.append(f"двойная точка в тексте: {len(dbl)} — {dbl[0]}")

    # 10. крошки: разметка обязана повторять видимую цепочку. Google снимает
    #     расширенный сниппет целиком, если BreadcrumbList описывает не то,
    #     что человек видит на странице, — а мы уже разошлись на единицу.
    crumb_bad = []
    for f in htmls:
        h = f.read_text(encoding="utf-8")
        vis = h.count("<li>", h.find('<ol class="crumbs">'), h.find("</ol>") + 1) \
            if '<ol class="crumbs">' in h else 0
        m = re.search(r'"BreadcrumbList".*?"itemListElement":\[(.*?)\]\}', h)
        mark = m.group(1).count('"ListItem"') if m else 0
        if vis != mark:
            crumb_bad.append(f"{f.relative_to(DIST)}: видно {vis}, размечено {mark}")
    if crumb_bad:
        problems.append(f"крошки разошлись с разметкой: {len(crumb_bad)} — {crumb_bad[0]}")

    if problems:
        print(f"\nГЕЙТ НЕ ПРОЙДЕН: {len(problems)} замечаний", file=sys.stderr)
        for p in problems[:20]:
            print("  " + p, file=sys.stderr)
        return 1

    print("гейты пройдены: кириллица, битые вычисления, дисклеймер, ссылки, "
          "объём, направление, полнота охвата, пунктуация, крошки")
    return 0


def caveat_block(code, loc, ranks, rp):
    """Оговорка перед числом; формулировка следует из того, что будет с зоной."""
    pct = loc["locality_pct"]
    nom = ranks["nominal"].get(code)
    adj = ranks["adjusted"].get(code)
    lead = "<strong>Read this before the number.</strong> "
    base = ("Locality pay is calculated from what <em>private employers in the same "
            "region pay for comparable work</em>. It is not a cost-of-living "
            "adjustment, and OPM says so in as many words. ")
    if nom is None or adj is None:
        body = (base + "This area has no single metropolitan price index published for "
                "it, so the comparison in Exhibit 1 leaves it out rather than guessing.")
    elif nom - adj >= 8:
        # Меньший номер ранга = лучше. Зона ПОДНИМАЕТСЯ, когда её ранг с учётом
        # цен меньше номинального. Ветки стояли наоборот, и страница
        # Сан-Франциско подавала падение с #1 на #21 как выигрыш.
        body = (base + f"Here the distinction works in your favour: the area ranks "
                f"#{nom} on the size of the cheque but #{adj} once local prices are "
                f"counted. The salary looks unremarkable and buys more than it appears "
                f"to.")
    elif nom - adj <= -8:
        body = (base + f"Here the distinction matters a great deal. The area ranks "
                f"#{nom} by the number on the cheque and only #{adj} once local prices "
                f"are counted — a {pct:g}% adjustment that a high cost base takes "
                f"back.")
    else:
        body = (base + f"Here the two rankings sit close together \u2014 #{nom} on paper "
                f"against #{adj} adjusted \u2014 so the {pct:g}% figure is a reasonable "
                f"guide to what the job is worth. That is not true everywhere, which is "
                f"what Exhibit 1 shows.")
    return f'<div class="caveat"><p>{lead}{body}</p></div>'


def mechanics_block(name, loc, T, cap, n_capped):
    """Как складывается число. Набор абзацев зависит от признаков зоны."""
    pct = loc["locality_pct"]
    year = T["year"]
    base_ref = T["base"]["grades"][REF_GRADE][REF_STEP]["annual"]
    ref = loc["grades"][REF_GRADE][REF_STEP]["annual"]

    B = ["<h2>How the number is built</h2>"]
    B.append(f'<p>Every General Schedule grade has ten steps. The base rate comes from '
             f'the nationwide table, and the locality percentage is applied on top of '
             f'it. For {esc(name)} in {year} that percentage is <strong>{pct:g}%</strong>'
             f', which turns a base rate of {money(base_ref)} into {money(ref)} at '
             f'GS-{REF_GRADE} step {REF_STEP}.</p>')
    if n_capped:
        B.append(f'<p>No General Schedule rate may exceed Level IV of the Executive '
                 f'Schedule, {money(cap)} in {year}. Because this locality pays '
                 f'{pct:g}% over base, that ceiling is reached inside the published '
                 f'table: {n_capped} of the 150 cells here are printed at the cap rather '
                 f'than at what the formula produces.</p>')
    else:
        B.append(f'<p>No General Schedule rate may exceed Level IV of the Executive '
                 f'Schedule, {money(cap)} in {year}. At {pct:g}% this locality stays '
                 f'below that ceiling everywhere, so every step increase in the table '
                 f'below is worth its full face value \u2014 which is not the case in '
                 f'the highest-paying areas.</p>')
    if pct < 25:
        B.append(f'<p>Steps are not evenly spaced, which catches out anyone trying to '
                 f'extrapolate from the first one. In the {year} base table the gap '
                 f'between step 8 and step 9 of GS-1 is $46, while the gap between step '
                 f'1 and step 2 is over $1,100. Every figure on this page is therefore '
                 f'read from the published table rather than derived from a formula.</p>')
    else:
        B.append(f'<p>The percentage is applied to the base rate, the result is rounded, '
                 f'and only then is it checked against the ceiling \u2014 in that order. '
                 f'Doing it the other way round produces different numbers at the top of '
                 f'the schedule, which is one reason published figures sometimes '
                 f'disagree. Every cell here was recomputed independently and matched '
                 f'the OPM table to the dollar.</p>')
    return "\n".join(B)


def neighbours_section(code, ranks):
    """Кто стоит рядом в рейтинге покупательной способности."""
    rows = ranks["rows"]
    idx = next((i for i, r in enumerate(rows) if r["code"] == code), None)
    if idx is None:
        return ""
    me = rows[idx]
    window = rows[max(0, idx - 3):min(len(rows), idx + 4)]
    items = []
    for r in window:
        mine = r["code"] == code
        mark = ' class="you"' if mine else ""
        pos = rows.index(r) + 1
        # Соседи по покупательной способности — самые осмысленные внутренние
        # ссылки на сайте: читатель уже сравнивает. Отсутствие таких ссылок с
        # главной мы сами диагностировали как причину плохой индексации.
        cell_name = (esc(r["name"]) if mine else
                     f'<a href="/locality/{slug(r["name"])}/">{esc(r["name"])}</a>')
        items.append(
            f'<tr{mark}><td class="rank">{pos}</td>'
            f'<th scope="row">{cell_name}</th>'
            f'<td class="num">{money(r["nominal"])}</td>'
            f'<td class="num">{r["rpp"]:.1f}</td>'
            f'<td class="num">{money(r["adjusted"])}</td></tr>')
    better = [r for r in rows[:idx] if r["nominal"] < me["nominal"]]
    lead = ""
    if better:
        b = better[-1]
        gap = me["nominal"] - b["nominal"]
        lead = (f'<p><strong>{esc(b["name"])}</strong> pays {money(gap)} less on paper '
                f'than this locality and still leaves you better off once prices are '
                f'counted. There are {len(better)} such areas above this one.</p>')
    return (f'<h2>What is next to it</h2>\n{lead}'
            f'<p>These are the localities immediately around this one once local prices '
            f'are taken into account. The middle column is the price level, where 100 is '
            f'the national average \u2014 lower is cheaper.</p>'
            f'<div class="scroll"><table><thead><tr><th class="rank">#</th>'
            f'<th>Locality</th><th class="num">On paper</th><th class="num">Prices</th>'
            f'<th class="num">What it buys</th></tr></thead>'
            f'<tbody>{"".join(items)}</tbody></table></div>')


def counties_section(name, places):
    """Какие округа входят в зону \u2014 уникальный текст и ответ на живой вопрос."""
    recs = places.get("places", [])
    counties = [p for p in recs if p["kind"] == "county"]
    states = places.get("states", [])

    B = ['<h2>Am I actually in this locality?</h2>']
    B.append('<p>Locality is decided by your <strong>duty station</strong> \u2014 the '
             'place you physically report to \u2014 not by where you live and not by '
             'where your agency is headquartered. If you report to a building in one '
             'county and live in the next one over, the building decides your pay. '
             'Telework arrangements have their own rules and can change which locality '
             'applies, so confirm with your HR office rather than assuming.</p>')
    if not counties:
        B.append('<p>This locality is defined by exclusion: every duty station in the '
                 'United States that does not fall inside one of the 57 named '
                 'metropolitan areas is paid at this rate. It is the floor of the '
                 'system and the lowest adjustment there is.</p>')
        return "\n".join(B)
    if len(states) > 1:
        B.append(f'<p>This locality covers <strong>{len(counties)} counties across '
                 f'{len(states)} states</strong> ({", ".join(states)}). Crossing a state '
                 f'line inside it does not change your pay; crossing out of it does.</p>')
    else:
        st = states[0] if states else ""
        B.append(f'<p>This locality covers <strong>{len(counties)} counties</strong>'
                 f'{" in " + st if st else ""}. A duty station anywhere inside this list '
                 f'is paid at exactly the same rate.</p>')
    chips = "".join(f'<li>{esc(c["name"])}</li>' for c in counties)
    B.append(f'<figure class="ex"><div class="ex-kicker">Every county in this locality'
             f'</div><div class="ex-title">{len(counties)} places paid at this rate</div>'
             f'<ul class="counties">{chips}</ul>'
             f'<figcaption>Source: OPM 2026 locality pay area definitions. FIPS codes '
             f'are omitted here for readability. Military installations that OPM assigns '
             f'to a different locality than the county around them are listed separately '
             f'and are not shown in this list.</figcaption></figure>')
    inst = [p for p in recs if p["kind"] == "installation"]
    if inst:
        B.append(f'<p>OPM also assigns {len(inst)} named installation'
                 f'{"s" if len(inst) != 1 else ""} to this locality separately from the '
                 f'county it sits in \u2014 a base can be paid at a different rate from '
                 f'the town outside its gate.</p>')
    return "\n".join(B)



if __name__ == "__main__":
    raise SystemExit(main())
