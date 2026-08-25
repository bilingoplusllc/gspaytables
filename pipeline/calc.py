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

  /* Ranks for the cell actually on screen, not for the GS-12 step 5 the
     build happened to rank by. Below the ceiling these agree with the
     published ranking, because every rate is proportional to the same base
     table and dividing by a price index preserves order. At the top of the
     schedule the EX-IV ceiling flattens the highest-paying areas into one
     another and the order genuinely changes \u2014 which is the one place a
     stale rank would be both wrong and interesting. */
  var rankCache = {};
  function ranksFor(g, s){
    var key = g + ":" + s;
    if (rankCache[key]) return rankCache[key];
    var live = [];
    for (var i = 0; i < D.zones.length; i++){
      var z = D.zones[i];
      if (!z.r) continue;
      var pay = rate(z, g, s).pay;
      live.push({ c: z.c, pay: pay, buys: pay / (z.r / 100) });
    }
    var map = { n: live.length };
    /* Competition ranking, not position in the array. At GS-15 step 10 the
       EX-IV ceiling cuts every area to the same dollar, and numbering them
       1..57 by iteration order would invent a ranking out of nothing. */
    var byNom = live.slice().sort(function(a, b){ return b.pay - a.pay; });
    var rank = 0, tie = 0;
    for (var k = 0; k < byNom.length; k++){
      if (k && byNom[k].pay === byNom[k-1].pay){ tie++; }
      else { rank = k + 1; tie = 0; }
      map[byNom[k].c] = { nom: rank };
    }
    for (var k = 0; k < byNom.length; k++){
      var same = 0;
      for (var m = 0; m < byNom.length; m++)
        if (byNom[m].pay === byNom[k].pay) same++;
      map[byNom[k].c].nomTies = same - 1;
    }
    live.sort(function(a, b){ return b.buys - a.buys; });
    for (var k = 0; k < live.length; k++)
      map[live[k].c].pp = k + 1;
    rankCache[key] = map;
    return map;
  }

  function render(box, zone, g, s){
    var out = box.querySelector("[data-out]");
    if (!zone){ out.innerHTML = ""; return; }

    var r = rate(zone, g, s);
    var tenAnnual = rate(zone, 10, 1).pay;
    var h = hourlyCents(r.pay), ot = overtimeCents(r.pay, tenAnnual);
    var parts = [];

    /* Where the page ships a pre-rendered hero, repaint it in place instead
       of printing the headline into [data-out]. The hero exists so that the
       number is on the screen before this script runs at all; writing a
       second copy below it would both duplicate the figure and undo that. */
    var hBig = box.querySelector("[data-big]");
    /* The year is deliberately absent here: it is already printed in the
       edition line and in the heading, and on a phone the area name alone
       takes five lines and pushes the ranks below the fold. */
    var head = 'GS-' + g + ', step ' + s + ' in ' + esc(zone.n);
    if (hBig){
      var hWhat = box.querySelector("[data-what]");
      var hRank = box.querySelector("[data-ranks]");
      if (hWhat) hWhat.innerHTML = head;
      hBig.textContent = money(r.pay);
      if (hRank){
        var lr = ranksFor(g, s)[zone.c];
        /* Saying "of 57" next to a promise of 58 areas reads as our own
           arithmetic error until the line says why one is missing. */
        hRank.innerHTML = lr
          ? 'Of the ' + ranksFor(g, s).n + ' areas with a published price ' +
            'level: <b>#' + lr.nom + '</b> on the payslip' +
            (lr.nomTies ? ' (tied with ' + lr.nomTies + ' other' +
              (lr.nomTies > 1 ? ' areas' : ' area') + ' at the statutory ' +
              'ceiling)' : '') +
            ', <b>#' + lr.pp + '</b> once local prices are counted.'
          : 'This area has no published price level, so it carries no ' +
            'purchasing-power rank.';
      }
    } else {
      parts.push('<p class="fp-what">' + head + '</p>');
      parts.push('<p class="fp-big">' + money(r.pay) + '</p>');
    }

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
        "average U.S. prices. At this grade and step the area ranks #" +
        ranksFor(g, s)[zone.c].pp + " of " + ranksFor(g, s).n +
        " on that measure; on the size of the paycheck alone it ranks #" +
        ranksFor(g, s)[zone.c].nom +
        (ranksFor(g, s)[zone.c].nomTies
          ? ", level with " + ranksFor(g, s)[zone.c].nomTies +
            " other area" + (ranksFor(g, s)[zone.c].nomTies > 1 ? "s" : "") +
            " held at the same statutory ceiling"
          : "") + ".");
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
      if (typeof repaintHome === "function") repaintHome(+g.value, +s.value);
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

    /* Controls ship disabled so that a visitor without JavaScript is not
       offered a select that silently does nothing. Enabling them is the
       last thing wire() does, after every listener is attached. */
    var ctl = box.querySelectorAll("select,input");
    for (var k = 0; k < ctl.length; k++) ctl[k].disabled = false;

    box.hidden = false;
    draw();
  }

  /* ---- the national table, repainted for the grade and step on screen ----
     The table is the showcase of the site and until now it silently showed a
     GS-12 step 5 to everyone. The rates are proportional to the base table, so
     the ORDER barely moves between grades — what moves is every dollar figure,
     and, at the top of the schedule, the order itself, because the EX-IV
     ceiling flattens the highest-paying areas into each other. */
  var homeTable = document.querySelector("table[data-home]");

  function repaintHome(g, s){
    if (!homeTable) return;
    var body = homeTable.tBodies[0];
    var rows = Array.prototype.slice.call(body.rows);
    var live = [];
    for (var i = 0; i < rows.length; i++){
      var z = byCode(rows[i].getAttribute("data-code"));
      if (!z) continue;
      var pay = rate(z, g, s).pay;
      live.push({ tr: rows[i], z: z, pay: pay,
                  buys: z.r ? pay / (z.r / 100) : null });
    }
    /* One source for ranks on the page: the same function the answer card
       uses. Two independent rankings of the same cell is how a page ends up
       contradicting itself in public. */
    var map = ranksFor(g, s);
    var ranked = live.filter(function(v){ return v.buys !== null; });
    for (var k = 0; k < ranked.length; k++){
      ranked[k].nom = map[ranked[k].z.c].nom;
      ranked[k].pp = map[ranked[k].z.c].pp;
    }

    function put(td, v, txt){
      td.setAttribute("data-v", v);
      td.textContent = txt;
    }
    for (var i = 0; i < live.length; i++){
      var v = live[i], c = v.tr.cells;
      put(c[3], v.pay, money(v.pay));
      if (v.buys === null) continue;
      var shift = v.nom - v.pp;
      put(c[0], v.pp, String(v.pp));
      put(c[5], Math.round(v.buys), money(v.buys));
      put(c[6], shift, shift > 0 ? "+" + shift
                     : (shift < 0 ? "\u2212" + (-shift) : "\u2014"));
      c[6].className = "num " + (shift > 0 ? "up" : (shift < 0 ? "down" : "flat"));
    }
    /* Restore the default order unless the reader has chosen one: re-sorting
       under someone who has just clicked a column heading would read as the
       table fighting back. */
    if (!homeTable.hasAttribute("data-touched")){
      ranked.sort(function(a, b){ return a.pp - b.pp; });
      for (var k = 0; k < ranked.length; k++) body.appendChild(ranked[k].tr);
      for (var i = 0; i < live.length; i++)
        if (live[i].buys === null) body.appendChild(live[i].tr);
    }
  }

  var boxes = document.querySelectorAll("[data-calc]");
  for (var i=0;i<boxes.length;i++) wire(boxes[i]);

  /* ---- the sticky answer bar, and the pay table as its control surface ---- */
  var bar = document.querySelector("[data-bar]");
  if (bar){
    var zone = byCode(bar.getAttribute("data-zone"));
    var bg = bar.querySelector("[data-grade]");
    var bs = bar.querySelector("[data-step]");
    var big = bar.querySelector("[data-ab-big]");
    var slots = bar.querySelectorAll("[data-ab]");
    var table = document.querySelector("table.pay");
    var cells = table ? table.querySelectorAll("td.cell") : [];

    function paint(g, s){
      if (!zone) return;
      var r = rate(zone, g, s);
      var ten = rate(zone, 10, 1).pay;
      var h = hourlyCents(r.pay), ot = overtimeCents(r.pay, ten);
      big.textContent = money(r.pay);
      var vals = [cents(h * 80), cents(h), cents(ot)];
      for (var i=0;i<slots.length && i<vals.length;i++) slots[i].textContent = vals[i];
      for (var j=0;j<cells.length;j++){
        var on = +cells[j].getAttribute("data-g") === g &&
                 +cells[j].getAttribute("data-s") === s;
        cells[j].classList.toggle("sel", on);
        cells[j].setAttribute("aria-selected", on ? "true" : "false");
        cells[j].tabIndex = on ? 0 : -1;
        /* The server marks the default cell so it is visible without script.
           Once script is running the selection is live, and two markers on
           the same table would contradict each other. */
        cells[j].classList.remove("ref");
      }
    }
    function pick(g, s, moveFocus){
      bg.value = g; bs.value = s; paint(g, s);
      if (moveFocus){
        var td = table && table.querySelector(
          'td.cell[data-g="' + g + '"][data-s="' + s + '"]');
        if (td) td.focus();
      }
    }
    bg.addEventListener("change", function(){ paint(+bg.value, +bs.value); });
    bs.addEventListener("change", function(){ paint(+bg.value, +bs.value); });
    paint(+bg.value, +bs.value);

    /* One delegated listener rather than 150, and a roving tab stop: only the
       selected cell sits in the tab order, so keyboard users are not made to
       walk through a hundred and fifty numbers to leave the table. */
    if (table){
      table.addEventListener("click", function(e){
        var td = e.target.closest ? e.target.closest("td.cell") : null;
        if (td) pick(+td.getAttribute("data-g"), +td.getAttribute("data-s"), true);
      });
      table.addEventListener("keydown", function(e){
        var td = e.target.closest ? e.target.closest("td.cell") : null;
        if (!td) return;
        var g = +td.getAttribute("data-g"), s = +td.getAttribute("data-s");
        var dg = 0, ds = 0;
        if (e.key === "ArrowUp") dg = -1;
        else if (e.key === "ArrowDown") dg = 1;
        else if (e.key === "ArrowLeft") ds = -1;
        else if (e.key === "ArrowRight") ds = 1;
        else if (e.key === "Home"){ ds = -10; }
        else if (e.key === "End"){ ds = 10; }
        else return;
        e.preventDefault();
        pick(Math.min(15, Math.max(1, g + dg)),
             Math.min(10, Math.max(1, s + ds)), true);
      });
    }
  }

  /* ---- sortable tables ----
     A 58-row table answers exactly one question: the one it happens to be
     sorted by. Sorting turns one table into seven. The sort key lives in
     data-v rather than being parsed out of the text: "$126,817" and "\u2212021"
     do not sort as strings, and parsing currency symbols is a quiet source of
     wrong answers. */
  var sortables = document.querySelectorAll("table[data-sortable]");
  for (var q=0;q<sortables.length;q++){
    (function(tb){
      var heads = tb.querySelectorAll("thead th[data-sort]");
      var state = { col: -1, dir: 1 };
      function sortBy(n){
        var body = tb.tBodies[0];
        var rows = Array.prototype.slice.call(body.rows);
        /* First click on a money or count column shows the biggest value,
           not the smallest. Sorting "what it buys" ascending put the worst
           place in the country at the top of the showcase table. */
        var th0 = tb.querySelector('thead th[data-sort="' + n + '"]');
        var down = th0 && th0.hasAttribute("data-desc");
        state.dir = (state.col === n) ? -state.dir : (down ? -1 : 1);
        state.col = n;
        rows.sort(function(a, b){
          var x = a.cells[n] && a.cells[n].getAttribute("data-v");
          var y = b.cells[n] && b.cells[n].getAttribute("data-v");
          /* A missing value is neither zero nor infinity. Rows without data go
             last in both directions: sorted ascending by price, an area with no
             price index used to surface at the top and read as the cheapest
             place in the country. */
          var ex = (x === null || x === "" || x === "-");
          var ey = (y === null || y === "" || y === "-");
          if (ex && ey) return 0;
          if (ex) return 1;
          if (ey) return -1;
          var nx = parseFloat(x), ny = parseFloat(y);
          var cmp;
          if (!isNaN(nx) && !isNaN(ny)) cmp = nx - ny;
          else cmp = String(x).localeCompare(String(y));
          return cmp * state.dir;
        });
        for (var i=0;i<rows.length;i++) body.appendChild(rows[i]);
        for (var h=0;h<heads.length;h++){
          var on = +heads[h].getAttribute("data-sort") === n;
          heads[h].setAttribute("aria-sort",
            on ? (state.dir > 0 ? "ascending" : "descending") : "none");
        }
      }
      for (var h=0;h<heads.length;h++){
        (function(th){
          var n = +th.getAttribute("data-sort");
          /* The click target is a real <button> inside the <th>. Putting
             role="button" on the <th> itself removed its columnheader role,
             which left a 58-row table with no column headers at all for a
             screen reader. A native button also brings Enter and Space with
             it, so there is no keydown handler to duplicate them. */
          var btn = th.querySelector("button");
          if (btn) btn.addEventListener("click", function(){
            tb.setAttribute("data-touched", "");
            sortBy(n);
          });
          th.addEventListener("keydown", function(e){
            if (btn) return;
            if (e.key === "Enter" || e.key === " "){ e.preventDefault(); sortBy(n); }
          });
        })(heads[h]);
      }
    })(sortables[q]);
  }

  /* ---- area switcher in the rail ---- */
  var jump = document.querySelector("[data-jump]");
  if (jump) jump.addEventListener("change", function(){
    if (jump.value) location.href = jump.value;
  });
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
                note: str = "", hero: str = "") -> str:
    """Разметка инструмента.

    Без hero инструмент скрыт атрибутом hidden и открывается скриптом: без JS
    на странице не остаётся мёртвых полей, которые молча ничего не делают.

    С hero всё иначе, и это главный экран главной страницы. Готовый ответ уже
    посчитан на сборке и лежит в разметке, поэтому прятать блок нельзя — он и
    есть содержимое. Поля вместо этого отдаются с disabled и включаются
    скриптом: мёртвых контролов по-прежнему нет, а сдвига вёрстки при
    инициализации больше нет тоже.
    """
    off = " disabled" if hero else ""
    grades = "".join(
        f'<option value="{g}"{" selected" if str(g) == grade else ""}>GS-{g}</option>'
        for g in range(1, 16))
    steps = "".join(
        f'<option value="{s}"{" selected" if str(s) == step else ""}>Step {s}</option>'
        for s in range(1, 11))

    zip_row = ("" if not with_zip else
               '<div class="fp-field"><label for="fp-zip">Work ZIP code</label>'
               f'<input id="fp-zip" data-zip type="text" inputmode="numeric" '
               f'maxlength="5" placeholder="e.g. 20001" '
               f'autocomplete="postal-code"{off}></div>')
    zone_row = ("" if not zones else
                '<div class="fp-field fp-wide"><label for="fp-zone">'
                'Locality pay area</label>'
                f'<select id="fp-zone" data-zone{off}>{zones}</select></div>')

    hero_block = f'<div class="fp-hero">{hero}</div>' if hero else ""

    # Дефолт «ступень 5» — середина грейда, и вся сравнительная арифметика
    # сайта считается по ней. Но человек с первым оффером получает из-за неё
    # число, завышенное на пятизначную сумму, и на сайте об этом не сказано
    # ни слова. Со ссылкой на закон, а не «обычно».
    hint = ("" if not hero else
            '<p class="fp-hint">Starting your first federal job? A first '
            'appointment is set at <strong>step 1</strong> of the grade '
            'unless the agency uses the superior qualifications authority '
            '(5 U.S.C. 5333; 5 CFR 531.212). The step above defaults to 5, '
            'the middle of the grade, because that is the cell this site '
            'ranks every area by.</p>')

    nojs = ("" if not hero else
            '<noscript><p class="fp-note">These controls need JavaScript. '
            'Every locality pay area also has its own page with the full '
            'table \u2014 the ranked list further down this page links to all '
            'of them.</p></noscript>')

    return (
        f'<div class="fp-calc{" fp-lead" if hero else ""}" data-calc'
        f'{f" data-fixed=\"{fixed}\"" if fixed else ""}'
        f'{"" if hero else " hidden"}>'
        f'{f"<h2>{heading}</h2>" if heading else ""}'
        f'{hero_block}'
        f'<div class="fp-fields">{zip_row}{zone_row}'
        f'<div class="fp-field"><label for="fp-grade">Grade</label>'
        f'<select id="fp-grade" data-grade{off}>{grades}</select></div>'
        f'<div class="fp-field"><label for="fp-step">Step</label>'
        f'<select id="fp-step" data-step{off}>{steps}</select></div></div>'
        f'{hint}'
        f'{nojs}'
        f'<p class="fp-zipmsg" data-zipmsg role="status"></p>'
        f'<div class="fp-out" data-out aria-live="polite"></div>'
        f'{f"<p class=\"fp-note\">{note}</p>" if note else ""}'
        f'</div>')
