"""Оформление FedPay — «ведомость».

Прежняя версия была собрана из решений, вынесенных с разбора MileageCurve, и
получилась его близнецом: та же пара Georgia + гротеск, тот же тёмно-зелёный
акцент, та же шапка с линейкой, те же «экспонаты». Два сайта одного владельца,
которые невозможно различить, — это и слабый продукт, и лишний след.

ИДЕЯ. Страница притворяется не журнальной статьёй, а служебным документом:
лист ведомости, лежащий на столе. Фон — «стол», колонка контента — «лист» с
боковыми линейками полей. Мебель документа (марка, шапки таблиц, заголовки
экспонатов) набрана вывороткой, как отпечатанная. Ведущая гарнитура —
системная моноширинная: каждое число стоит в своей разрядной клетке, столбцы
совпадают сами собой, и читатель видит не «текст про деньги», а сам платёжный
документ. Длинная проза — пропорциональным гротеском: форма напечатана на
машинке, служебная записка к ней набрана.

ЧЕМ ОТЛИЧАЕТСЯ ОТ MileageCurve, по пунктам:

1.  Гарнитура. Там Georgia для слов и гротеск для чисел. Здесь пара
    перевёрнута: моноширинная для всего каркаса, пропорциональная — только
    для прозы.
2.  Акцент. Там тёмно-зелёный #0f6e5e. Здесь штемпельная киноварь #a63016 —
    цвет красной краски на бланке. Синий не используется вовсе: его занял
    конкурент gstakehomepay.com.
3.  Оговорка. Там кремовая плашка с полосой слева. Здесь рамка бланка, а
    фраза «Read this before the number» превращена в штамп выворотки.
4.  Заголовки разделов. Там border-top и отступ. Здесь моноширинный капслок,
    и остаток строки добирается ДВОЙНОЙ линейкой — идиома печатной формы.
5.  Крошки. Там знак «›». Здесь файловый путь через «/».
6.  Экспонаты. Там надзаголовок висит в воздухе. Здесь экспонат — лист формы:
    рамка, выворотная шапка, тело, подпись источника в отдельной полосе.
7.  Полосы сравнения. Там серая дорожка и сплошная заливка. Здесь дорожки нет:
    пустая бумага с пунктирной базовой линией, заливка набрана знакоместами,
    как печатает гистограмму строчный принтер.
8.  Ширина. Там колонка 880px. Здесь лист 1100px: таблице 15x10 нужна ширина,
    и на 1280px она помещается целиком.
9.  Скруглений нет вовсе — у бланка их не бывает.
10. Значка-логотипа нет: марка — это выворотная нашлёпка с именем.

ПОЧЕМУ ЭТО УМЕСТНО ИМЕННО ЗДЕСЬ. Читатель пришёл сверить число, от которого
зависит переезд. Ему нужна не редакционная интонация, а ощущение
первоисточника — тот же вид, что у самой таблицы OPM. Моноширинная сетка
делает 150 клеток честно сопоставимыми: разряды стоят друг под другом без
единого трюка. Киноварь занята единственным смыслом — ограничение и внимание
(потолок, оговорка, своя строка), и потолок кодируется ещё и штриховкой 45
градусов, поэтому читается в чёрно-белой печати и при дальтонизме.

СОХРАНЕНО ИЗ УРОКОВ: ни одного position:absolute для декора (sticky-колонка
грейдов — функция, а не украшение), никаких внешних запросов, три состояния
тем, табличные цифры везде, широкие таблицы прокручиваются внутри контейнера.

ПРИВИТО ИЗ ДРУГИХ НАПРАВЛЕНИЙ: бухгалтерский блок цифр вместо абзаца прозы
под крупным числом (направление 4) и разрыв между 5-й и 6-й ступенью в таблице
окладов (направление 1) — глазу нужен якорь на середине из десяти колонок.
"""

CSS = """
:root{
  color-scheme:light;
  --desk:#e9e1d0;        /* стол, на котором лежит лист */
  --sheet:#fbf8f1;       /* сам лист */
  --band:#f2ecdf;        /* полоса ведомости (чётная строка) */
  --ink:#16130f;
  --muted:#615748;
  --rule:#d7cfbc;
  --rule-strong:#9e9179;
  --stamp:#a63016;       /* штемпельная киноварь */
  --stamp-soft:#f7e5de;
  --hatch:rgba(166,48,22,.30);
  --up:#1f5d3c;          /* подъём в рейтинге */
  --s1:4px; --s2:8px; --s3:14px; --s4:22px; --s5:34px; --s6:54px;
  --mono:ui-monospace,"Cascadia Mono",Consolas,"SF Mono",Menlo,"DejaVu Sans Mono",monospace;
  --prose:ui-sans-serif,"Segoe UI",system-ui,-apple-system,"Helvetica Neue",sans-serif;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --desk:#0d0c0a; --sheet:#1a1814; --band:#211e18;
    --ink:#ece5d6; --muted:#a29886;
    --rule:#403a30; --rule-strong:#796d58;
    --stamp:#f0705a; --stamp-soft:#2d1a15;
    --hatch:rgba(240,112,90,.34);
    --up:#63c795;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --desk:#0d0c0a; --sheet:#1a1814; --band:#211e18;
  --ink:#ece5d6; --muted:#a29886;
  --rule:#403a30; --rule-strong:#796d58;
  --stamp:#f0705a; --stamp-soft:#2d1a15;
  --hatch:rgba(240,112,90,.34);
  --up:#63c795;
}

*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;background:var(--desk)}
body{margin:0;background:var(--desk);color:var(--ink);
  font:15px/1.6 var(--mono);
  font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}

/* ЛИСТ. Никакого absolute: обычный блок в потоке с боковыми линейками полей. */
.wrap{max-width:1100px;margin:0 auto;min-height:100vh;background:var(--sheet);
  border-left:1px solid var(--rule);border-right:1px solid var(--rule);
  padding:0 var(--s4)}

/* ---------- шапка: нашлёпка-марка, поле подзаголовка, бланковая навигация */
header.site{padding:var(--s4) 0 var(--s3);margin-bottom:var(--s5);
  border-bottom:4px double var(--ink)}
.masthead{display:flex;align-items:center;gap:var(--s3);flex-wrap:wrap}
.brand{font:700 20px/1 var(--mono);letter-spacing:.02em;text-decoration:none;
  background:var(--ink);color:var(--sheet);padding:7px 11px 8px}
.tagline{font:400 12px/1.35 var(--mono);color:var(--muted);
  letter-spacing:.02em;max-width:34ch}
header.site nav{margin-left:auto;display:flex;flex-wrap:wrap;gap:var(--s1);
  font:500 12.5px/1 var(--mono)}
header.site nav a{color:var(--muted);text-decoration:none;padding:6px 8px;
  border:1px solid transparent}
header.site nav a::before{content:"[";margin-right:5px;color:var(--rule-strong)}
header.site nav a::after{content:"]";margin-left:5px;color:var(--rule-strong)}
header.site nav a:hover{background:var(--ink);color:var(--sheet)}
header.site nav a:hover::before,header.site nav a:hover::after{color:var(--sheet)}
header.site nav a[aria-current="page"]{color:var(--ink);
  border-color:var(--rule-strong);background:var(--band)}

/* ---------- общая типографика */
h1{font:700 clamp(21px,3.1vw,31px)/1.25 var(--mono);letter-spacing:-.02em;
  margin:0 0 var(--s3);max-width:34ch}
h2{display:flex;align-items:center;gap:var(--s3);
  font:700 14px/1.2 var(--mono);text-transform:uppercase;letter-spacing:.14em;
  margin:var(--s6) 0 var(--s4)}
h2::after{content:"";flex:1;border-top:3px double var(--rule-strong)}
h3{font:700 15px/1.3 var(--mono);letter-spacing:.01em;margin:var(--s4) 0 var(--s2)}
p{margin:0 0 var(--s3);max-width:70ch}
main p{font-family:var(--prose);font-size:16px;line-height:1.62}
a{color:var(--stamp);text-decoration:underline;text-underline-offset:2px}
:focus-visible{outline:2px solid var(--stamp);outline-offset:2px}

.crumbs{list-style:none;display:flex;gap:var(--s2);padding:0;margin:0 0 var(--s3);
  font:500 12px/1 var(--mono);color:var(--muted);flex-wrap:wrap;letter-spacing:.04em}
.crumbs li+li::before{content:"/";margin-right:var(--s2);color:var(--rule-strong)}
.crumbs a{color:var(--muted);text-decoration:underline;
  text-underline-offset:2px;text-decoration-color:var(--rule-strong)}
.crumbs a:hover{color:var(--stamp);text-decoration:underline}
.sub{max-width:64ch;color:var(--muted);margin-bottom:var(--s4)}
main p.sub{font-size:17px;line-height:1.55}

/* ---------- оговорка: рамка бланка и фраза-штамп */
.caveat{border:1px solid var(--stamp);background:var(--stamp-soft);
  padding:var(--s3) var(--s3) var(--s2);margin:0 0 var(--s4)}
.caveat p{margin-bottom:var(--s2)}
.caveat strong:first-child{display:inline-block;background:var(--stamp);
  color:var(--sheet);font:700 11.5px/1 var(--mono);letter-spacing:.13em;
  text-transform:uppercase;padding:5px 8px 6px;margin-right:8px;vertical-align:2px}

/* ---------- карточка ответа: корешок платёжки */
.answer{border:1px solid var(--rule-strong);margin:0 0 var(--s5);
  background:var(--sheet)}
.answer .what{display:block;background:var(--stamp);color:var(--sheet);
  padding:7px 12px 8px;font:700 11.5px/1.2 var(--mono);
  text-transform:uppercase;letter-spacing:.13em}
.answer .body{padding:var(--s4) var(--s3) var(--s3)}
.answer .big{display:block;font:700 clamp(34px,6.6vw,58px)/1 var(--mono);
  letter-spacing:-.03em;padding-bottom:var(--s3);margin-bottom:var(--s3);
  border-bottom:2px dashed var(--rule-strong)}
.answer p:last-child{margin-bottom:0}

/* ---------- бухгалтерский блок: разбор числа строками, а не абзацем.
   Привито из направления 4: читатель сверяет расчётный лист, ему нужны
   позиции друг под другом, а не пересказ. */
.ledger{margin:0 0 var(--s3);border-top:1px solid var(--rule)}
.ledger div{display:flex;align-items:baseline;gap:var(--s2);
  padding:5px 0;border-bottom:1px solid var(--rule)}
.ledger dt{flex:1;font:400 13px/1.5 var(--mono);color:var(--muted);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ledger dd{margin:0;font:700 14px/1.5 var(--mono);text-align:right;
  white-space:nowrap}
.ledger div.total dt{color:var(--ink);font-weight:700}
.ledger div.total{border-bottom:3px double var(--rule-strong)}
.ledger dd.down{color:var(--stamp)}
.ledger dd.up{color:var(--up)}

/* ---------- экспонат = лист формы */
figure.ex{margin:var(--s5) 0;padding:0;border:1px solid var(--rule-strong);
  background:var(--sheet)}
figure.ex>.ex-kicker{display:block;background:var(--ink);color:var(--sheet);
  padding:6px 12px 7px;font:700 11.5px/1.3 var(--mono);
  text-transform:uppercase;letter-spacing:.13em}
figure.ex>.ex-title{padding:var(--s3) var(--s3) 0;
  font:700 16px/1.3 var(--mono);margin:0 0 var(--s2)}
figure.ex>.ex-note{padding:0 var(--s3);color:var(--muted);max-width:72ch;
  font-size:15px;margin-bottom:var(--s3)}
figure.ex>.scroll,figure.ex>.bars,figure.ex>.counties{margin:var(--s3)}
figure.ex>figcaption{background:var(--band);border-top:1px solid var(--rule);
  padding:10px 12px;font:400 12px/1.55 var(--mono);color:var(--muted)}
figcaption strong{color:var(--ink)}

/* ---------- полосы: печать знакоместами, без серой дорожки */
.bars{margin:0;padding:0;list-style:none}
.bars li{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,3fr) max-content;
  gap:var(--s3);align-items:center;padding:6px 0;border-bottom:1px solid var(--rule)}
.bars li:last-child{border-bottom:0}
.bars .nm{font:400 12.5px/1.35 var(--mono);color:var(--muted);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar{display:block;height:15px;border-bottom:1px dotted var(--rule-strong)}
.bar span{display:block;height:12px;color:var(--ink);
  background-image:repeating-linear-gradient(90deg,
    currentColor 0 .46em, transparent .46em .66em)}
.bars li.hi .nm{color:var(--ink);font-weight:700}
.bars li.hi .nm::before{content:"\\25B6\\00a0";color:var(--stamp)}
.bars li.hi .bar span{color:var(--stamp)}
.bars li.hi .bar{border-bottom-color:var(--stamp)}
.bars .v{font:700 13px/1 var(--mono);text-align:right}

/* ---------- таблицы */
/* Подсказка о прокрутке. Слои с background-attachment:local уезжают вместе
   с содержимым, слои со scroll стоят на месте и закрывают тень, когда
   прокручивать больше некуда. Никакого position:absolute. */
.scroll{overflow-x:auto;overscroll-behavior-x:contain;
  -webkit-overflow-scrolling:touch;border:1px solid var(--rule-strong);
  background:
    linear-gradient(to right,var(--sheet),transparent) 0 0/24px 100% no-repeat local,
    linear-gradient(to left,var(--sheet),transparent) 100% 0/24px 100% no-repeat local,
    linear-gradient(to right,rgba(0,0,0,.20),transparent) 0 0/12px 100% no-repeat scroll,
    linear-gradient(to left,rgba(0,0,0,.20),transparent) 100% 0/12px 100% no-repeat scroll}
.scroll:focus-visible{outline:2px solid var(--stamp);outline-offset:2px}
table{border-collapse:separate;border-spacing:0;width:100%;
  font:13.5px/1.45 var(--mono);font-variant-numeric:tabular-nums}
th,td{padding:6px 9px;text-align:left;white-space:nowrap;
  border-bottom:1px solid var(--rule)}
td+td,th+th,th+td,td+th{border-left:1px solid var(--rule)}
tbody tr:last-child th,tbody tr:last-child td{border-bottom:0}
thead th{background:var(--ink);color:var(--sheet);
  font:700 11px/1.3 var(--mono);text-transform:uppercase;letter-spacing:.08em;
  border-bottom:0;border-left-color:var(--rule-strong);
  position:sticky;top:0;z-index:2}
th.num,td.num{text-align:right}
th.rank,td.rank{text-align:right;width:1%;color:var(--muted);font-weight:700}
th[scope="row"]{font-weight:700;white-space:normal;min-width:14ch}

/* ведомостная разлиновка. Фон задан явно на каждой ячейке — иначе
   sticky-колонка просвечивает. */
tbody tr:nth-child(odd) th,tbody tr:nth-child(odd) td{background:var(--sheet)}
tbody tr:nth-child(even) th,tbody tr:nth-child(even) td{background:var(--band)}

/* таблица окладов: колонка грейдов не уезжает при прокрутке */
table.pay th[scope="row"]{position:sticky;left:0;z-index:1;white-space:nowrap;
  min-width:8ch;border-right:2px solid var(--rule-strong)}
table.pay thead th:first-child{position:sticky;left:0;z-index:3;
  border-right:2px solid var(--rule-strong)}
/* разрыв посередине десяти ступеней: якорь для глаза при поиске клетки */
table.pay th.gut,table.pay td.gut{border-left:2px solid var(--rule-strong)}

/* потолок: штриховка 45 градусов и знак — читается без цвета и в ч/б печати */
tbody tr th.capped,tbody tr td.capped{
  background-color:var(--stamp-soft);
  background-image:repeating-linear-gradient(45deg,
    var(--hatch) 0 2px, transparent 2px 6px);
  font-weight:700}
tbody tr td.capped::before{content:"\\25B2";float:left;font-size:11px;
  line-height:1.78;color:var(--stamp)}

/* своя строка в рейтинге соседей: цвет и знак */
tbody tr.you th,tbody tr.you td{background:var(--stamp-soft);font-weight:700}
tbody tr.you th[scope="row"]::after{content:"\\00a0\\25C0";color:var(--stamp)}
/* Только background-color: сокращённое свойство сбрасывало background-image
   и вместе с ним штриховку потолка — двойное кодирование пропадало от
   движения мыши. */
tbody tr:hover th,tbody tr:hover td{background-color:var(--band)}
tbody tr.you:hover th,tbody tr.you:hover td{background-color:var(--stamp-soft)}
tbody tr:hover th.capped,tbody tr:hover td.capped{background-color:var(--stamp-soft)}

/* Опорная клетка: страница объявляет «GS-12 ступень 5 = столько-то», и в
   таблице из 150 клеток эта самая клетка обязана быть найдена глазом сразу. */
table.pay td.ref{outline:2px solid var(--stamp);outline-offset:-2px;
  font-weight:700}
table.pay td.ref::after{content:"\00a0\25C0";color:var(--stamp);font-size:10px}

/* сдвиг в рейтинге: знак самодостаточен, цвет лишь помогает */
td.up{color:var(--up);font-weight:700}
td.down{color:var(--stamp);font-weight:700}
td.flat{color:var(--muted)}

/* ---------- плитки потолка: та же штриховка, что в таблице */
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:var(--s3);margin:var(--s4) 0}
.tile{border:1px solid var(--rule-strong);background:var(--sheet);
  border-top:6px solid transparent;
  background-image:repeating-linear-gradient(45deg,
    var(--hatch) 0 2px, transparent 2px 6px);
  background-size:100% 6px;background-repeat:no-repeat;background-origin:border-box;
  padding:var(--s3)}
.tile .k{display:inline-block;background:var(--ink);color:var(--sheet);
  font:700 11px/1 var(--mono);letter-spacing:.12em;padding:5px 7px 6px;
  margin-bottom:10px}
.tile .v{font:700 21px/1.1 var(--mono);letter-spacing:-.01em}
.tile .d{font-family:var(--prose);font-size:14px;line-height:1.5;
  color:var(--muted);margin-top:6px}

/* ---------- ссылки-плашки на грейды */
.chips{display:flex;flex-wrap:wrap;gap:0;margin:var(--s3) 0;padding:0;
  list-style:none}
.chips a{display:inline-block;padding:7px 11px;border:1px solid var(--rule);
  margin:0 -1px -1px 0;font:700 13px/1.3 var(--mono);color:var(--ink);
  text-decoration:none;background:var(--sheet)}
.chips a:hover{background:var(--ink);color:var(--sheet)}

/* Города зоны: те же клетки бланка, но крупнее — это не справочная сноска,
   а ответ на вопрос, которым человек начинает поиск. */
.chips-plain{list-style:none;margin:var(--s3) 0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:0}
.chips-plain li{font:700 13px/1.4 var(--mono);color:var(--ink);
  border:1px solid var(--rule);margin:0 -1px -1px 0;padding:8px 10px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chips-plain li:nth-child(even){background:var(--band)}

/* ---------- округа: матрица клеток бланка, а не список */
.counties{list-style:none;margin:0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0}
.counties li{font:400 12.5px/1.4 var(--mono);color:var(--muted);
  border:1px solid var(--rule);margin:0 -1px -1px 0;padding:7px 9px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.counties li:nth-child(even){background:var(--band)}

/* ---------- инструмент расчёта */
.fp-calc{border:1px solid var(--rule-strong);background:var(--sheet);
  margin:var(--s5) 0}
.fp-calc h2{margin:0;background:var(--stamp);color:var(--sheet);
  padding:7px 12px 8px;font-size:11.5px;letter-spacing:.13em}
.fp-calc h2::after{display:none}
.fp-fields{display:flex;flex-wrap:wrap;gap:0;border-bottom:1px solid var(--rule)}
.fp-field{flex:1 1 150px;padding:var(--s3);border-right:1px solid var(--rule);
  border-bottom:1px solid var(--rule);margin:0 -1px -1px 0}
.fp-field.fp-wide{flex:2 1 280px}
.fp-field label{display:block;font:700 10.5px/1.2 var(--mono);color:var(--muted);
  text-transform:uppercase;letter-spacing:.11em;margin-bottom:6px}
.fp-field select,.fp-field input{width:100%;font:400 15px/1.3 var(--mono);
  color:var(--ink);background:var(--band);border:1px solid var(--rule-strong);
  border-radius:0;padding:7px 8px}
.fp-field select:focus-visible,.fp-field input:focus-visible{
  outline:2px solid var(--stamp);outline-offset:1px}
.fp-zipmsg:not(:empty){margin:0;padding:9px var(--s3);font-size:13px;
  background:var(--band);border-bottom:1px solid var(--rule);
  font-family:var(--mono);color:var(--muted)}
.fp-out{padding:var(--s4) var(--s3) var(--s3)}
.fp-out p.fp-what{font:700 11.5px/1.2 var(--mono);color:var(--muted);
  text-transform:uppercase;letter-spacing:.11em;margin:0 0 var(--s2)}
.fp-out p.fp-big{font:700 clamp(30px,5.6vw,48px)/1 var(--mono);
  letter-spacing:-.03em;margin:0 0 var(--s3)}
.fp-lines{margin:0 0 var(--s4);border-top:1px solid var(--rule)}
.fp-lines dt{font:400 13px/1.5 var(--mono);color:var(--muted)}
.fp-lines dd{margin:0;font:700 14px/1.5 var(--mono);text-align:right}
.fp-lines{display:grid;grid-template-columns:1fr max-content}
.fp-lines dt,.fp-lines dd{padding:5px 0;border-bottom:1px solid var(--rule)}
.fp-out p{margin-bottom:var(--s3)}
.fp-out p.fp-src{margin-bottom:0;font-family:var(--mono);font-size:13px}
.fp-note{padding:0 var(--s3) var(--s3);color:var(--muted);font-size:14px}

/* ---------- подвал */
footer{margin-top:var(--s6);padding:var(--s4) 0 var(--s6);
  border-top:4px double var(--ink);color:var(--muted)}
footer p{font-family:var(--prose);font-size:14px;line-height:1.6;max-width:76ch}
footer a{color:var(--muted)}
footer p.links{font-family:var(--mono);font-size:12.5px;letter-spacing:.02em}
.disclaimer{color:var(--ink);border:1px solid var(--rule-strong);
  background:var(--band);padding:var(--s3);margin-bottom:var(--s3)}

@media (max-width:900px){
  .wrap{padding:0 var(--s3)}
  header.site nav{margin-left:0;width:100%;margin-top:var(--s2)}
}
@media (max-width:640px){
  body{font-size:14.5px}
  main p{font-size:15.5px}
  figure.ex>.scroll,figure.ex>.bars,figure.ex>.counties{margin:var(--s2)}
  .bars li{grid-template-columns:minmax(0,1fr) max-content;gap:var(--s1) var(--s2)}
  .bars .nm{white-space:normal;grid-column:1}
  .bars .v{grid-column:2}
  .bars .bar{grid-column:1 / -1;margin-top:2px}
  .answer .body{padding:var(--s3) var(--s2) var(--s2)}
  table{font-size:12.5px}
  th,td{padding:5px 7px}
}
@media print{
  header.site nav,.fp-calc{display:none}
  html,body,.wrap{background:#fff;color:#000;border:0}
  .wrap{max-width:none;padding:0}
  a{color:#000}
  /* Выворотка на бумаге не работает: фоны по умолчанию не печатаются, и
     белый текст исчезал белым по белому — включая шапку таблицы, то есть
     единственный указатель номера ступени. */
  .brand,thead th,figure.ex>.ex-kicker,.answer .what,.tile .k{
    background:#fff !important;color:#000 !important;
    border:1px solid #000;box-shadow:none}
  thead th{border-width:0 0 2px 0}
  /* Заливка, которая НЕСЁТ СМЫСЛ, печатается принудительно. */
  td.capped,th.capped,tr.you td,tr.you th{
    -webkit-print-color-adjust:exact;print-color-adjust:exact}
  .scroll{overflow:visible;border:1px solid #000;background:none}
  table{font-size:9pt}
  th,td{padding:2px 4px}
  figure.ex,.answer,.caveat,.tile{break-inside:avoid}
}
"""

# Значка нет: марка — выворотная нашлёпка с именем. Отдельный SVG-символ был
# ещё одним общим приёмом с MileageCurve.
MARK = ""
