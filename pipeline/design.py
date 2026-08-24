"""Оформление FedPay. Один файл — весь визуальный язык сайта.

Решения взяты из разбора MileageCurve, где «выглядит непрофессионально» звучало
трижды подряд, пока не выяснилось, что у страницы был только шрифтовой масштаб
и ничего больше. Что реально изменило приговор:

* --radius: 2px. Скруглённые карточки — самый громкий признак «скачанной темы».
* Раздельные шрифты: засечки для слов, гротеск для ЧИСЕЛ. У Georgia минускульные
  цифры, и число внутри засечного блока читается как сбой отрисовки.
* Настоящая шапка: знак, подзаголовок и линейка 3px вместо жирного слова и
  четырёх серых ссылок.
* Таблицы и графики — пронумерованные экспонаты с надзаголовком, названием,
  описанием шкалы и подписью источника, а не «мебель» посреди текста.
* Одна линейка на раздел вместо трёх сложенных волосяных.

Отдельно: никакого position:absolute для декора. На прошлом сайте это ломалось
дважды. Всё — в потоке.
"""

CSS = """
:root{
  --ink:#12100e; --muted:#5c574f; --line:#ddd8cf; --line-strong:#b8b1a4;
  --bg:#fbfaf7; --card:#fff; --accent:#0f5d4e; --accent-soft:#e7f0ed;
  --warn-bg:#fdf6e6; --warn-line:#c9a227; --track:#f0ede7;
  --radius:2px;
  --s1:4px; --s2:8px; --s3:14px; --s4:22px; --s5:36px; --s6:56px;
  --serif:Georgia,'Iowan Old Style','Times New Roman',serif;
  --sans:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ink:#eceae6; --muted:#a49e94; --line:#33302b; --line-strong:#57524a;
    --bg:#141310; --card:#1c1a17; --accent:#4fbfa4; --accent-soft:#17302a;
    --warn-bg:#2a2416; --warn-line:#8a7325; --track:#232019;
  }
}
:root[data-theme="dark"]{
  --ink:#eceae6; --muted:#a49e94; --line:#33302b; --line-strong:#57524a;
  --bg:#141310; --card:#1c1a17; --accent:#4fbfa4; --accent-soft:#17302a;
  --warn-bg:#2a2416; --warn-line:#8a7325; --track:#232019;
}

*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:17px/1.65 var(--serif);text-rendering:optimizeLegibility}
.wrap{max-width:960px;margin:0 auto;padding:0 var(--s4)}

/* числа — всегда гротеск, всегда табличные */
.num,td.num,th.num,.big,.pct{font-family:var(--sans);
  font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}

/* ---------- шапка ---------- */
header.site{border-bottom:3px solid var(--ink);padding:var(--s4) 0 var(--s2);
  margin-bottom:var(--s5)}
.masthead{display:flex;align-items:baseline;gap:var(--s3);flex-wrap:wrap}
.brand{font:700 25px/1 var(--serif);color:var(--ink);text-decoration:none;
  letter-spacing:-.01em;display:inline-flex;align-items:center;gap:8px}
.brand svg{flex:none}
.tagline{font:400 12.5px/1.3 var(--sans);color:var(--muted);
  text-transform:uppercase;letter-spacing:.09em}
header.site nav{margin-left:auto;display:flex;gap:var(--s3);
  font:500 13.5px/1 var(--sans)}
header.site nav a{color:var(--muted);text-decoration:none;padding-bottom:3px;
  border-bottom:2px solid transparent}
header.site nav a:hover{color:var(--ink);border-bottom-color:var(--accent)}
header.site nav a[aria-current="page"]{color:var(--ink);border-bottom-color:var(--accent)}

/* ---------- заголовки и текст ---------- */
h1{font:700 clamp(28px,4.4vw,42px)/1.14 var(--serif);letter-spacing:-.02em;
  margin:0 0 var(--s3)}
h2{font:700 24px/1.25 var(--serif);margin:var(--s6) 0 var(--s3);
  padding-top:var(--s3);border-top:1px solid var(--line-strong)}
h3{font:600 18px/1.3 var(--serif);margin:var(--s4) 0 var(--s2)}
p{margin:0 0 var(--s3);max-width:66ch}
.sub{font:400 19px/1.5 var(--serif);color:var(--muted);margin-bottom:var(--s4);
  max-width:60ch}
a{color:var(--accent)}
.crumbs{list-style:none;display:flex;gap:var(--s2);padding:0;margin:0 0 var(--s3);
  font:500 12.5px/1 var(--sans);color:var(--muted);flex-wrap:wrap}
.crumbs li+li::before{content:"›";margin-right:var(--s2);color:var(--line-strong)}
.crumbs a{color:var(--muted);text-decoration:none}
.crumbs a:hover{color:var(--accent)}

/* ---------- ответный блок ---------- */
.answer{background:var(--card);border:1px solid var(--line-strong);
  border-left:4px solid var(--accent);border-radius:var(--radius);
  padding:var(--s4);margin:0 0 var(--s5)}
.answer .big{font:700 clamp(32px,5.2vw,46px)/1 var(--sans);letter-spacing:-.02em;
  display:block;margin-bottom:var(--s2)}
.answer .what{font:500 13px/1.3 var(--sans);color:var(--muted);
  text-transform:uppercase;letter-spacing:.08em;margin-bottom:var(--s3)}
.answer p:last-child{margin-bottom:0}

/* оговорка — ВСЕГДА над числом, не в подвале */
.caveat{background:var(--warn-bg);border-left:3px solid var(--warn-line);
  padding:var(--s3);margin:0 0 var(--s3);font-size:15.5px}
.caveat strong{font-weight:700}
.caveat p:last-child{margin-bottom:0}

/* ---------- экспонаты ---------- */
figure.ex{margin:var(--s5) 0;padding:0}
.ex-kicker{font:600 11.5px/1 var(--sans);color:var(--accent);
  text-transform:uppercase;letter-spacing:.12em;margin-bottom:var(--s2)}
.ex-title{font:700 19px/1.3 var(--serif);margin-bottom:var(--s1)}
.ex-note{font:400 14px/1.5 var(--sans);color:var(--muted);margin-bottom:var(--s3);
  max-width:70ch}
figcaption{font:400 12.5px/1.5 var(--sans);color:var(--muted);
  margin-top:var(--s2);padding-top:var(--s2);border-top:1px solid var(--line)}

/* ---------- таблицы ---------- */
/* Тень-подсказка у краёв прокрутки: приём Lea Verou на чистых фонах —
   никакого position:absolute, который на прошлом сайте ломался дважды.
   Слои с background-attachment:local уезжают вместе с содержимым, слои со
   scroll стоят на месте и закрывают тень, когда прокручивать больше некуда. */
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;
  background:
    linear-gradient(to right,var(--bg),transparent) 0 0/28px 100% no-repeat local,
    linear-gradient(to left,var(--bg),transparent) 100% 0/28px 100% no-repeat local,
    linear-gradient(to right,rgba(0,0,0,.13),transparent) 0 0/14px 100% no-repeat scroll,
    linear-gradient(to left,rgba(0,0,0,.13),transparent) 100% 0/14px 100% no-repeat scroll;}
table{border-collapse:collapse;width:100%;font-size:14.5px}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);
  white-space:nowrap}
/* Числа не переносим никогда, а длинное название зоны — можно: иначе одна
   строка «Atlanta--Athens-Clarke County--Sandy Springs, GA-AL» распирает
   таблицу шире колонки и выталкивает последний столбец за край. */
th[scope="row"]{white-space:normal;min-width:14ch}
/* Выравнивание по СМЫСЛУ колонки, а не по её позиции. Числа справа —
   их сравнивают по разрядам; слова слева. Раньше правило было привязано к
   первой колонке, и в таблицах с рангом имена зоны уезжали вправо. */
th,td{text-align:left}
th.num,td.num,th.rank,td.rank{text-align:right}
th[scope="row"]{font-weight:600;font-size:14px}
thead th{font:600 12px/1.2 var(--sans);color:var(--muted);
  text-transform:uppercase;letter-spacing:.06em;
  border-bottom:2px solid var(--line-strong);background:var(--bg)}
tbody tr:hover td{background:var(--track)}
tbody tr:hover td:first-child{background:var(--track)}
td.capped{background:var(--warn-bg);position:relative}
td.capped::after{content:"▲";font-size:9px;color:var(--warn-line);
  margin-left:5px;vertical-align:top}
.rank{color:var(--muted);font:600 12px/1 var(--sans);width:1%}
tr.you td{background:var(--accent-soft);font-weight:700}
/* Сдвиг в рейтинге: знак несёт смысл сам по себе, поэтому «+20» и «−17»
   читаются и без цвета — на печати и при дальтонизме. */
td.up{color:var(--accent);font-weight:600}
td.down{color:#a3402f;font-weight:600}
:root[data-theme="dark"] td.down,
:root:not([data-theme="light"]) td.down{color:#e08a76}
td.flat{color:var(--muted)}

/* ---------- полосы сравнения ---------- */
.bars{margin:0;padding:0;list-style:none}
.bars li{display:grid;grid-template-columns:1.6fr 3fr auto;gap:var(--s3);
  align-items:center;padding:5px 0;border-bottom:1px solid var(--line)}
.bars .nm{font:500 14px/1.3 var(--sans);overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.bar{background:var(--track);height:15px;border-radius:0}
.bar span{display:block;height:100%;background:var(--accent)}
.bars .v{font:600 13.5px/1 var(--sans);font-variant-numeric:tabular-nums}
.bars li.hi .bar span{background:var(--warn-line)}

/* ---------- прочее ---------- */
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:var(--s3);margin:var(--s4) 0}
.tile{background:var(--card);border:1px solid var(--line);
  border-radius:var(--radius);padding:var(--s3)}
.tile .k{font:600 11.5px/1 var(--sans);color:var(--muted);
  text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}
.tile .v{font:700 22px/1.1 var(--sans);font-variant-numeric:tabular-nums}
.tile .d{font:400 13px/1.45 var(--sans);color:var(--muted);margin-top:5px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:var(--s3) 0;padding:0;
  list-style:none}
.chips a{display:inline-block;padding:4px 10px;border:1px solid var(--line);
  border-radius:var(--radius);font:500 13px/1.4 var(--sans);
  color:var(--ink);text-decoration:none}
.chips a:hover{border-color:var(--accent);background:var(--track)}
.counties{list-style:none;margin:0;padding:0;display:grid;\n  grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:2px 14px;\n  font:400 14px/1.7 var(--sans)}\n.counties li{color:var(--muted);border-bottom:1px solid var(--line);\n  padding:3px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\nfooter{margin-top:var(--s6);padding:var(--s4) 0 var(--s6);
  border-top:3px solid var(--ink);font:400 13.5px/1.6 var(--sans);
  color:var(--muted)}
footer p{max-width:74ch}
footer a{color:var(--muted)}
.disclaimer{font-weight:600;color:var(--ink)}

@media (max-width:640px){
  body{font-size:16px}
  .wrap{padding:0 var(--s3)}
  header.site nav{width:100%;margin-left:0;margin-top:var(--s2)}
  .bars li{grid-template-columns:1.3fr 2fr auto;gap:var(--s2)}
  .bars .nm{font-size:13px}
}
@media print{
  header.site nav,.chips{display:none}
  body{background:#fff;color:#000}
}
"""

MARK = ('<svg width="16" height="18" viewBox="0 0 16 18" aria-hidden="true" '
        'focusable="false"><rect x="0" y="10" width="3.4" height="8" '
        'fill="currentColor"/><rect x="6.3" y="5" width="3.4" height="13" '
        'fill="currentColor" opacity=".66"/><rect x="12.6" y="0" width="3.4" '
        'height="18" fill="currentColor" opacity=".4"/></svg>')
