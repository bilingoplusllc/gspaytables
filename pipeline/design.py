"""Оформление FedPay — «приборная панель ведомости».

ПОЧЕМУ ПЕРЕДЕЛАНО ВТОРОЙ РАЗ. Первый вариант был близнецом MileageCurve по
решениям. Второй сменил краску и гарнитуру, но оставил тот же СКЕЛЕТ: крошки,
заголовок, подзаголовок, плашка-оговорка, карточка с числом, экспонаты, секции
прозы — одна колонка сверху вниз. Судьи сформулировали точно: сайты разные,
автор узнаётся. Плюс моноширинная гарнитура владельцу не понравилась.

ЧТО ИЗМЕНИЛОСЬ ТЕПЕРЬ — именно архитектура:

1.  ЗАЛИПАЮЩАЯ ПОЛОСА ОТВЕТА. Зона, грейд, ступень и все производные числа
    (год, две недели, час, переработка, два ранга) видны на любой глубине
    прокрутки. Грейд и ступень переключаются прямо в ней. Раньше ответ был
    карточкой, которая уезжала вверх и больше не возвращалась.
2.  ДВЕ КОЛОНКИ. Постоянный рельс с оглавлением страницы, переключателем зоны и
    местом под рекламу; основная колонка — данные. Раньше была одна колонка, и
    на широком экране половина ширины простаивала.
3.  СЕТКА ФАКТОВ ВМЕСТО ЛЕНТЫ. Четыре карточки — как складывается число, два
    ранга, что оно покупает, что с потолком — стоят рядом на первом экране.
    Раньше эти же четыре вещи были разбросаны по четырём экранам прокрутки.
4.  ТАБЛИЦА КАК ИНТЕРФЕЙС. Клетка выбирается мышью или стрелками, и полоса
    ответа переезжает на неё. Раньше таблица была картинкой, на которую можно
    было только смотреть.
5.  ЗАГОЛОВКИ-ВОПРОСЫ. Разделы называются так, как человек спрашивает, а не так,
    как называется поле в базе. Это одновременно и структура, и попадание в
    поисковые запросы.
6.  ЗАМЕТКИ НА ПОЛЯХ. Оговорки, определения и источники ушли из цветных врезок
    посреди текста в узкую колонку сбоку. Чтение больше ничем не разрывается.
7.  МЕСТА ПОД РЕКЛАМУ предусмотрены в раскладке заранее — в рельсе и между
    разделами, — а не втискиваются потом в готовую страницу.

ГАРНИТУРА. Archivo: гротеск с широким диапазоном насыщенности и настоящими
табличными цифрами, переменный woff2 в 35 КБ, лежит на нашем домене. Не
моноширинный и не Georgia. Системный стек остаётся запасным, и страница
читается, даже если файл не доехал.

ПАЛИТРА. Холодный светло-серый лист, почти чёрная структура, единственный
акцент — охра. Тёмно-зелёный занят MileageCurve, тёмно-синий — конкурентом
gstakehomepay. Зелёный и рыжий остаются только знаками направления «+N / −N»,
и знак читается без цвета.

СОХРАНЕНО ИЗ УРОКОВ: ни одного position:absolute для декора (sticky — функция),
никаких внешних запросов, три состояния тем, табличные цифры, широкие таблицы
прокручиваются внутри контейнера, кодирование не только цветом.

ВНИМАНИЕ: блок ниже — СЫРАЯ строка. В CSS обратный слэш принадлежит CSS, а не
питону: в обычной строке \\00a0 превращается в нулевой байт, и однажды так и
случилось на всех 103 страницах.
"""

CSS = r"""
:root{
  color-scheme:light;
  --page:#f1f2f4;
  --card:#ffffff;
  --ink:#17191d;
  --ink-soft:#3d424b;
  --muted:#5f6672;
  --line:#dcdfe4;
  --line-strong:#b3b9c2;
  --bar:#17191d;
  --bar-ink:#f4f5f7;
  --accent:#8a5a06;
  --accent-soft:#fdf3e0;
  --warn:#9a2f28;
  --warn-soft:#fbeceb;
  --up:#20603f;
  --s1:4px; --s2:8px; --s3:14px; --s4:22px; --s5:34px; --s6:52px;
  --face:"Archivo","Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --page:#15171a; --card:#1d2024; --ink:#e9ebee; --ink-soft:#c2c7cf;
    --muted:#9aa1ac;
    --line:#2c3036; --line-strong:#575e67;
    --bar:#0c0d0f; --bar-ink:#e9ebee;
    --accent:#e0a44a; --accent-soft:#2a2113;
    --warn:#e58a80; --warn-soft:#2c1a18;
    --up:#63c795;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --page:#15171a; --card:#1d2024; --ink:#e9ebee; --ink-soft:#c2c7cf;
  --muted:#9aa1ac;
  --line:#2c3036; --line-strong:#575e67;
  --bar:#0c0d0f; --bar-ink:#e9ebee;
  --accent:#e0a44a; --accent-soft:#2a2113;
  --warn:#e58a80; --warn-soft:#2c1a18;
  --up:#63c795;
}

*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;background:var(--page)}
body{margin:0;background:var(--page);color:var(--ink);
  font:16px/1.6 var(--face);font-variant-numeric:tabular-nums;
  font-feature-settings:"tnum" 1;-webkit-font-smoothing:antialiased}

/* ---------- шапка: узкая полоса, не занимающая первый экран */
header.site{background:var(--card);border-bottom:1px solid var(--line)}
.masthead{max-width:1320px;margin:0 auto;padding:10px var(--s4);
  display:flex;align-items:center;gap:var(--s3);flex-wrap:wrap}
.brand{font:800 19px/1 var(--face);letter-spacing:-.02em;color:var(--ink);
  text-decoration:none}
.tagline{font:500 12px/1.3 var(--face);color:var(--muted);max-width:26ch}
header.site nav{margin-left:auto;display:flex;gap:var(--s1);flex-wrap:wrap;
  font:600 13px/1 var(--face)}
header.site nav a{color:var(--muted);text-decoration:none;padding:7px 9px;
  border-radius:3px}
header.site nav a:hover{color:var(--ink);background:var(--page)}
header.site nav a[aria-current="page"]{color:var(--ink);background:var(--page)}

/* ---------- ПОЛОСА ОТВЕТА: главное структурное отличие.
   Липнет к верху, поэтому ответ никогда не уезжает из виду. */
.answerbar{position:sticky;top:0;z-index:20;background:var(--bar);
  color:var(--bar-ink);border-bottom:1px solid var(--line-strong)}
.ab-in{max-width:1320px;margin:0 auto;padding:10px var(--s4);
  display:flex;align-items:center;gap:var(--s4);flex-wrap:wrap}
.ab-where{font:600 12px/1.35 var(--face);letter-spacing:.04em;
  text-transform:uppercase;opacity:.72;max-width:30ch}
.ab-pick{display:flex;align-items:center;gap:6px;font:600 12px/1 var(--face)}
.ab-pick label{opacity:.75;letter-spacing:.06em;text-transform:uppercase}
.ab-pick select{font:600 14px/1 var(--face);color:var(--bar-ink);
  background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.30);
  border-radius:3px;padding:6px 7px}
.ab-pick select option{color:#17191d;background:#fff}
.ab-main{display:flex;align-items:baseline;gap:8px;margin-left:auto}
.ab-big{font:800 clamp(22px,3.2vw,32px)/1 var(--face);letter-spacing:-.03em}
.ab-unit{font:600 11px/1 var(--face);letter-spacing:.08em;text-transform:uppercase;
  opacity:.7}
.ab-more{display:flex;gap:var(--s4);flex-wrap:wrap}
.ab-more div{display:flex;flex-direction:column;gap:2px}
.ab-more .v{font:700 15px/1 var(--face)}
.ab-more .k{font:600 10px/1 var(--face);letter-spacing:.08em;
  text-transform:uppercase;opacity:.66}
.ab-more .down{color:#f0a59c}
.ab-more .up{color:#8fdcb4}

/* ---------- раскладка: рельс и основная колонка */
.layout{max-width:1320px;margin:0 auto;padding:var(--s4);
  display:grid;grid-template-columns:230px minmax(0,1fr);gap:var(--s5)}
/* Страницы без рельса: одна колонка разумной ширины, а не дыра в сетке. */
.layout.solo{grid-template-columns:minmax(0,1fr);max-width:820px}
.rail{align-self:start;position:sticky;top:96px}
.rail h2{font:700 11px/1 var(--face);letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);margin:0 0 var(--s2);max-width:none}
.rail ol{list-style:none;margin:0 0 var(--s4);padding:0;
  border-left:2px solid var(--line)}
.rail li a{display:block;padding:5px 0 5px var(--s3);color:var(--muted);
  text-decoration:none;font:500 13.5px/1.35 var(--face);
  border-left:2px solid transparent;margin-left:-2px}
.rail li a:hover{color:var(--ink);border-left-color:var(--accent)}
.rail-note{font:500 12.5px/1.5 var(--face);color:var(--muted);
  margin:0 0 var(--s4);max-width:none}
.rail li a[aria-current="page"]{color:var(--ink);font-weight:700;
  border-left-color:var(--accent)}
.rail .switch{margin-bottom:var(--s4)}
.rail .switch label{display:block;font:700 11px/1 var(--face);letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.rail select{width:100%;font:500 13px/1.3 var(--face);color:var(--ink);
  background:var(--card);border:1px solid var(--line-strong);border-radius:3px;
  padding:7px}

/* ---------- места под рекламу: заложены в раскладку заранее */
.ad-slot{border:1px dashed var(--line-strong);border-radius:3px;
  display:flex;align-items:center;justify-content:center;
  font:600 10px/1 var(--face);letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);background:var(--card)}
.ad-rail{min-height:600px;width:100%}
.ad-band{min-height:110px;margin:0 0 var(--s4)}

/* ---------- типографика основной колонки */
h1{font:800 clamp(23px,2.7vw,33px)/1.2 var(--face);letter-spacing:-.025em;
  margin:0 0 var(--s2);max-width:26ch}
.sub{font:400 17px/1.55 var(--face);color:var(--ink-soft);max-width:62ch;
  margin:0 0 var(--s4)}
h2{font:700 clamp(18px,2vw,23px)/1.3 var(--face);letter-spacing:-.015em;
  margin:0 0 var(--s3);max-width:32ch}
h3{font:700 15px/1.35 var(--face);margin:var(--s4) 0 var(--s2)}
p{margin:0 0 var(--s3);max-width:66ch;color:var(--ink-soft)}
a{color:var(--accent);text-underline-offset:2px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.crumbs{list-style:none;display:flex;flex-wrap:wrap;gap:6px;padding:0;
  margin:0 0 var(--s3);font:500 12.5px/1 var(--face);color:var(--muted)}
.crumbs li+li::before{content:"\203A";margin-right:6px;color:var(--line-strong)}
.crumbs a{color:var(--muted)}

/* ---------- раздел-вопрос */
section.q{background:var(--card);border:1px solid var(--line);border-radius:4px;
  padding:var(--s4);margin:0 0 var(--s4)}
section.q>:last-child{margin-bottom:0}
.q-lead{font:600 17px/1.5 var(--face);color:var(--ink);max-width:62ch;
  margin:0 0 var(--s3)}
.q-lead strong{font-weight:800}

/* ---------- сетка фактов на первом экране */
/* Ровно две колонки: при auto-fit четвёртая карточка оставалась одна в
   строке и выглядела остатком, а не частью набора. */
.facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
  gap:var(--s3);margin:0 0 var(--s4)}
@media (max-width:560px){.facts{grid-template-columns:minmax(0,1fr)}}
.fact{background:var(--card);border:1px solid var(--line);border-radius:4px;
  padding:var(--s3) var(--s3) var(--s2)}
.fact h3{font:700 10.5px/1.2 var(--face);letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin:0 0 var(--s2)}
.fact p{font-size:14px;line-height:1.5;margin-bottom:var(--s2)}
.fact .kpi{font:800 26px/1.05 var(--face);letter-spacing:-.02em;
  color:var(--ink);display:block;margin-bottom:4px}
.fact .kpi-sub{font:500 12.5px/1.4 var(--face);color:var(--muted);display:block}

/* ---------- оговорка. Не цветная плашка посреди чтения, а полоса на поле:
   тот же приём, что у заметок, чтобы текст ничем не разрывался. */
.caveat{border-left:3px solid var(--warn);background:var(--warn-soft);
  padding:var(--s3) var(--s3) 2px;margin:0 0 var(--s3);border-radius:0 3px 3px 0}
.caveat p{color:var(--ink-soft);font-size:15px;line-height:1.55;max-width:64ch}
.caveat strong:first-child{color:var(--warn);font-weight:800}

/* ---------- карточка вердикта. Нужна там, где ответ не одно число в полосе,
   а сопоставление двух зон: на страницах сравнения. */
.answer{background:var(--card);border:1px solid var(--line);border-radius:4px;
  margin:0 0 var(--s4);overflow:hidden}
.answer .what{display:block;background:var(--bar);color:var(--bar-ink);
  padding:8px var(--s4);font:700 10.5px/1.2 var(--face);
  letter-spacing:.11em;text-transform:uppercase}
.answer .body{padding:var(--s4)}
.answer .big{display:block;font:800 clamp(30px,5vw,46px)/1 var(--face);
  letter-spacing:-.03em;margin:0 0 var(--s3);color:var(--ink)}
.answer p:last-child{margin-bottom:0}

/* ---------- опорная клетка: отмечена сервером, видна и без скрипта.
   Со скриптом её сменяет выбранная, и метка снимается. */
table.pay td.ref{outline:2px solid var(--accent);outline-offset:-2px;
  font-weight:700}
table.pay td.ref::after{content:"\25C0";margin-left:6px;font-size:9px;
  color:var(--accent)}
table.pay td.sel::after{color:inherit}

/* ---------- бухгалтерский разбор */
.ledger{margin:0 0 var(--s3);border-top:1px solid var(--line)}
.ledger div{display:flex;align-items:baseline;gap:var(--s2);padding:6px 0;
  border-bottom:1px solid var(--line)}
.ledger dt{flex:1;font:500 13.5px/1.45 var(--face);color:var(--muted)}
.ledger dd{margin:0;font:700 14.5px/1.45 var(--face);white-space:nowrap}
.ledger div.total dt{color:var(--ink);font-weight:700}
.ledger div.total{border-bottom:2px solid var(--line-strong)}
.ledger dd.down{color:var(--warn)}
.ledger dd.up{color:var(--up)}

/* ---------- заметки на полях: оговорки больше не рвут текст */
.withnotes{display:grid;grid-template-columns:minmax(0,1fr) 250px;
  gap:var(--s5);align-items:start}
.sidenote{font:500 13px/1.5 var(--face);color:var(--muted);
  border-left:2px solid var(--accent);padding-left:var(--s3)}
.sidenote b{display:block;font:700 10.5px/1.2 var(--face);letter-spacing:.1em;
  text-transform:uppercase;color:var(--accent);margin-bottom:6px}
.sidenote p{font-size:13px;line-height:1.5;color:var(--muted);max-width:none}
.sidenote p:last-child{margin-bottom:0}

/* ---------- таблицы */
.scroll{overflow-x:auto;overscroll-behavior-x:contain;
  -webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:4px;
  background:
    linear-gradient(to right,var(--card),transparent) 0 0/26px 100% no-repeat local,
    linear-gradient(to left,var(--card),transparent) 100% 0/26px 100% no-repeat local,
    linear-gradient(to right,rgba(0,0,0,.16),transparent) 0 0/12px 100% no-repeat scroll,
    linear-gradient(to left,rgba(0,0,0,.16),transparent) 100% 0/12px 100% no-repeat scroll}
.scroll:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
table{border-collapse:separate;border-spacing:0;width:100%;
  font:14px/1.4 var(--face)}
th,td{padding:7px 10px;text-align:left;white-space:nowrap;
  border-bottom:1px solid var(--line)}
tbody tr:last-child th,tbody tr:last-child td{border-bottom:0}
thead th{position:sticky;top:0;z-index:2;background:var(--bar);
  color:var(--bar-ink);font:700 11px/1.3 var(--face);letter-spacing:.07em;
  text-transform:uppercase;border-bottom:0}
/* Заголовок как кнопка сортировки: стрелка появляется только у активного
   столбца, чтобы шапка не превращалась в частокол значков. */
thead th[data-sort]{cursor:pointer;user-select:none}
thead th[data-sort]:hover{background:var(--ink)}
thead th[aria-sort="ascending"]::after{content:"\2191";margin-left:5px}
thead th[aria-sort="descending"]::after{content:"\2193";margin-left:5px}
th.num,td.num{text-align:right}
th.rank,td.rank{text-align:right;width:1%;color:var(--muted);font-weight:700}
th[scope="row"]{font-weight:700;white-space:normal;min-width:13ch;
  background:var(--card)}
tbody tr:nth-child(even) td{background:var(--page)}
tbody tr:nth-child(even) th[scope="row"]{background:var(--page)}

table.pay th[scope="row"]{position:sticky;left:0;z-index:1;white-space:nowrap;
  min-width:7ch;border-right:2px solid var(--line-strong)}
table.pay thead th:first-child{position:sticky;left:0;z-index:3;
  border-right:2px solid var(--line-strong)}
table.pay th.gut,table.pay td.gut{border-left:2px solid var(--line-strong)}

/* клетка как элемент управления: выбирается мышью и с клавиатуры */
table.pay td.cell{cursor:pointer}
table.pay td.cell:hover{background:var(--accent-soft)}
table.pay td.sel,table.pay td.sel:hover{background:var(--bar);
  color:var(--bar-ink);font-weight:700}
table.pay td.sel::after{content:"\25C0";margin-left:6px;font-size:9px}

td.capped{background-color:var(--warn-soft);
  background-image:repeating-linear-gradient(45deg,
    rgba(154,47,40,.20) 0 2px, transparent 2px 6px);font-weight:700}
td.capped::before{content:"\25B2";float:left;font-size:10px;line-height:1.9;
  color:var(--warn)}
tbody tr.you th,tbody tr.you td{background:var(--accent-soft);font-weight:700}
td.up{color:var(--up);font-weight:700}
td.down{color:var(--warn);font-weight:700}
td.flat{color:var(--muted)}
.tlegend{font:500 12px/1.5 var(--face);color:var(--muted);margin:var(--s2) 0 0;
  display:flex;gap:var(--s4);flex-wrap:wrap;max-width:none}

/* ---------- полосы сравнения */
.bars{margin:0;padding:0;list-style:none}
.bars li{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,3fr) max-content;
  gap:var(--s3);align-items:center;padding:6px 0;border-bottom:1px solid var(--line)}
.bars li:last-child{border-bottom:0}
.bars .nm{font:500 13px/1.35 var(--face);color:var(--muted);overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.bar{display:block;height:14px;background:var(--page);border-radius:2px}
.bar span{display:block;height:100%;background:var(--line-strong);border-radius:2px}
.bars li.hi .nm{color:var(--ink);font-weight:700}
.bars li.hi .bar span{background:var(--accent)}
.bars .v{font:700 13px/1 var(--face);text-align:right}

/* ---------- подписи и источники */
figure.ex{margin:0;padding:0}
.ex-kicker{font:700 10.5px/1.2 var(--face);letter-spacing:.1em;
  text-transform:uppercase;color:var(--accent);margin-bottom:6px}
.ex-title{font:700 17px/1.3 var(--face);margin:0 0 var(--s2)}
.ex-note{font-size:14px;line-height:1.55;color:var(--muted);max-width:66ch;
  margin-bottom:var(--s3)}
figcaption{font:500 12px/1.55 var(--face);color:var(--muted);
  margin-top:var(--s3);padding-top:var(--s2);border-top:1px solid var(--line);
  max-width:none}
figcaption strong{color:var(--ink-soft)}

/* ---------- плитки и списки */
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:var(--s3);margin:var(--s3) 0}
.tile{border:1px solid var(--line);border-radius:4px;padding:var(--s3);
  background:var(--page)}
.tile .k{font:700 10.5px/1 var(--face);letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);display:block;margin-bottom:6px}
.tile .v{font:800 21px/1.1 var(--face);letter-spacing:-.02em}
.tile .d{font:500 13px/1.5 var(--face);color:var(--muted);margin-top:5px}
.chips,.chips-plain,.counties{display:flex;flex-wrap:wrap;gap:6px;margin:var(--s3) 0;
  padding:0;list-style:none}
.chips a,.chips-plain li,.counties li{display:inline-block;padding:5px 10px;
  border:1px solid var(--line);border-radius:3px;font:600 13px/1.3 var(--face);
  color:var(--ink);text-decoration:none;background:var(--page)}
.counties li{font-weight:500;color:var(--muted)}
.chips a:hover{border-color:var(--accent);color:var(--accent)}

/* ---------- инструмент расчёта */
.fp-calc{border:1px solid var(--line);border-radius:4px;background:var(--card);
  margin:0 0 var(--s4)}
.fp-calc h2{margin:0;padding:var(--s3) var(--s4);border-bottom:1px solid var(--line);
  font-size:15px;letter-spacing:0}
.fp-fields{display:flex;flex-wrap:wrap;gap:var(--s3);padding:var(--s3) var(--s4)}
.fp-field{flex:1 1 150px}
.fp-field.fp-wide{flex:2 1 280px}
.fp-field label{display:block;font:700 10.5px/1.2 var(--face);color:var(--muted);
  text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px}
.fp-field select,.fp-field input{width:100%;font:500 15px/1.3 var(--face);
  color:var(--ink);background:var(--page);border:1px solid var(--line-strong);
  border-radius:3px;padding:8px}
.fp-zipmsg:not(:empty){margin:0;padding:10px var(--s4);font-size:13.5px;
  background:var(--accent-soft);border-top:1px solid var(--line);color:var(--ink-soft)}
.fp-out{padding:var(--s4)}
.fp-out p.fp-what{font:700 10.5px/1.2 var(--face);color:var(--muted);
  text-transform:uppercase;letter-spacing:.1em;margin:0 0 var(--s2)}
.fp-out p.fp-big{font:800 clamp(28px,5vw,42px)/1 var(--face);letter-spacing:-.03em;
  margin:0 0 var(--s3);color:var(--ink)}
.fp-lines{display:grid;grid-template-columns:1fr max-content;margin:0 0 var(--s4);
  border-top:1px solid var(--line)}
.fp-lines dt{font:500 13.5px/1.45 var(--face);color:var(--muted)}
.fp-lines dd{margin:0;font:700 14.5px/1.45 var(--face);text-align:right}
.fp-lines dt,.fp-lines dd{padding:6px 0;border-bottom:1px solid var(--line)}
.fp-out p{margin-bottom:var(--s3)}
.fp-out p.fp-src{margin-bottom:0;font-size:13.5px}
.fp-note{padding:0 var(--s4) var(--s4);color:var(--muted);font-size:13.5px}

/* ---------- подвал */
footer{background:var(--card);border-top:1px solid var(--line);margin-top:var(--s6)}
footer .in{max-width:1320px;margin:0 auto;padding:var(--s5) var(--s4)}
footer p{font-size:13.5px;line-height:1.6;color:var(--muted);max-width:78ch}
footer a{color:var(--muted)}
.disclaimer{color:var(--ink-soft);font-weight:600}

@media (max-width:1080px){
  .layout{grid-template-columns:minmax(0,1fr);gap:var(--s4)}
  /* Рельс уходит ПОД содержимое. В одну колонку он вставал первым, и на
     телефоне человек видел оглавление и рекламный блок раньше заголовка
     страницы — на странице грейда это пятнадцать ссылок до первой строки
     текста. Навигация не должна стоять между читателем и ответом. */
  main{order:1}
  .rail{order:2;position:static;display:grid;
    grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:var(--s3)}
  .rail ol{margin-bottom:0}
  .ad-rail{min-height:110px}
  .withnotes{grid-template-columns:minmax(0,1fr);gap:var(--s3)}
}
@media (max-width:640px){
  body{font-size:15.5px}
  .masthead,.ab-in,.layout,footer .in{padding-left:var(--s3);padding-right:var(--s3)}
  /* На телефоне липкая полоса в две строки съедала пятую часть экрана.
     Вторичные числа стоят в карточке сразу под ней, поэтому в полосе
     остаётся только то, ради чего она липкая: где, что и сколько. */
  .ab-more{display:none}
  .ab-in{gap:var(--s3);padding:8px var(--s3)}
  .ab-where{font-size:11px;max-width:none;flex:1 1 100%}
  .ab-main{margin-left:auto}
  .rail{grid-template-columns:minmax(0,1fr)}
  section.q{padding:var(--s3)}
  table{font-size:13px}
  th,td{padding:6px 8px}
  .bars li{grid-template-columns:minmax(0,1fr) max-content;gap:4px var(--s2)}
  .bars .nm{white-space:normal;grid-column:1}
  .bars .v{grid-column:2}
  .bars .bar{grid-column:1 / -1;margin-top:2px}
}
@media print{
  header.site nav,.rail,.ad-slot,.ab-pick,.fp-calc{display:none}
  .answerbar{position:static}
  html,body{background:#fff;color:#000}
  .layout{display:block;max-width:none;padding:0}
  section.q,.fact,.scroll{border:1px solid #000;break-inside:avoid}
  thead th,.answerbar{background:#fff !important;color:#000 !important;
    border-bottom:2px solid #000}
  td.capped,tr.you td,td.sel{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .scroll{overflow:visible;background:none}
  table{font-size:9pt}
}
"""

MARK = ""
