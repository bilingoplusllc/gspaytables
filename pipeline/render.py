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

import hashlib
import html
import json
import math
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import calc
import compare
import design
import fonts
import icons
import ladder
import states
import pages as P

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
DIST = HERE / "dist"

SITE = "FedPay"
TAGLINE = "What the federal pay tables actually mean"
DOMAIN = "https://fedpayscale.com"
OWNER = "BiLingoPlus LLC"
CONTACT = "hello@fedpayscale.com"

# Цвет строки браузера на мобильных: должен совпадать с фоном страницы,
# иначе над сайтом висит чужая полоса.
# Дата последнего изменения данных. Выставляется в main() по отпечатку.
DATA_DATE = ""

# Правила @font-face. Читаются с диска: сборка страниц в сеть не ходит.
FONT_CSS = ""

# Предзагрузка шрифта. Без неё браузер узнаёт о файле только разобрав CSS,
# и загрузка стартует позже, чем могла бы. Замер показал, что подмена на
# системный стек сдвигает текст на 0,6% — компенсировать метрики не за чем,
# а вот стартовать раньше стоит.
FONT_PRELOAD = ""

# Тег подключения внешнего скрипта. Имя содержит отпечаток данных,
# поэтому выставляется в main() после их чтения.
JS_TAG = ""

THEME_LIGHT = "#f1f2f4"
THEME_DARK = "#15171a"

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


def data_date(T: dict, R: dict, L: dict) -> str:
    """Дата последнего РЕАЛЬНОГО изменения данных.

    Отпечаток берётся с содержимого: ставки, проценты, ценовые индексы, состав
    зон. Не изменились — дата остаётся прежней, сколько бы раз ни пересобирали.
    """
    blob = json.dumps([T["year"], T["ex_iv_cap"], R["bea_year"],
                       {c: l["locality_pct"] for c, l in T["localities"].items()},
                       {c: v.get("rpp") for c, v in R["areas"].items()},
                       {c: len(v.get("places", [])) for c, v in L.items()}],
                      sort_keys=True, separators=(",", ":"))
    fp = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    stamp = DATA / "last-changed.txt"
    if stamp.exists():
        old_fp, old_date = stamp.read_text(encoding="utf-8").split()[:2]
        if old_fp == fp:
            return old_date
    today = date.today().isoformat()
    stamp.write_text(f"{fp} {today}\n", encoding="utf-8")
    return today


def side_rail(title: str, links: list, note: str = "") -> str:
    """Рельс со списком ссылок. Пустой список рельса не создаёт."""
    if not links:
        return ""
    items = "".join(
        f'<li><a href="{href}"{" aria-current=\'page\'" if cur else ""}>{esc(label)}'
        f'</a></li>' for href, label, cur in links)
    tail = f'<p class="rail-note">{note}</p>' if note else ""
    return (f'<h2>{esc(title)}</h2><ol>{items}</ol>{tail}'
            f'<div class="ad-slot ad-rail">Advertisement</div>')


def calc_bundle(T: dict, R: dict, ranks: dict) -> tuple:
    """Возвращает (имя файла, содержимое) для внешнего скрипта.

    Данные и код одинаковы на каждой странице: клиент считает ставки сам, и ему
    нужны те же 150 базовых чисел и 58 процентов везде. Встроенный в страницу
    скрипт кешировать невозможно, поэтому он выносится в файл, а отпечаток в
    имени гарантирует, что при изменении данных адрес сменится сам — старый кеш
    не выстрелит устаревшими ставками.
    """
    body = ("window.__FP=" + calc.calc_data(T, R, ranks, slug) + ";\n"
            + calc.CALC_JS)
    fp = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    return f"fp.{fp}.js", body


def calc_script(name: str) -> str:
    """Тег подключения. defer: разметка уже разобрана, гонки нет."""
    return f'<script src="/{name}" defer></script>'


def cities(area_name: str) -> list:
    """Главные города зоны — из её же официального имени.

    OPM перечисляет их сам. Двойной дефис разделяет города, когда в имени
    города есть собственный дефис; одинарный — во всех остальных случаях.
    Для зон-штатов и остатка США городов в имени нет, и выдумывать их мы не
    станем: на такой странице честнее сказать про весь штат.
    """
    head = area_name.split(",")[0].strip()
    if head.startswith("State of") or head.startswith("Rest of"):
        return []
    parts = head.split("--") if "--" in head else head.split("-")
    seen, out = set(), []
    for p in parts:
        p = p.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out


def ordinal(n: int) -> str:
    """Порядковое числительное по-английски. «22th» вместо «22nd» на странице
    о деньгах читается как небрежность, а небрежность здесь стоит доверия."""
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


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
        "dateModified": DATA_DATE,
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
          crumbs: list = None, js: str = "", bar: str = "", rail: str = "",
          wide: bool = False, noindex: bool = False) -> str:
    """Каркас страницы.

    bar  — залипающая полоса ответа. Есть на страницах, у которых ответ
           выражается одним числом: зона, грейд, сравнение.
    rail — левый рельс: оглавление страницы, переключатель и место под рекламу.
           Пустой рельс превращает раскладку в одноколоночную, а не оставляет
           в сетке дыру.
    """
    updated = DATA_DATE
    cur = lambda k: ' aria-current="page"' if k == nav else ""
    # wide — раскладка без рельса и без колонки в 820 px: на главной её
    # занимала таблица из 58 строк на семь колонок, а рельс отбирал под
    # дубликат верхнего меню ещё 230 px слева.
    layout = "layout" if rail else ("layout wide" if wide else "layout solo")
    rail_html = f'<aside class="rail">{rail}</aside>' if rail else ""
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
{FONT_PRELOAD}
<meta name="theme-color" content="{THEME_LIGHT}" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="{THEME_DARK}" media="(prefers-color-scheme: dark)">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""}{'<meta name="robots" content="noindex">' if noindex else ""}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{DOMAIN}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<style>{FONT_CSS}{strip_css_comments(design.CSS)}</style>
{jsonld(title, desc, canonical, crumbs or [])}
</head><body>
<a class="skip" href="#content">Skip to content</a>
<header class="site">
  <div class="masthead">
    <a class="brand" href="/">{SITE}</a>
    <span class="tagline">{TAGLINE}</span>
    <nav aria-label="Main">
      <a href="/"{cur('home')}>Localities</a>
      <a href="/calculator/"{cur('calc')}>Calculator</a>
      <a href="/compare/"{cur('compare')}>Compare</a>
      <a href="/states/"{cur('states')}>States</a>
      <a href="/promotion/"{cur('promotion')}>Promotions</a>
      <a href="/grades/"{cur('grades')}>Grades</a>
      <a href="/how-locality-pay-works/"{cur('how')}>How it works</a>
      <a href="/about/"{cur('about')}>About</a>
    </nav>
  </div>
</header>
{bar}
<div class="{layout}">
{rail_html}
<main id="content">
{body}
</main>
</div>
<footer><div class="in">
  <p class="disclaimer">FedPay is an independent reference published by {OWNER}.
  It is not affiliated with, endorsed by, or connected to the U.S. Office of Personnel
  Management or any government agency.</p>
  <p>Pay figures are computed from the official OPM salary tables and verified cell by
  cell against them. Price levels are Regional Price Parities from the U.S. Bureau of
  Economic Analysis. Both are works of the U.S. government and in the public domain.</p>
  <p><a href="/how-locality-pay-works/">How locality pay works</a> ·
  <a href="/grades/">All grades</a> · <a href="/compare/">Compare areas</a> ·
  <a href="/methodology/">Methodology</a> · <a href="/about/">About</a> ·
  <a href="/contact/">Contact</a> ·
  <a href="/privacy/">Privacy</a> ·
  <a href="/terms/">Terms</a></p>
  <p>Data last changed {updated}. Pay tables are published once a year, so this
  date moves when the underlying figures move, not when the site is rebuilt.<br>
  <a href="mailto:{CONTACT}">{CONTACT}</a></p>
</div></footer>
{js}
</body></html>"""


# ------------------------------------------------------------------ страница зоны
def answer_bar(code: str, loc: dict, T: dict, ranks: dict, rp: dict) -> str:
    """Залипающая полоса ответа.

    Отвечает на главный вопрос страницы и не уезжает из виду при прокрутке.
    Отрисована сервером на опорной клетке, скрипт делает её живой; без скрипта
    остаётся верным неподвижным ответом, а не сломанным виджетом.
    """
    ref = loc["grades"][REF_GRADE][REF_STEP]
    year = T["year"]
    nom = ranks["nominal"].get(code)
    adj = ranks["adjusted"].get(code)

    grades = "".join(
        f'<option value="{g}"{" selected" if str(g) == REF_GRADE else ""}>GS-{g}</option>'
        for g in range(1, 16))
    steps = "".join(
        f'<option value="{s}"{" selected" if str(s) == REF_STEP else ""}>Step {s}</option>'
        for s in range(1, 11))

    more = [("Every two weeks", f'${ref["hourly"] * 80:,.2f}', ""),
            ("Per hour", f'${ref["hourly"]:,.2f}', ""),
            ("Overtime hour", f'${ref["overtime"]:,.2f}', "")]
    if nom and adj:
        more.append(("On paper", f"#{nom}", ""))
        move = nom - adj
        more.append(("After prices", f"#{adj}",
                     "up" if move > 0 else ("down" if move < 0 else "")))

    cells = "".join(
        f'<div><span class="v {cls}" data-ab="{i}">{v}</span>'
        f'<span class="k">{k}</span></div>'
        for i, (k, v, cls) in enumerate(more))

    return (f'<div class="answerbar" data-bar data-zone="{code}">'
            f'<div class="ab-in">'
            f'<span class="ab-where">{esc(name_of(loc))} &middot; {year}</span>'
            f'<span class="ab-pick"><label for="ab-grade">Grade</label>'
            f'<select id="ab-grade" data-grade>{grades}</select></span>'
            f'<span class="ab-pick"><label for="ab-step">Step</label>'
            f'<select id="ab-step" data-step>{steps}</select></span>'
            f'<span class="ab-main"><span class="ab-big" data-ab-big>'
            f'{money(ref["annual"])}</span>'
            f'<span class="ab-unit">a year</span></span>'
            f'<span class="ab-more">{cells}</span>'
            f'</div></div>')


def name_of(loc: dict) -> str:
    return loc["area_name"]


def locality_rail(code: str, T: dict, sections: list) -> str:
    """Рельс: переключатель зоны, оглавление страницы, место под рекламу."""
    opts = "".join(
        f'<option value="/locality/{slug(l["area_name"])}/"'
        f'{" selected" if c == code else ""}>{esc(l["area_name"])}</option>'
        for c, l in sorted(T["localities"].items(), key=lambda kv: kv[1]["area_name"]))
    nav = "".join(f'<li><a href="#{i}">{esc(label)}</a></li>' for i, label in sections)
    return (f'<div class="switch"><label for="rail-zone">Switch area</label>'
            f'<select id="rail-zone" data-jump>{opts}</select></div>'
            f'<h2>On this page</h2><ol>{nav}</ol>'
            f'<div class="ad-slot ad-rail">Advertisement</div>')


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
    n_capped = sum(1 for st in grades.values() for c in st.values() if c["capped"])
    nom = ranks["nominal"].get(code)
    adj = ranks["adjusted"].get(code)

    SECTIONS = [("rates", "Every rate here"),
                ("worth", "Is it a lot?"),
                ("ceiling", "Where raises stop"),
                ("near", "Who is next to it"),
                ("where", "Am I in this area?"),
                ("built", "How it is built"),
                ("work-it-out", "Work out your own")]

    B: list[str] = []
    B.append('<ol class="crumbs"><li><a href="/">All localities</a></li>'
             f'<li>{esc(name)}</li></ol>')
    B.append(f'<h1>{esc(name)} GS pay scale, {year}</h1>')
    B.append(f'<p class="sub">Every General Schedule rate for this locality pay area, '
             f'what the {pct:g}% adjustment is actually worth once local prices are '
             f'counted, and which cells stop growing because they hit the statutory '
             f'ceiling.</p>')

    # --- четыре факта на первом экране, вместо четырёх экранов прокрутки
    B.append(facts_grid(code, loc, T, R, ranks, ref, base_ref, n_capped, nom, adj))
    B.append('<div class="ad-slot ad-band">Advertisement</div>')

    # --- 1. таблица как элемент управления
    B.append(f'<section class="q" id="rates"><h2>Every {year} rate in '
             f'{esc(name)}</h2>')
    B.append(f'<p class="q-lead">All 150 cells, read from the published OPM table. '
             f'<strong>Click any cell</strong> and the bar at the top of the page '
             f'moves onto it \u2014 or use the arrow keys once a cell is '
             f'selected.</p>')
    B.append(exhibit_table(loc, cap, year))
    B.append('</section>')

    # --- 2. много ли это
    B.append('<section class="q" id="worth">')
    B.append('<h2>Is that a lot? Not until you count local prices</h2>')
    B.append(caveat_block(code, loc, ranks, rp))
    B.append(exhibit_purchasing_power(code, T, R, ranks))
    B.append('</section>')

    # --- 3. потолок
    if n_capped:
        B.append(f'<section class="q" id="ceiling">'
                 f'{cap_section(loc, cap, n_capped, year)}</section>')
    else:
        B.append(f'<section class="q" id="ceiling">'
                 f'<h2>Do raises ever stop counting here?</h2>'
                 f'<p class="q-lead">No. Every one of the 150 cells in this area '
                 f'stays below the {money(cap)} statutory ceiling.</p>'
                 f'<p>No General Schedule rate may exceed Level IV of the Executive '
                 f'Schedule, {money(cap)} in {year}. In the highest-paying localities '
                 f'that ceiling is reached inside the published table, and step '
                 f'increases in that band add nothing at all to the payslip. At '
                 f'{pct:g}% this area stays clear of it, so every step increase is '
                 f'worth its full face value all the way to GS-15 step 10.</p>'
                 f'</section>')

    # --- 4. соседи
    B.append(f'<section class="q" id="near">{neighbors_section(code, ranks)}</section>')

    # --- 5. где это
    B.append('<section class="q" id="where">')
    B.append(cities_section(name, places))
    B.append(counties_section(name, places))
    B.append('</section>')

    # --- 6. как устроено, с заметками на полях
    B.append(f'<section class="q" id="built">'
             f'{mechanics_block(name, loc, T, cap, n_capped)}</section>')

    # --- 7. инструмент
    B.append('<section class="q" id="work-it-out">')
    B.append(calc.calc_widget(
        fixed=code, grade=REF_GRADE, step=REF_STEP,
        heading="Work out a different grade and step",
        note=("Rates are recomputed from the published base table and this area's "
              "percentage, in the order the law sets: percentage first, rounding "
              "second, statutory ceiling last.")))
    B.append('</section>')

    title = fit_title(f"{name} GS Pay Scale {year}")
    cs = cities(name)
    covers = ("Covers " + ", ".join(cs[:-1]) + " and " + cs[-1] + "."
              if len(cs) > 1 else (f"Covers {cs[0]}." if cs else ""))
    d = fit_desc([p for p in [
        f"GS-12 step 5 in {name} is {money(ref['annual'])} in {year} \u2014 "
        f"{pct:g}% locality pay.",
        covers,
        "All 15 grades and 10 steps, checked against the official table.",
        "Plus what the salary is worth after local prices.",
    ] if p])

    return shell(title, d, "\n".join(B), f"{DOMAIN}/locality/{slug(name)}/", "home",
                 crumbs=[("All localities", "/"), (name, None)],
                 js=JS_TAG,
                 bar=answer_bar(code, loc, T, ranks, rp),
                 rail=locality_rail(code, T, SECTIONS))


def facts_grid(code, loc, T, R, ranks, ref, base_ref, n_capped, nom, adj) -> str:
    """Четыре карточки: разбор, два ранга, покупательная способность, потолок."""
    year, cap = T["year"], T["ex_iv_cap"]
    pct = loc["locality_pct"]
    rpp = R["areas"].get(code, {}).get("rpp")

    rows = [("Base rate before locality", money(base_ref), ""),
            (f"Locality pay, {pct:g}%", "+ " + money(ref["annual"] - base_ref), ""),
            ("Annual rate", money(ref["annual"]), "total")]
    ledger = "".join(
        f'<div{" class=\"total\"" if m == "total" else ""}>'
        f"<dt>{k}</dt><dd>{v}</dd></div>" for k, v, m in rows)
    c1 = (f'<div class="fact"><p class="fact-k">How the number is assembled</p>'
          f'<dl class="ledger">{ledger}</dl>'
          f'<p class="kpi-sub">Biweekly is the hourly rate times 80, the way OPM '
          f'derives it \u2014 not the annual rate divided by 26.</p></div>')

    if nom and adj:
        move = nom - adj
        word = "Places gained" if move > 0 else ("Places lost" if move < 0
                                                 else "No change")
        sign = ("+" if move > 0 else ("\u2212" if move < 0 else ""))
        cls = "up" if move > 0 else ("down" if move < 0 else "")
        c2 = (f'<div class="fact"><p class="fact-k">Paid #{nom}, {ordinal(adj)} in what it buys</p>'
              f'<span class="kpi {cls}">{sign}{abs(move) if move else "0"}</span>'
              f'<span class="kpi-sub">{word} once local prices are counted, out of '
              f'{ranks["n"]} areas with published price data.</span></div>')
        buys = ref["annual"] / (rpp / 100.0)
        c3 = (f'<div class="fact"><p class="fact-k">What it actually buys</p>'
              f'<span class="kpi">{money(buys)}</span>'
              f'<span class="kpi-sub">at average U.S. prices, from a salary of '
              f'{money(ref["annual"])}. Local price level {rpp:.1f} against a '
              f'national average of 100.</span></div>')
    else:
        c2 = (f'<div class="fact"><p class="fact-k">Rank</p>'
              f'<span class="kpi">\u2014</span>'
              f'<span class="kpi-sub">This area has no single published price index, '
              f'so it is left out of the purchasing-power ranking rather than given '
              f'an invented figure.</span></div>')
        c3 = (f'<div class="fact"><p class="fact-k">Locality adjustment</p>'
              f'<span class="kpi">{pct:g}%</span>'
              f'<span class="kpi-sub">on top of the nationwide base table, for every '
              f'grade and every step in this area.</span></div>')

    if n_capped:
        c4 = (f'<div class="fact"><p class="fact-k">Ceiling watch</p>'
              f'<span class="kpi">{n_capped} of 150</span>'
              f'<span class="kpi-sub">cells are pinned to the {money(cap)} statutory '
              f'ceiling. Inside that band a step increase adds nothing.</span></div>')
    else:
        c4 = (f'<div class="fact"><p class="fact-k">Ceiling watch</p>'
              f'<span class="kpi">Clear</span>'
              f'<span class="kpi-sub">No cell in this area reaches the {money(cap)} '
              f'ceiling, so every step increase is worth its full face '
              f'value.</span></div>')

    return f'<div class="facts">{c1}{c2}{c3}{c4}</div>'


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
        body = (base + f"Here the distinction works in your favor: the area ranks "
                f"#{nom} on the size of the paycheck but #{adj} once local prices are "
                f"counted. The salary looks unremarkable and buys more than it appears "
                f"to.")
    elif nom - adj <= -8:
        body = (base + f"Here the distinction matters a great deal. The area ranks "
                f"#{nom} by the number on the paycheck and only #{adj} once local prices "
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


def neighbors_section(code, ranks):
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
            f'the national average \u2014 lower is cheaper. Prices are '
            f'shown to one decimal place; the adjusted figures are computed '
            f'from the published index, which carries three.</p>'
            f'<div class="scroll" tabindex="0" role="region" aria-label="Scrollable table"><table><thead><tr><th class="rank">#</th>'
            f'<th>Locality</th><th class="num">On paper</th><th class="num">Prices</th>'
            f'<th class="num">What it buys</th></tr></thead>'
            f'<tbody>{"".join(items)}</tbody></table></div>')


def cities_section(name: str, places: dict) -> str:
    """Города зоны. Отвечает на вопрос, который человек задаёт своими словами.

    Никто не ищет «San Jose-San Francisco-Oakland». Ищут «San Francisco GS pay
    scale». Раздел существует ради этого вопроса, а не ради плотности слов:
    он говорит, что все перечисленные города платят одинаково, — а это
    неочевидно и людей это удивляет.
    """
    cs = cities(name)
    if not cs:
        if name.startswith("State of"):
            state = name.replace("State of", "").strip()
            return (f'<h2>Which cities does this cover?</h2>'
                    f'<p>All of them. This locality pay area is the whole state of '
                    f'{esc(state)}: {esc(state)} City limits and county lines make no '
                    f'difference to the percentage, and a duty station anywhere in '
                    f'the state is paid from the same table.</p>')
        return ('<h2>Which cities does this cover?</h2>'
                '<p>Every city in the United States that is not inside one of the '
                '57 named locality pay areas. That includes plenty of substantial '
                'metropolitan areas: being a city is not the test, being a '
                '<em>named locality pay area</em> is. If your city is not on the '
                'list of 57, this is your rate.</p>')

    joined = ", ".join(esc(c) for c in cs[:-1])
    last = esc(cs[-1])
    lead = f"{joined} and {last}" if len(cs) > 1 else last
    chips = "".join(f"<li>{esc(c)}</li>" for c in cs)
    states = [s for s in places.get("states", []) if s]
    n_counties = len([p for p in places.get("places", []) if p["kind"] == "county"])

    # Формулировка следует из признаков зоны, а не повторяется дословно на
    # пятидесяти восьми страницах: одинаковый абзац — это тонкий контент.
    if len(cs) == 1:
        first = (f'<p>This area is named after a single city, '
                 f'<strong>{lead}</strong>, and that is unusual: most locality pay '
                 f'areas are named after two or three. It does not mean the area is '
                 f'small \u2014 it means one city dominates it.</p>')
    elif len(states) > 1:
        first = (f'<p>OPM names this area after its principal cities: '
                 f'<strong>{lead}</strong>. They are not all in the same state, and '
                 f'that is the point worth taking away: the area crosses '
                 f'{len(states)} state lines and pays the same percentage on both '
                 f'sides of every one of them. A state border is not a pay '
                 f'border.</p>')
    elif len(cs) >= 3:
        first = (f'<p>OPM names this area after three principal cities: '
                 f'<strong>{lead}</strong>. All three are paid from the same table '
                 f'at the same percentage, which surprises people who assume the '
                 f'largest of the three commands more than the others. Size of city '
                 f'has nothing to do with it; the area is one unit.</p>')
    else:
        first = (f'<p>OPM names this area after <strong>{lead}</strong>. Both are '
                 f'paid at the same percentage from the same table \u2014 there is '
                 f'no premium for working in the larger of the two.</p>')

    if n_counties >= 20:
        second = (f'<p>The area reaches far beyond those city limits: '
                  f'{n_counties} counties in all, which is among the broader '
                  f'definitions in the system. Plenty of towns nobody would '
                  f'associate with {esc(cs[0])} are paid at this rate. What decides '
                  f'it is the county your duty station sits in, and the full list '
                  f'is below.</p>')
    elif n_counties:
        second = (f'<p>Those cities are the label, not the boundary. The area is '
                  f'defined as {n_counties} named counties, and a duty station '
                  f'anywhere inside them is paid at this rate whether or not it is '
                  f'near any of the cities above. The list is below.</p>')
    else:
        second = ('<p>Those cities are the label rather than the boundary: what '
                  'decides the rate is the county your duty station sits in.</p>')

    return (f'<h2>Which cities does this cover?</h2>\n{first}\n{second}\n'
            f'<ul class="chips-plain">{chips}</ul>')


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
    # Разрыв после пятой ступени: десять одинаковых колонок чисел не дают глазу
    # ни одного якоря, и нужная клетка ищется пересчётом. С разделителем
    # посередине «седьмая» читается как «вторая после разрыва».
    mid = steps[len(steps) // 2] if len(steps) > 4 else None

    def gut(s: str) -> str:
        return " gut" if s == mid else ""

    head = "".join(f'<th class="num{gut(s)}" scope="col">{s}</th>' for s in steps)
    body = []
    for g in sorted(grades, key=int):
        cells = []
        for s in steps:
            c = grades[g].get(str(s))
            if not c:
                cells.append(f'<td class="num{gut(s)}">\u2014</td>')
                continue
            cls = "num capped" if c["capped"] else "num"
            # Опорная клетка — та самая, о которой кричит заголовок страницы.
            # Без метки читатель искал её пересечением строки и столбца в
            # матрице из 150 одинаковых чисел.
            if g == REF_GRADE and str(s) == REF_STEP:
                cls += " ref"
            # Знак доллара снят: он повторялся 150 раз, добавляя шум и десятую
            # часть ширины таблицы, при том что единица названа в пояснении
            # прямо над таблицей.
            # Клетка знает свой адрес: по нему её находят и клик, и стрелки.
            cells.append(f'<td class="{cls} cell{gut(s)}" data-g="{g}" data-s="{s}">'
                         f'{c["annual"]:,}</td>')
        body.append(f'<tr><th scope="row">GS-{g}</th>{"".join(cells)}</tr>')

    return f"""<figure class="ex">
<p class="ex-note">Annual rates in U.S. dollars, read cell by cell from the published
OPM table rather than calculated. The cell marked ◀ is GS-{REF_GRADE} step {REF_STEP},
the one quoted at the top of this page. Cells marked ▲ have been cut down to the
statutory ceiling of {money(cap)} — the printed number is lower than the formula
would give.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Scrollable table"><table class="pay">
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


def page_hero(T: dict, ranks: dict, esc, money,
              code: str = "DCB", g: str = None, s: str = None) -> str:
    """Готовый ответ первого экрана, посчитанный на сборке.

    Зона по умолчанию — Washington-Baltimore: там работает больше федеральных
    служащих, чем в любой другой области, и это же значение уже стоит в
    селекте. Скрипт при инициализации перерисовывает эти три узла тем же
    содержимым, поэтому подмены на глазах у читателя не происходит.

    Ранг подписан «of 57», хотя областей 58. Разница настоящая: у одной нет
    опубликованного индекса цен. Молчать об этом нельзя — это первое число,
    которое человек на странице проверяет.
    """
    g = g or REF_GRADE
    s = s or REF_STEP
    loc = T["localities"][code]
    cell = loc["grades"][g][s]
    nom = ranks["nominal"].get(code)
    adj = ranks["adjusted"].get(code)
    line = (f'Of the {ranks["n"]} areas with a published price level: '
            f'<b>#{nom}</b> on the payslip, <b>#{adj}</b> once local prices '
            f'are counted.'
            if nom and adj else
            'This area has no published price level, so it carries no '
            'purchasing-power rank.')
    return (f'<p class="fp-what" data-what>GS-{g}, step {s} in '
            f'{esc(loc["area_name"])}, {T["year"]}</p>'
            f'<p class="fp-big" data-big>{money(cell["annual"])}</p>'
            f'<p class="fp-ranks" data-ranks>{line}</p>')


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
    global DATA_DATE, FONT_CSS, JS_TAG, FONT_PRELOAD
    T = json.loads((DATA / "paytables-2026.json").read_text(encoding="utf-8"))
    R = json.loads((DATA / "rpp-map.json").read_text(encoding="utf-8"))
    L = json.loads((DATA / "localities-2026.json").read_text(encoding="utf-8"))
    DATA_DATE = data_date(T, R, L)
    # Готовый блок @font-face читается с диска: сборка страниц в сеть не
    # ходит, шрифт качает fetch.py. Нет файла — страницы соберутся на
    # запасном системном стеке.
    FONT_CSS = fonts.css_from_disk()
    _woff = sorted(fonts.FONTS.glob("*.woff2")) if fonts.available() else []
    FONT_PRELOAD = "".join(
        f'<link rel="preload" href="/fonts/{f.name}" as="font" '
        f'type="font/woff2" crossorigin>' for f in _woff)
    ranks = compute_ranks(T, R)

    bundle_name, bundle_body = calc_bundle(T, R, ranks)
    JS_TAG = calc_script(bundle_name)

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
        grade_links = [(f"/gs-{x}/", f"GS-{x}", x == g)
                       for x in sorted(T["base"]["grades"], key=int)]
        write(f"gs-{g}", P.grade_page(
            g, T, R, ranks, shell, esc, money, slug,
            rail=side_rail("Every grade", grade_links,
                           "Each page shows that grade in all 58 areas at once."),
            widget=calc.calc_widget(
                zones=calc.zone_options(T, "DCB"), grade=g, step="5",
                hero=page_hero(T, ranks, esc, money, g=g, s="5"),
                heading=f"What a GS-{g} earns where you are",
                note=("Pick the locality pay area, or open the full calculator to "
                      "find it from a ZIP code.")),
            js=JS_TAG))
        urls.append(f"/gs-{g}/")

    grade_links = [(f"/gs-{x}/", f"GS-{x}", False)
                   for x in sorted(T["base"]["grades"], key=int)]
    write("grades", P.grades_index(
        T, ranks, shell, esc, money,
        rail=side_rail("Every grade", grade_links,
                       "Each page shows that grade in all 58 areas at once.")))
    urls.append("/grades/")

    # Инструмент. Виджет здесь полный: поиск по индексу и выбор зоны, тогда как
    # на странице зоны зона уже известна и спрашивать её незачем.
    write("calculator", P.calculator(
        T, R, shell, esc, money,
        calc.calc_widget(zones=calc.zone_options(T, "DCB"), with_zip=True,
                         hero=page_hero(T, ranks, esc, money),
                         heading="Work out a General Schedule salary",
                         note=("Gross pay from the published federal tables. Not "
                               "take-home: deductions depend on choices this page "
                               "does not ask about.")),
        js=JS_TAG,
        rail=side_rail(
        "Popular areas",
        [(f"/locality/{slug(l['area_name'])}/", l["area_name"], False)
        for c, l in sorted(T["localities"].items(),
        key=lambda kv: -kv[1]["grades"]["12"]["5"]["annual"])[:10]],
        "The ten highest-paying locality pay areas.")))
    urls.append("/calculator/")

    # --- сравнения зон: отдельное поисковое намерение «А или Б»
    cmp_items = []
    # Рельс сравнений строится заранее: он одинаков на всех страницах пары и
    # служит навигацией между ними.
    cmp_rail = ""
    for a, b in compare.pairs(T, ranks):
        rel, html_page = compare.compare_page(a, b, T, R, ranks, L, shell, esc,
                                              money, slug, cmp_rail)
        write(rel, html_page)
        urls.append(f"/{rel}/")
        cmp_items.append((rel, rel.split("/")[-1].replace("-vs-", " vs ")
                          .replace("-", " ").title()))
    # Второй проход: теперь список пар известен, и рельс можно наполнить.
    cmp_rail = side_rail(
        "Other comparisons",
        [(f"/{rel}/", title, False) for rel, title in cmp_items[:12]],
        "Highest-paying areas against each other and against Rest of U.S.")
    for a, b in compare.pairs(T, ranks):
        rel, html_page = compare.compare_page(a, b, T, R, ranks, L, shell, esc,
                                              money, slug, cmp_rail)
        write(rel, html_page)

    write("compare", compare.compare_index(cmp_items, shell, esc))
    urls.append("/compare/")

    # --- штаты: у конкурента это позиция №1 в выдаче, а у нас данных больше.
    sz = states.state_zones(L)
    # Штаты без единой названной зоны целиком внутри Rest of U.S. — это тоже
    # ответ, и он тоже кому-то нужен.
    # Штаты без единой названной зоны получают ОДНУ общую страницу: различать
    # их нечем, и восемь страниц с подставленным названием — это шаблонный
    # контент, а не восемь ответов. Замер показал между ними 82% совпадения.
    no_area = [s for s in states.NAMES if s not in sz]
    # Зона -> штаты, которые она захватывает. Нужна, чтобы страницы
    # штатов под одной зоной не говорили одно и то же.
    zone_reach = {}
    for s_code, zmap in sz.items():
        for z in zmap:
            zone_reach.setdefault(z, set()).add(s_code)
    st_items = []
    for st in sorted(states.NAMES, key=lambda s: states.NAMES[s]):
        if st in no_area:
            continue
        # Штаты без названной зоны своей страницы не имеют: ведём на общую.
        st_rail = side_rail(
            "Every state",
            [(("/states/no-locality-area/" if x in no_area
               else f"/states/{slug(states.NAMES[x])}/"),
              states.NAMES[x], x == st)
             for x in sorted(states.NAMES, key=lambda z: states.NAMES[z])],
            "Locality pay areas do not follow state lines.")
        rel, html_page = states.state_page(st, sz[st], T, R, ranks, shell, esc,
                                           money, slug, st_rail, zone_reach)
        write(rel, html_page)
        urls.append(f"/{rel}/")
        st_items.append((rel, states.NAMES[st]))
    write("states/no-locality-area",
           states.no_area_page(no_area, T, shell, esc, money, slug))
    urls.append("/states/no-locality-area/")
    # В указателе каждый из восьми штатов назван поимённо и ведёт на общую
    # страницу: человек ищет свой штат, а не категорию.
    for c in sorted(no_area, key=lambda z: states.NAMES[z]):
        st_items.append(("states/no-locality-area", states.NAMES[c]))
    st_items.sort(key=lambda x: x[1])
    write("states", states.states_index(st_items, shell, esc))
    urls.append("/states/")

    # --- лестница грейдов: типа страниц нет ни у одного конкурента
    lad_items = [(f"promotion/gs-{g}-to-gs-{g+1}", f"GS-{g} to GS-{g+1}")
                 for g in range(1, 15)]
    for g in range(1, 15):
        lad_rail = side_rail(
            "Every promotion",
            [(f"/promotion/gs-{x}-to-gs-{x+1}/", f"GS-{x} to GS-{x+1}", x == g)
             for x in range(1, 15)],
            "The step you land on is set by rule, not by negotiation.")
        rel, html_page = ladder.ladder_page(g, T, R, ranks, shell, esc, money,
                                            slug, lad_rail)
        write(rel, html_page)
        urls.append(f"/{rel}/")
    write("promotion", ladder.ladder_index(lad_items, T, shell, esc, money))
    urls.append("/promotion/")

    # Файл индексов подгружается инструментом по запросу пользователя, поэтому
    # он лежит рядом, а не внутри страницы: 203 КБ незачем возить всем.
    shutil.copyfile(DATA / "zip-zone.json", DIST / "zip-zone.json")
    icons.write_all(DIST)
    (DIST / bundle_name).write_text(bundle_body, encoding="utf-8")
    if fonts.available():
        (DIST / "fonts").mkdir(exist_ok=True)
        for f in list(fonts.FONTS.glob("*.woff2")) + [fonts.FONTS / "LICENSE.txt"]:
            shutil.copyfile(f, DIST / "fonts" / f.name)

    # --- главная и статические
    (DIST / "index.html").write_text(
        P.home(T, R, ranks, L, shell, esc, money, slug,
               widget=calc.calc_widget(
                   zones=calc.zone_options(T, "DCB"), with_zip=True,
                   heading="What does your grade and step pay?",
                   hero=page_hero(T, ranks, esc, money),
                   note=("Gross pay from the published federal tables. Not "
                         "take-home: deductions depend on choices this page "
                         "does not ask about. New to federal service? A first "
                         "appointment is almost always step 1 \u2014 the "
                         "default here is step 5, the middle of the grade.")),
               js=JS_TAG), encoding="utf-8")
    for rel, html_ in (
        ("how-locality-pay-works", P.how_it_works(T, shell, money)),
        ("about", P.about(shell)),
        ("contact", P.contact(shell, CONTACT, OWNER)),
        ("methodology", P.methodology(T, R, shell, money, OWNER, CONTACT)),
        ("privacy", P.privacy(shell)),
        ("terms", P.terms(shell)),
    ):
        write(rel, html_)
        urls.append(f"/{rel}/")

    (DIST / "404.html").write_text(P.not_found(shell), encoding="utf-8")
    (DIST / "sitemap.xml").write_text(P.sitemap(urls, DOMAIN, DATA_DATE),
                                      encoding="utf-8")
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    (DIST / "_redirects").write_text("/index.html  /  301\n", encoding="utf-8")
    (DIST / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  X-Frame-Options: DENY\n"
        "  Cache-Control: public, max-age=0, must-revalidate\n"
        "\n"
        "# Fonts and the ZIP lookup change once a year and carry stable\n"
        "# names, so they may be cached indefinitely.\n"
        "/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/zip-zone.json\n  Cache-Control: public, max-age=604800\n"
        "\n"
        "# The tool filename carries the data fingerprint: when the data\n"
        "# changes the address changes with it, so this never expires.\n"
        "/fp.*.js\n  Cache-Control: public, max-age=31536000, immutable\n",
        encoding="utf-8")

    print(f"страниц: {len(urls)} + 404")

    # ------------------------------------------------------------------ гейты
    problems: list[str] = []
    htmls = sorted(DIST.rglob("*.html"))
    all_urls = {u.rstrip("/") for u in urls} | {"/404.html"}

    # 0. просимая гарнитура и отгружаемая — одно и то же.
    #    Прежний гейт шрифта убеждался, что блок @font-face есть и файл
    #    уехал, но не сверял имена. Один тестовый вызов загрузчика — и сайт
    #    собрался зелёным, отгружая две гарнитуры, которые CSS не просит, и
    #    рисуясь системным стеком.
    if FONT_CSS:
        shipped = {m.lower() for m in
                   re.findall(r"font-family:'([^']+)'", FONT_CSS)}
        asked = set()
        for stack in re.findall(r"--(?:face|serif|sans|mono)\s*:\s*([^;}]+)",
                                design.CSS):
            first = stack.split(",")[0].strip().strip('"\'')
            if first and not first.startswith("var("):
                asked.add(first.lower())
        for name in sorted(asked - shipped):
            problems.append(f"шрифт: CSS просит {name!r}, а он не отгружается")
        for name in sorted(shipped - asked):
            problems.append(f"шрифт: отгружается {name!r}, а CSS его не просит")

    # 0. подрезанная гарнитура обязана покрывать каждый знак страницы.
    #    fonts.py качает шрифты с параметром text=, то есть ровно под тот
    #    набор знаков, что был в выкладке на момент загрузки. Появление
    #    нового знака не ломает сборку и не даёт ошибки — он просто
    #    отрисуется системным шрифтом посреди строки.
    covered = set()
    for rng in re.findall(r"unicode-range:([^;}]+)", FONT_CSS):
        for part in rng.split(","):
            part = part.strip().lower().lstrip("u+")
            if not part:
                continue
            try:
                if "-" in part:
                    a, b = part.split("-", 1)
                    covered.update(range(int(a, 16), int(b, 16) + 1))
                else:
                    covered.add(int(part, 16))
            except ValueError:
                continue
    if covered:
        # Знаки, которых в текстовых гарнитурах не бывает: они намеренно
        # отданы системному стеку либо нарисованы.
        DRAWN = set(chr(c) for c in (0x25B2, 0x25BC, 0x25C0, 0x25B6))
        seen = {}
        for f in htmls:
            body = f.read_text(encoding="utf-8")
            body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S)
            body = re.sub(r"<[^>]+>", " ", body)
            body = re.sub(r"&[a-z]+;|&#\d+;", " ", body)
            for ch in body:
                if ch.isspace() or ch in DRAWN or ord(ch) in covered:
                    continue
                seen.setdefault(ch, f.relative_to(DIST))
        for ch, where in sorted(seen.items()):
            problems.append(
                f"шрифт: знак U+{ord(ch):04X} {ch!r} не входит в подрезанную "
                f"гарнитуру — {where}")

    # 0. табличные цифры не должны теряться в сокращении font:.
    #    CSS Fonts 4: `font:` сбрасывает font-variant-numeric в исходное
    #    значение. Объявление на body уничтожалось на КАЖДОМ элементе с
    #    числом, и сайт про деньги набирал суммы пропорциональными цифрами.
    #    Проверяем сам стиль: в отрендеренном HTML этого не видно.
    #    Сравниваем ПОЛОЖЕНИЕ последнего сокращения font: и последнего
    #    объявления font-variant-numeric для одного и того же селектора: при
    #    равной специфичности выигрывает то, что ниже по файлу.
    NUM_SEL = ("table", ".ab-big", ".fact .kpi", ".ledger dd",
               ".fp-out p.fp-big", ".fp-lines dd", ".fp-hero p.fp-big",
               ".tlegend")
    bare = re.sub(r"/\*.*?\*/", "", design.CSS, flags=re.S)
    rules = [(m.start(), [s.strip() for s in m.group(1).split(",")], m.group(2))
             for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", bare)]
    for sel in NUM_SEL:
        short = variant = -1
        for pos, sels, body in rules:
            if sel not in sels:
                continue
            if re.search(r"\bfont:", body):
                short = pos
            if "font-variant-numeric" in body:
                variant = pos
        if short >= 0 and variant < short:
            problems.append(
                f"стиль: {sel} набирается сокращением font: и теряет "
                f"табличные цифры")

    # 0a. американский сайт американскими словами. Список форм, а не
    #     словарь: ловим ровно то, что уже один раз просочилось, плюс
    #     ближайших родственников. Смотрим и HTML, и клиентский бандл —
    #     одно вхождение жило в JS и попадало на страницу из браузера.
    BRIT = ("cheque", "favour", "labour", "neighbour", "centre", "colour",
            "organise", "analyse", "programme", "whilst", "practise",
            "licence", "defence", "traveller", "enrolment", "fulfil")
    for f in sorted(DIST.rglob("*.html")) + sorted(DIST.glob("fp.*.js")):
        low = f.read_text(encoding="utf-8").lower()
        for w in BRIT:
            if w in low:
                problems.append(
                    f"{f.relative_to(DIST)}: британская форма {w!r}")

    # 0b. кириллица во ВСЕЙ выкладке, не только в HTML. Файл _headers
    #     однажды уехал с русскими комментариями: гейт смотрел *.html и не
    #     увидел его. Проверка, которая зависит от того, отдаёт ли данный
    #     хостинг служебный файл наружу, ничего не гарантирует.
    for f in sorted(DIST.rglob("*")):
        if not f.is_file() or f.suffix in (".woff2", ".png", ".ico"):
            continue
        try:
            body = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if re.search(r"[\u0400-\u04FF]", body):
            problems.append(f"{f.relative_to(DIST)}: кириллица в выкладке")

    # 0. карта сайта против сборки, в обе стороны и без дублей.
    #    Хаб /promotion/ однажды выпал из карты из-за копипасты в соседней
    #    строке, и ни один гейт этого не увидел: страница была на месте, а
    #    дубль /compare/ добивал счётчик до правильного числа.
    smap = re.findall(r"<loc>([^<]+)</loc>",
                      (DIST / "sitemap.xml").read_text(encoding="utf-8"))
    for u in sorted({u for u in smap if smap.count(u) > 1}):
        problems.append(f"карта сайта: адрес повторяется — {u}")
    built = {"/" + f.relative_to(DIST).as_posix()[:-len("index.html")]
             for f in htmls if f.name == "index.html"}
    listed = {u[len(DOMAIN):] or "/" for u in smap if u.startswith(DOMAIN)}
    for miss in sorted(built - listed):
        problems.append(f"карта сайта: страница есть, адреса нет — {miss}")
    for ghost in sorted(listed - built):
        problems.append(f"карта сайта: адрес есть, страницы нет — {ghost}")

    for f in htmls:
        h = f.read_text(encoding="utf-8")
        rel = f.relative_to(DIST)

        # 1. отрендеренный вывод, а не исходники: кириллица не должна уехать
        if re.search(r"[\u0400-\u04FF]", h):
            problems.append(f"{rel}: кириллица в отгружаемом HTML")
        # 2. следы сломанных вычислений — только в ВИДИМОМ тексте.
        #    NaN и undefined внутри <script> законны: это собственные значения
        #    языка. Гейт существует ради того, чтобы читатель не увидел «NaN»
        #    вместо суммы, а не ради чистоты исходника.
        visible = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
        for bad in ("NaN", "undefined", "None", "$0<", ">$0 "):
            if bad in visible:
                problems.append(f"{rel}: в выводе встречается {bad!r}")
        # 3. тире там, где должна быть длина CSS или число
        if re.search(r"[\u2013\u2014](?=px|\d*px)|\d[\u2013\u2014]px", h):
            problems.append(f"{rel}: тире вместо длины CSS")
        # 4. дисклеймер обязателен на каждой странице — FTC Impersonation Rule
        if "not affiliated with" not in h:
            problems.append(f"{rel}: нет дисклеймера о неаффилированности")
        # 5. внутренние ссылки должны вести на существующее — на страницу
        #    ИЛИ на файл. Иконки и шрифты лежат в сборке файлами, и проверка
        #    только по списку страниц объявляла их битыми.
        for href in set(re.findall(r'href="(/[^"#?]*)"', h)):
            if href.rstrip("/") in all_urls:
                continue
            if (DIST / href.lstrip("/")).exists():
                continue
            problems.append(f"{rel}: ссылка в никуда {href}")

    # 6. объём текста — только для КОНТЕНТНЫХ страниц.
    #    404, политика, условия и «о сайте» существуют не ради объёма, и
    #    требовать от них 700 слов — значит лить воду в юридический документ.
    # Служебные страницы существуют не ради объёма. Дописывать контакты до
    # семисот слов — значит лить воду туда, где нужен адрес.
    SERVICE = {"404.html", "privacy", "terms", "about", "contact"}
    thin = []
    for f in htmls:
        rel = f.relative_to(DIST)
        if rel.name == "404.html" or rel.parts[0] in SERVICE:
            continue
        h = f.read_text(encoding="utf-8")
        body = h[h.find("<main"):h.find("</main>")]
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
        good = "works in your favor" in h
        bad = "matters a great deal" in h
        if good and bad:
            contra.append(f"{f.relative_to(DIST)}: обе формулировки сразу")
        # Опора структурная, а не на формулировку: строка «Places gained» или
        # «Places lost» в бухгалтерском блоке считается из чисел, а прозу можно
        # переписать — и однажды переписали, после чего гейт покраснел на 42
        # верных страницах. Ключ должен зависеть от данных, а не от стиля.
        elif good and "Places gained" not in h:
            contra.append(f"{f.relative_to(DIST)}: «в вашу пользу», но мест не прибавилось")
        elif bad and "Places lost" not in h:
            contra.append(f"{f.relative_to(DIST)}: «съедает надбавку», но мест не потеряно")
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
        # Закрывающий тег ищем ПОСЛЕ открывающего: в рельсе теперь тоже
        # есть список, и в разметке он стоит раньше крошек.
        i = h.find('<ol class="crumbs">')
        vis = h.count("<li>", i, h.find("</ol>", i) + 1) if i >= 0 else 0
        m = re.search(r'"BreadcrumbList".*?"itemListElement":\[(.*?)\]\}', h)
        mark = m.group(1).count('"ListItem"') if m else 0
        if vis != mark:
            crumb_bad.append(f"{f.relative_to(DIST)}: видно {vis}, размечено {mark}")
    if crumb_bad:
        problems.append(f"крошки разошлись с разметкой: {len(crumb_bad)} — {crumb_bad[0]}")

    # 11. клиентский расчёт. Инструмент считает ставки сам из базовой таблицы и
    #     процента, а не возит готовые. Повторяем здесь ТУ ЖЕ арифметику, что в
    #     JS, и сверяем со всеми 8 700 опубликованными клетками: годовую,
    #     часовую, ставку переработки и признак потолка.
    def _half_up(x: float) -> int:
        return math.floor(x + 0.5)

    cap = T["ex_iv_cap"]
    calc_bad = []

    # Данные берём ИЗ ГОТОВОЙ СТРАНИЦЫ — ровно ту строку, которую получит
    # браузер. Первая версия гейта читала исходный словарь и потому пропустила
    # подложенную порчу отгружаемых данных: проверялось намерение, а не
    # артефакт.
    # Данные уехали в отдельный файл, и проверять надо ЕГО: именно он попадёт
    # в браузер. Заодно убеждаемся, что страницы на него ссылаются.
    bundles = list(DIST.glob("fp.*.js"))
    if len(bundles) != 1:
        problems.append(f"файлов инструмента в сборке: {len(bundles)}, нужен один")
        shipped = None
    else:
        src = bundles[0].read_text(encoding="utf-8")
        m = re.search(r"window\.__FP=(\{.*?\});", src, re.S)
        shipped = json.loads(m.group(1)) if m else None
        if shipped is None:
            problems.append("в файле инструмента нет данных")
        linked = sum(1 for f in htmls if bundles[0].name in
                     f.read_text(encoding="utf-8"))
        if linked == 0:
            problems.append("ни одна страница не подключает файл инструмента")

    if shipped:
        if shipped.get("cap") != cap:
            calc_bad.append(f"потолок в данных {shipped.get('cap')} вместо {cap}")
        ship_zone = {z["c"]: z for z in shipped["zones"]}
        ship_base = shipped["base"]

    for code, loc in (T["localities"].items() if shipped else []):
        z = ship_zone.get(code)
        if not z:
            calc_bad.append(f"{code}: зоны нет в отгруженных данных")
            break
        pct = z["p"]
        if abs(pct - loc["locality_pct"]) > 1e-9:
            calc_bad.append(f"{code}: процент {pct} вместо {loc['locality_pct']}")
            break
        ten_raw = _half_up(ship_base[9][0] * (1 + pct / 100))
        ten = min(ten_raw, cap)
        ten_h = _half_up(ten * 100 / 2087)
        for g in range(1, 16):
            for s in range(1, 11):
                cell = loc["grades"][str(g)][str(s)]
                base_v = ship_base[g - 1][s - 1]
                raw = _half_up(base_v * (1 + pct / 100))
                pay = min(raw, cap)
                h = _half_up(pay * 100 / 2087)
                ot = (_half_up(h * 1.5) if h <= ten_h
                      else max(h, _half_up(ten_h * 1.5)))
                if pay != cell["annual"]:
                    calc_bad.append(f"{code} GS-{g}/{s} годовая {cell['annual']}≠{pay}")
                elif abs(h / 100 - cell["hourly"]) > 1e-9:
                    calc_bad.append(f"{code} GS-{g}/{s} часовая {cell['hourly']}≠{h/100}")
                elif abs(ot / 100 - cell["overtime"]) > 1e-9:
                    calc_bad.append(f"{code} GS-{g}/{s} переработка "
                                    f"{cell['overtime']}≠{ot/100}")
                elif (raw > cap) != cell["capped"]:
                    calc_bad.append(f"{code} GS-{g}/{s} признак потолка")
                if len(calc_bad) > 3:
                    break
    if calc_bad:
        problems.append(f"клиентский расчёт разошёлся с таблицами OPM: "
                        f"{len(calc_bad)}+ — {calc_bad[0]}")

    # 12. непреобразованные escape-последовательности в ВИДИМОМ тексте.
    #     Внутри <script> запись вида \uXXXX законна — это исходник JavaScript.
    #     В тексте страницы она означает, что где-то перепутан уровень
    #     экранирования, и читателю показывают шесть символов вместо тире.
    #     Ровно так на 16 страницах сравнения оказалось «\u2014»: HTML при этом
    #     валиден, слов достаточно, вычисления целы — ни один прежний гейт не
    #     видел ничего.
    esc_pat = re.compile(r"\\u[0-9a-fA-F]{4}")
    script_pat = re.compile(r"<script.*?</script>", re.S)
    raw_esc = []
    for f in htmls:
        visible = script_pat.sub(" ", f.read_text(encoding="utf-8"))
        m = esc_pat.search(visible)
        if m:
            raw_esc.append(f"{f.relative_to(DIST)}: {m.group(0)}")
    if raw_esc:
        problems.append(f"escape-последовательности в тексте: {len(raw_esc)} — "
                        f"{raw_esc[0]}")

    # 13. управляющие символы. В CSS запись вида \00a0 означает неразрывный
    #     пробел, но внутри обычной строки питона \0 — это нулевой байт, а
    #     \25 — восьмеричное 025. Так на все 103 страницы уехали 0x00 и 0x15:
    #     HTML при этом валиден, гейты зелёные, а файл технически бинарный.
    ctl = []
    for f in htmls:
        s = f.read_text(encoding="utf-8")
        hit = [c for c in s if ord(c) < 32 and c not in "\n\r\t"]
        if hit:
            ctl.append(f"{f.relative_to(DIST)}: {hex(ord(hit[0]))}")
    if ctl:
        problems.append(f"управляющие символы в выводе: {len(ctl)} — {ctl[0]}")

    # 14. внешние запросы и правдивость заявления о приватности.
    #     Правило «сайт не ходит наружу» существовало без проверки, а страница
    #     приватности при этом подробно описывала Google Analytics 4, которого
    #     в сборке не было ни строчки. Заявление обязано описывать то, что
    #     реально загружает браузер, — в обе стороны.
    ext_pat = re.compile(
        r'(?:src|href)\s*=\s*["\']https?://(?!fedpayscale\.com)([^/"\']+)',
        re.I)
    outside = {}
    for f in htmls:
        h = f.read_text(encoding="utf-8")
        # Ссылки на источники — это ссылки, а не загрузки. Считаем только то,
        # что браузер тянет сам: скрипты, стили, шрифты, картинки, iframe.
        for m in re.finditer(
                r"<(script|link|img|iframe|source)\b[^>]*>", h, re.I):
            hit = ext_pat.search(m.group(0))
            if hit:
                outside.setdefault(hit.group(1), str(f.relative_to(DIST)))
    if outside:
        first = next(iter(outside.items()))
        problems.append(f"внешние запросы на {len(outside)} доменов: "
                        f"{first[0]} на {first[1]}")

    priv = DIST / "privacy" / "index.html"
    if priv.exists():
        p_txt = priv.read_text(encoding="utf-8")
        claims_analytics = ("Google Analytics" in p_txt
                            and "no analytics of any kind" not in p_txt)
        if claims_analytics and not outside:
            problems.append("страница приватности описывает аналитику, "
                            "которой в сборке нет")

    # 15. шрифт. Восстановление main() из git однажды тихо откатило две строки —
    #     чтение @font-face и копирование файлов, — и сборка осталась зелёной:
    #     страницы просто поехали на запасном системном стеке. Заметить это
    #     можно было только по отсутствию каталога в готовой папке.
    if fonts.available():
        miss = [str(f.relative_to(DIST)) for f in htmls
                if "@font-face" not in f.read_text(encoding="utf-8")]
        if miss:
            problems.append(f"шрифт не подключён на {len(miss)} страницах: {miss[0]}")
        shipped = list((DIST / "fonts").glob("*.woff2")) if (DIST / "fonts").exists() else []
        if not shipped:
            problems.append("файлы шрифта не скопированы в сборку")

    # 16. класс без правила. Перестройка оформления выбросила правила для
    #     блоков, оставшихся на других типах страниц: оговорка на 58 страницах
    #     потеряла рамку, карточка ответа на 37 рассыпалась. Все прежние гейты
    #     были зелёными — невидимый CSS ничего не ломает из того, что они умеют
    #     проверять.
    css_text = design.CSS
    # Только то, что появляется ВО ВРЕМЯ РАБОТЫ скрипта и потому не может
    # встретиться в отгружаемой разметке. Всё, что ставит генератор, обязано
    # проверяться: solo и wide лежали здесь по ошибке, а это модификаторы
    # раскладки на одиннадцати и одной странице.
    RUNTIME = {
        "sel",   # выбранная клетка таблицы ставок
        "you",   # строка своей области после пересчёта таблицы
    }
    seen_cls = {}
    for f in htmls:
        h = f.read_text(encoding="utf-8")
        body = h[h.find("<body>"):]
        for m in re.finditer(r'class="([^"]+)"', body):
            for c in m.group(1).split():
                seen_cls.setdefault(c, str(f.relative_to(DIST)))

    def styled(name: str) -> bool:
        """Есть ли в стилях селектор ИМЕННО этого класса.

        Подстрока не годится: ".bar" находится внутри ".bars", ".q" внутри
        ".q-lead", ".in" внутри ".in-". Девять коротких имён были защищены
        только на бумаге. Имя класса кончается там, где кончаются буквы,
        цифры, дефис и подчёркивание.
        """
        return re.search(r"\." + re.escape(name) + r"(?![\w-])",
                         css_text) is not None

    orphan = sorted(c for c in seen_cls if c not in RUNTIME and not styled(c))
    if orphan:
        problems.append(f"классы без правил в CSS: {len(orphan)} — "
                        f"{', '.join(orphan[:4])} (напр. {seen_cls[orphan[0]]})")

    if problems:
        print(f"\nГЕЙТ НЕ ПРОЙДЕН: {len(problems)} замечаний", file=sys.stderr)
        for p in problems[:20]:
            print("  " + p, file=sys.stderr)
        return 1

    print("гейты пройдены: кириллица, битые вычисления, дисклеймер, ссылки, "
          "объём, направление, полнота охвата, пунктуация, крошки, "
          "клиентский расчёт, экранирование, управляющие символы, "
                "внешние запросы, шрифт, стили, карта сайта, американское написание, табличные цифры, покрытие шрифта, совпадение гарнитуры")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
