"""Интерактивная часть сайта: расчёт оклада и поиск своей зоны по индексу.

Почему это появилось. Ревью конкурентов: калькулятор есть у всех трёх старожилов,
а у двух новичков он и есть весь продукт. У нас не было ни одного инструмента —
только таблицы. При этом «gs pay scale 2026 with locality Calculator» стоит прямо
в блоке связанных запросов Google.

Чем наш отличается. Конкуренты отвечают числом. Мы отвечаем числом И тем, чего оно
стоит: место в двух рейтингах, пересчёт на местные цены и прямое указание зоны, где
та же клетка таблицы оставляет больше на руках. Ни у кого этого нет.

Почему клиенту хватает пары килобайт. parse.py доказал, что «база x (1 + процент),
округление, потом потолок» воспроизводит таблицу OPM до доллара на всех 8 700
клетках. Часовая ставка и ставка переработки тоже выводятся точно — правила ниже
проверены на тех же 8 700 клетках, расхождений ноль:

  hourly   = округл_вверх(annual / 2087, до цента)
  overtime = своя <= GS-10/1 ? округл_вверх(своя * 1.5)
                             : max(своя, округл_вверх(GS-10/1 * 1.5))
             (5 U.S.C. 5542; сравнение и умножение — от УЖЕ округлённой часовой)

Поэтому вместо 630 КБ готовых таблиц клиент получает 150 базовых ставок, 58
процентов и потолок. Гейт в render.py пересчитывает то же самое питоном и сверяет
с опубликованными таблицами, чтобы эта экономия не разъехалась со страницами.

Считаем в ЦЕЛЫХ ЦЕНТАХ. В double 24.345 не представимо точно, и наивное
Math.round(x*100)/100 роняет цент на каждой третьей клетке — именно так и было
поймано при выводе правила.

Индекс подгружается отдельным файлом и только когда пользователь начал его вводить:
203 КБ незачем возить всем.
"""
from __future__ import annotations

import json


def calc_data(T: dict, R: dict, ranks: dict, slug) -> str:
    """Компактные данные для клиента: база, зоны, проценты, цены, ранги."""
    base = [[T["base"]["grades"][str(g)][str(s)]["annual"] for s in range(1, 11)]
            for g in range(1, 16)]

    zones = []
    for code, loc in sorted(T["localities"].items(),
                            key=lambda kv: kv[1]["area_name"]):
        rp = R["areas"].get(code, {})
        zones.append({
            "c": code,
            "n": loc["area_name"],
            "u": "/locality/" + slug(loc["area_name"]) + "/",
            "p": loc["locality_pct"],
            "r": rp.get("rpp"),
            "kn": ranks["nominal"].get(code),
            "ka": ranks["adjusted"].get(code),
        })

    return json.dumps({
        "year": T["year"],
        "cap": T["ex_iv_cap"],
        "base": base,
        "zones": zones,
        "nranked": ranks["n"],
        "beaYear": R["bea_year"],
    }, separators=(",", ":"))


CALC_JS = r"""
(function(){
  var D = window.__FP;
  if (!D) return;

  var ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  /* 5 CFR 531.405: one year each to step 4, two to step 7, three after. */
  var WAITS = [1,1,1,2,2,2,3,3,3];
  var HOURS = 2087;
  var zipData = null, zipState = "idle";

  /* Money is handled in whole cents throughout: 24.345 has no exact double
     representation, and rounding it naively loses a cent on a third of the
     cells. Every figure below is an integer number of cents until it is
     formatted for display. */
  function halfUp(x){ return Math.floor(x + 0.5); }
  function money(dollars){
    return "$" + Math.round(dollars).toLocaleString("en-US");
  }
  function cents(c){
    return "$" + (c/100).toLocaleString("en-US",
      {minimumFractionDigits:2, maximumFractionDigits:2});
  }

  function hourlyCents(annual){ return halfUp(annual * 100 / HOURS); }

  function overtimeCents(annual, tenAnnual){
    var own = hourlyCents(annual), ten = hourlyCents(tenAnnual);
    if (own <= ten) return halfUp(own * 1.5);
    return Math.max(own, halfUp(ten * 1.5));
  }

  /* The order is fixed by law: apply the percentage, round, and only then
     apply the ceiling. Doing it the other way round produces different
     figures at the top of the schedule, which is one reason published
     numbers disagree between reference sites. */
  function rate(zone, g, s){
    var b = D.base[g-1][s-1];
    var raw = halfUp(b * (1 + zone.p/100));
    return { pay: Math.min(raw, D.cap), capped: raw > D.cap,
             base: b, uncapped: raw };
  }

  function byCode(c){
    for (var i=0;i<D.zones.length;i++) if (D.zones[i].c === c) return D.zones[i];
    return null;
  }

  function yearsTo(step){
    var y = 0;
    for (var i=0;i<step-1;i++) y += WAITS[i];
    return y;
  }

  /* Which locality leaves the same grade and step better off once local
     prices are counted. */
  function betterThan(zone, g, s){
    if (!zone.r) return null;
    var mine = rate(zone, g, s).pay / (zone.r/100), best = null;
    for (var i=0;i<D.zones.length;i++){
      var z = D.zones[i];
      if (!z.r || z.c === zone.c) continue;
      var v = rate(z, g, s).pay / (z.r/100);
      if (v > mine && (!best || v > best.v)) best = { z: z, v: v };
    }
    return best;
  }

  function esc(s){
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }
  function pct(p){ return (Math.round(p*100)/100) + "%"; }
  /* A full stop, unless the name already ends in one. The Rest of U.S. area
     name ends in a full stop, so the naive template appended a second one.
     The same defect was caught in the static pages and is gated there;
     script-built text is outside the reach of that gate, so the rule lives
     here as well. */
  function dot(name){ return /\.\s*$/.test(name) ? "" : "."; }

  function render(box, zone, g, s){
    var out = box.querySelector("[data-out]");
    if (!zone){ out.innerHTML = ""; return; }

    var r = rate(zone, g, s);
    var tenAnnual = rate(zone, 10, 1).pay;
    var h = hourlyCents(r.pay), ot = overtimeCents(r.pay, tenAnnual);
    var parts = [];

    parts.push('<p class="fp-what">GS-' + g + ', step ' + s + ' in ' +
               esc(zone.n) + ', ' + D.year + '</p>');
    parts.push('<p class="fp-big">' + money(r.pay) + '</p>');

    var lines = [["Base rate before locality", money(r.base)],
                 ["Locality pay " + pct(zone.p), "+ " + money(r.uncapped - r.base)]];
    if (r.capped) lines.push(["Cut to the statutory ceiling",
                              "− " + money(r.uncapped - r.pay)]);
    /* OPM derives the biweekly rate as the hourly rate times 80, not as the
       annual rate divided by 26. The two differ, and only the first matches
       the payslip. */
    lines.push(["Every two weeks", cents(h * 80)]);
    lines.push(["Per hour", cents(h)]);
    lines.push(["Per overtime hour", cents(ot)]);
    parts.push('<dl class="fp-lines">' + lines.map(function(l){
      return "<dt>" + l[0] + "</dt><dd class=\"num\">" + l[1] + "</dd>";
    }).join("") + "</dl>");

    var notes = [];
    if (r.capped){
      notes.push("<strong>This cell is capped.</strong> The formula gives " +
        money(r.uncapped) + ", but no General Schedule rate may exceed Level IV " +
        "of the Executive Schedule — " + money(D.cap) + " in " + D.year +
        ". Step increases inside that band add nothing to the payslip.");
    }
    if (ot <= h){
      notes.push("Overtime here is worth no more than an ordinary hour: above " +
        "GS-10 step 1 the overtime rate is capped, so the hour is paid at the " +
        "greater of your own rate and one and a half times GS-10 step 1.");
    }

    if (zone.r){
      var adj = r.pay / (zone.r/100);
      notes.push("Local prices are <strong>" + zone.r.toFixed(1) + "</strong> " +
        "against a national average of 100, so this salary buys about " +
        "<strong>" + money(adj) + "</strong> of what the same money buys at " +
        "average U.S. prices. On that measure the area ranks #" + zone.ka +
        " of " + D.nranked + "; on the size of the cheque alone it ranks #" +
        zone.kn + ".");
      /* A gap smaller than one percent of the salary is inside the error of
         the price data itself: the index is a year behind the pay tables,
         is rounded to a tenth, and metropolitan boundaries do not match
         locality boundaries. Reporting such a gap as a reason to move would
         be false precision, so below that threshold we say there is none. */
      var b = betterThan(zone, g, s);
      var floor = r.pay * 0.01;
      if (b && (b.v - adj) >= floor){
        var br = rate(b.z, g, s);
        notes.push("The same grade and step in <a href=\"" + b.z.u + "\">" +
          esc(b.z.n) + "</a> pays " + money(br.pay) +
          (br.pay < r.pay ? ", which is " + money(r.pay - br.pay) +
           " less on paper, and still" : " and") +
          " leaves you <strong>" + money(b.v - adj) + " a year better off</strong> " +
          "once local prices are counted.");
      } else if (b){
        notes.push("A few localities edge past this one on purchasing power, but " +
          "by less than one percent of the salary \u2014 which is inside the " +
          "error of the price data itself. On the money, they are the same place.");
      } else {
        notes.push("No other locality with published price data leaves a GS-" + g +
          " step " + s + " better off than this one.");
      }
    } else {
      notes.push("This area has no single price index published for it, so the " +
        "purchasing-power comparison leaves it out rather than guessing.");
    }

    if (s < 10){
      var w = WAITS[s-1], next = rate(zone, g, s+1).pay;
      notes.push("The next step is due after <strong>" + w + " year" +
        (w > 1 ? "s" : "") + "</strong> at this step and would pay " + money(next) +
        (next === r.pay ? " — the same, because the ceiling has already been " +
         "reached" : ", a rise of " + money(next - r.pay)) +
        ". Reaching step 10 from step 1 takes " + yearsTo(10) + " years.");
    } else {
      notes.push("Step 10 is the top of GS-" + g + ". Anything further requires " +
        "promotion to a higher grade, which restarts the step clock.");
    }

    parts.push(notes.map(function(n){ return "<p>" + n + "</p>"; }).join(""));
    parts.push('<p class="fp-src"><a href="' + zone.u + '">Every ' + D.year +
      " rate for " + esc(zone.n) + "</a></p>");
    out.innerHTML = parts.join("");
  }

  function findZip(zip){
    if (!zipData) return null;
    var keys = zipData.keys, lo = 0, hi = keys.length/5 - 1;
    while (lo <= hi){
      var mid = (lo + hi) >> 1, k = keys.substr(mid*5, 5);
      if (k === zip) return zipData.zones[ALPHA.indexOf(zipData.vals[mid])];
      if (k < zip) lo = mid + 1; else hi = mid - 1;
    }
    return null;
  }

  function wire(box){
    var g = box.querySelector("[data-grade]");
    var s = box.querySelector("[data-step]");
    var z = box.querySelector("[data-zone]");
    var zip = box.querySelector("[data-zip]");
    var msg = box.querySelector("[data-zipmsg]");
    var fixed = box.getAttribute("data-fixed");

    function draw(){
      render(box, fixed ? byCode(fixed) : byCode(z.value), +g.value, +s.value);
    }
    [g, s, z].forEach(function(el){ if (el) el.addEventListener("change", draw); });

    function lookup(v){
      var code = findZip(v);
      if (!code){
        msg.textContent = "ZIP " + v + " is not in the Census ZIP-to-county file. " +
          "Some ZIPs serve post office boxes only and have no area of their own — " +
          "pick the area from the list instead.";
        return;
      }
      var zone = byCode(code);
      msg.innerHTML = "ZIP " + v + " is in <strong>" + esc(zone.n) + "</strong>" +
        dot(zone.n);
      if (z) z.value = code;
      draw();
    }

    if (zip){
      zip.addEventListener("input", function(){
        var v = zip.value.replace(/[^0-9]/g, "").slice(0,5);
        if (v.length < 5){ msg.textContent = ""; return; }
        if (zipState === "ready"){ lookup(v); return; }
        if (zipState !== "idle") return;
        zipState = "loading";
        msg.textContent = "Looking that up…";
        fetch("/zip-zone.json").then(function(r){ return r.json(); })
          .then(function(j){ zipData = j; zipState = "ready"; lookup(v); })
          .catch(function(){
            zipState = "failed";
            msg.textContent = "Could not load the ZIP index. Pick the area " +
              "from the list instead.";
          });
      });
    }

    box.hidden = false;
    draw();
  }

  var boxes = document.querySelectorAll("[data-calc]");
  for (var i=0;i<boxes.length;i++) wire(boxes[i]);
})();
"""


def zone_options(T: dict, selected: str = "") -> str:
    """Список зон для выпадающего меню, по алфавиту."""
    opts = []
    for code, loc in sorted(T["localities"].items(),
                            key=lambda kv: kv[1]["area_name"]):
        sel = " selected" if code == selected else ""
        name = (loc["area_name"].replace("&", "&amp;")
                .replace("<", "&lt;").replace(">", "&gt;"))
        opts.append(f'<option value="{code}"{sel}>{name}</option>')
    return "".join(opts)


def calc_widget(fixed: str = "", zones: str = "", with_zip: bool = False,
                grade: str = "12", step: str = "5", heading: str = "",
                note: str = "") -> str:
    """Разметка инструмента.

    Скрыт атрибутом hidden и открывается скриптом. Без скрипта на странице не
    остаётся мёртвых полей, которые ничего не делают, — урок press-every-button.
    """
    grades = "".join(
        f'<option value="{g}"{" selected" if str(g) == grade else ""}>GS-{g}</option>'
        for g in range(1, 16))
    steps = "".join(
        f'<option value="{s}"{" selected" if str(s) == step else ""}>Step {s}</option>'
        for s in range(1, 11))

    zip_row = ("" if not with_zip else
               '<div class="fp-field"><label for="fp-zip">Work ZIP code</label>'
               '<input id="fp-zip" data-zip type="text" inputmode="numeric" '
               'maxlength="5" placeholder="35801" autocomplete="postal-code"></div>')
    zone_row = ("" if not zones else
                '<div class="fp-field fp-wide"><label for="fp-zone">'
                'Locality pay area</label>'
                f'<select id="fp-zone" data-zone>{zones}</select></div>')

    return (
        f'<div class="fp-calc" data-calc'
        f'{f" data-fixed=\"{fixed}\"" if fixed else ""} hidden>'
        f'{f"<h2>{heading}</h2>" if heading else ""}'
        f'<div class="fp-fields">{zip_row}{zone_row}'
        f'<div class="fp-field"><label for="fp-grade">Grade</label>'
        f'<select id="fp-grade" data-grade>{grades}</select></div>'
        f'<div class="fp-field"><label for="fp-step">Step</label>'
        f'<select id="fp-step" data-step>{steps}</select></div></div>'
        f'<p class="fp-zipmsg" data-zipmsg></p>'
        f'<div class="fp-out" data-out></div>'
        f'{f"<p class=\"fp-note\">{note}</p>" if note else ""}'
        f'</div>')
