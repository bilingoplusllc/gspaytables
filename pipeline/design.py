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

  /* ---------- земли: три хроматические поверхности вместо трёх серых.
     Сегодняшний сайт различал блоки рамкой в 1 px при контрасте карточки
     к фону 1.12:1 — глаз видел линию, а не объект. Здесь разделяет
     смена земли, и лист к столу даёт 1.40:1 без единой рамки. */
  --ground:#e2d8bf;      /* стол, на котором лежит документ */
  --sheet:#fdfaf3;       /* лист документа */
  --tint:#f1e7cc;        /* тонированный регистр: зебра, полоса штемпелей */
  --tint-2:#e6dab9;      /* полоса подписей и рекламы */

  /* ---------- чернила: три слоя, а не один */
  --ink:#191610;         /* текст и заголовки */
  --ink-2:#544c3b;       /* служебный слой: метки, источники, сноски */
  --ink-3:#7c7360;       /* третий слой: заглушки, отключённое */

  /* ---------- глубокая полоса. В тёмной теме ОСТАЁТСЯ тёмной:
     шапка, меню и подвал должны читаться полосами при любой теме. */
  --deep:#132440;
  --deep-ink:#f7f2e3;
  --deep-ink-2:#c2cde0;
  --deep-hair:rgba(247,242,227,.30);

  /* ---------- плашка. В тёмной теме ИНВЕРТИРУЕТСЯ в пергамент: ордер
     ответа, шапка ведомости и штемпель обязаны остаться самыми громкими
     поверхностями страницы, а не утонуть в фоне. В светлой теме численно
     совпадает с --deep, и это совпадение намеренное, а не дубль. */
  --band:#132440;
  --band-ink:#f7f2e3;
  --band-ink-2:#c2cde0;
  --band-hair:rgba(247,242,227,.30);

  /* ---------- акцент-печать. Работает ЗАЛИВКОЙ, а не цветом букв:
     прежняя охра существовала только как цвет глифов на 67 прогонах и
     хроматических поверхностей не давала ни одной. */
  --seal:#7b1e2b;
  --seal-fill:#7b1e2b;
  --seal-on:#fdf6ef;

  /* ---------- направление: цвет числа и заливка полосы отдельно */
  --gain:#1c5138;
  --loss:#7b1e2b;
  --gain-fill:#2f6a4a;
  --loss-fill:#8d2733;
  --loss-soft:#f2d6cf;

  /* ---------- линейки трёх весов вместо одной в 1 px на всю страницу */
  --hair:rgba(25,22,16,.17);
  --rule:rgba(25,22,16,.44);
  --heavy:#132440;

  /* ---------- контролы */
  --field:#fffdf8;
  --field-line:#8a8067;
  --focus:#7b1e2b;
  /* Кольцо фокуса на тёмной плашке: --focus на --band даёт 1.52:1, то
     есть на меню и на кнопках заголовков столбцов фокуса не видно. */
  --focus-on-band:#f2d6cf;

  /* ---------- подсказка о боковой прокрутке. У облика её нет вовсе, а
     таблица ставок занимает 731 px в контейнере 315 px. */
  --shade:rgba(25,22,16,.20);

  /* ---------- единственная глубина: оттиск листа на столе */
  --sheet-shadow:0 1px 0 rgba(25,22,16,.20),0 18px 34px -22px rgba(25,22,16,.60);

  /* ---------- шкала кеглей: восемь ступеней, у каждой своя работа.
     Было шестнадцать кеглей, одиннадцать из них стиснуты в полосу
     10.5-17 px с шагом в полпикселя — сложность без иерархии. */
  --s-stamp:13px;                     /* прописная метка в 1-3 слова */
  --s-fine:15px;                      /* служебный слой */
  --s-text:17px;                      /* проза и ведомость */
  --s-lead:21px;                      /* лид раздела */
  --s-head:27px;                      /* заголовок раздела */
  --s-kpi:34px;                       /* число во врезке */
  --s-title:clamp(29px,3.5vw,40px);   /* заголовок выпуска */
  --s-figure:clamp(42px,8.4vw,64px);  /* число ответа */

  /* ---------- ритм привязан к строке прозы: 17 x 1.62 = 27.5.
     Прежде на всю страницу было два зазора, и промежуток между разделами
     был МЕНЬШЕ одной строки текста. */
  --sp1:7px; --sp2:14px; --sp3:27px; --sp4:54px; --sp5:81px; --sp6:108px;

  /* Georgia в запасном стеке стоять не может: это гарнитура соседнего
     сайта фермы, и провал загрузки превратил бы FedPay в его двойника. */
  --serif:"Source Serif 4","Iowan Old Style","Palatino Linotype",
    "Times New Roman",serif;
  --sans:"Libre Franklin","Helvetica Neue",Arial,sans-serif;

  /* ---------- алиасы прежних имён. Существуют ровно затем, чтобы шаг
     смены краски не тронул ни одного селектора: скелет старый, краска
     новая, гейт «класс без правила» зелёный. Уходят по мере того, как
     каждый блок переписывается на новый словарь. */
  --page:var(--ground);
  --card:var(--sheet);
  --ink-soft:var(--ink-2);
  --muted:var(--ink-2);
  --line:var(--hair);
  --line-strong:var(--rule);
  --control-line:var(--field-line);
  --bar:var(--band);
  --bar-ink:var(--band-ink);
  --accent:var(--seal);
  --accent-soft:var(--tint);
  --warn:var(--loss);
  --warn-soft:var(--loss-soft);
  --up:var(--gain);
  --s1:7px; --s2:14px; --s3:27px; --s4:27px; --s5:54px; --s6:81px;
  --face:var(--sans);
}

@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --ground:#100e0b;
    --sheet:#302c25;
    --tint:#423c30;
    --tint-2:#4e4739;
    --ink:#f2ead7;
    --ink-2:#c8bda2;
    --ink-3:#9e947f;
    --deep:#1e2a41;
    --deep-ink:#f0e8d6;
    --deep-ink-2:#b9c3d6;
    --deep-hair:rgba(240,232,214,.24);
    --band:#e7dcc0;
    --band-ink:#171207;
    --band-ink-2:#5b5136;
    --band-hair:rgba(23,18,7,.28);
    --seal:#e8a49b;
    --seal-fill:#8d2733;
    --seal-on:#fdf6ef;
    --gain:#93cfa8;
    --loss:#e8a49b;
    --gain-fill:#3f8a62;
    --loss-fill:#b0454a;
    --loss-soft:#5a3a34;
    --hair:rgba(242,234,215,.20);
    --rule:rgba(242,234,215,.46);
    --heavy:#e7dcc0;
    --field:#26231d;
    --field-line:#9a8f76;
    --focus:#e8a49b;
    --focus-on-band:#5a3a34;
    --shade:rgba(242,234,215,.24);
    --sheet-shadow:0 0 0 1px rgba(242,234,215,.10),0 20px 40px -26px #000;
  }
}
/* Блок-близнец обязателен. Медиазапрос даёт системную тему и оставляет
   возможность вручную вернуться в светлую; этот блок даёт ручное
   переключение выше по приоритету. Слить их в один — сломать одно из
   двух. */
:root[data-theme="dark"]{
  color-scheme:dark;
  --ground:#100e0b;
  --sheet:#302c25;
  --tint:#423c30;
  --tint-2:#4e4739;
  --ink:#f2ead7;
  --ink-2:#c8bda2;
  --ink-3:#9e947f;
  --deep:#1e2a41;
  --deep-ink:#f0e8d6;
  --deep-ink-2:#b9c3d6;
  --deep-hair:rgba(240,232,214,.24);
  --band:#e7dcc0;
  --band-ink:#171207;
  --band-ink-2:#5b5136;
  --band-hair:rgba(23,18,7,.28);
  --seal:#e8a49b;
  --seal-fill:#8d2733;
  --seal-on:#fdf6ef;
  --gain:#93cfa8;
  --loss:#e8a49b;
  --gain-fill:#3f8a62;
  --loss-fill:#b0454a;
  --loss-soft:#5a3a34;
  --hair:rgba(242,234,215,.20);
  --rule:rgba(242,234,215,.46);
  --heavy:#e7dcc0;
  --field:#26231d;
  --field-line:#9a8f76;
  --focus:#e8a49b;
  --focus-on-band:#5a3a34;
  --shade:rgba(242,234,215,.24);
  --sheet-shadow:0 0 0 1px rgba(242,234,215,.10),0 20px 40px -26px #000;
}

*{box-sizing:border-box}

/* Переход по якорю обязан учитывать липкую полосу: без этого заголовок
   раздела встаёт ровно под неё, и ссылка ведёт мимо цели. */
:root{--stick:64px}
[id]{scroll-margin-top:var(--stick)}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}

/* Ссылка «к содержимому»: видна только при фокусе с клавиатуры. Никакого
   position:absolute — она просто схлопнута в точку, пока не понадобится. */
.skip{display:block;width:0;height:0;overflow:hidden;
  white-space:nowrap;clip-path:inset(50%)}
.skip:focus-visible{display:inline-block;width:auto;height:auto;overflow:visible;clip-path:none;
  margin:var(--s2);padding:var(--s2) var(--s3);background:var(--card);
  color:var(--ink);box-shadow:inset 0 0 0 2px var(--seal-fill);
  text-decoration:none;font-weight:700}
html{-webkit-text-size-adjust:100%;background:var(--page)}
body{margin:0;background:var(--ground);color:var(--ink);
  font:400 var(--s-text)/1.62 var(--serif);font-variant-numeric:tabular-nums;
  font-feature-settings:"tnum" 1;-webkit-font-smoothing:antialiased}

/* ---------- шапка: узкая полоса, не занимающая первый экран */

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
/* Страницы без рельса: одна колонка разумной ширины, а не дыра в сетке. */
.layout.solo{grid-template-columns:minmax(0,1fr);max-width:820px}
/* Широкая одноколоночная: главная. Рельса нет — он дублировал верхнее меню
   и отбирал 230 px слева, — но и 820 px колонки мало таблице на семь
   колонок и 58 строк. */
.layout.wide{grid-template-columns:minmax(0,1fr);max-width:1180px}
.layout.wide .sub{max-width:60ch}
.rail-note{font:500 12.5px/1.5 var(--face);color:var(--muted);
  margin:0 0 var(--s4);max-width:none}

/* ---------- места под рекламу: заложены в раскладку заранее */
/* Сеть не подключена. Пустые пунктирные рамки с надписью Advertisement —
   это не «место под рекламу», это признак недоделанного сайта на странице,
   которая продаёт себя точностью. Показывать их будем вместе с реальными
   блоками, зарезервировав высоту под конкретный формат. */
.ad-slot{display:none}
.ad-slot.on{display:flex;border:1px dashed var(--line-strong);border-radius:3px;
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
/* Ссылка наследует цвет своего окружения и опознаётся подчёркиванием, а не
   краской. Прежде она была жёстко цвета акцента — и в подвале на тёмной
   полосе давала 1.52:1. В печатной форме ссылка и не должна быть цветной:
   цветом там помечают величины, а не переходы. */
a{color:inherit;text-underline-offset:.18em;text-decoration-thickness:.06em}
a:hover{color:var(--seal)}
.plate a:hover,footer a:hover,.mast a:hover,.menu a:hover{color:var(--deep-ink)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

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
.fact .fact-k{margin:0;}
.fact .fact-k{font:700 10.5px/1.2 var(--face);letter-spacing:.1em;
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
.sidenote b{display:block;font:700 10.5px/1.2 var(--face);letter-spacing:.1em;
  text-transform:uppercase;color:var(--accent);margin-bottom:6px}
.sidenote p:last-child{margin-bottom:0}

/* ---------- таблицы */
/* overflow-x:auto делает overflow-y тоже auto, поэтому sticky в шапке
   цеплялся за контейнер, который по вертикали не прокручивается, и не липнул
   НИ НА ОДНОЙ странице. Ограниченная высота даёт настоящую прокрутку. */
.scroll{overflow:auto;max-height:min(78vh,880px);overscroll-behavior-x:contain;
  -webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:4px;
  background:
    linear-gradient(to right,var(--card),transparent) 0 0/26px 100% no-repeat local,
    linear-gradient(to left,var(--card),transparent) 100% 0/26px 100% no-repeat local,
    linear-gradient(to right,var(--shade),transparent) 0 0/12px 100% no-repeat scroll,
    linear-gradient(to left,var(--shade),transparent) 100% 0/12px 100% no-repeat scroll}
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
/* Приглушённый цвет колонки рангов относится к ТЕЛУ таблицы. В шапке она
   лежит на тёмной плашке, и служебные чернила давали там 1.83:1 — ровно тот
   дефект, что нашли в макете, только здесь его создавала специфичность:
   .rank (0,1,1) перебивал thead th (0,0,2). */
tbody th.rank,tbody td.rank{color:var(--ink-2)}
th.rank,td.rank{text-align:right;width:1%;font-weight:700}
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

/* ---------- карточка-герой: ответ выше полей, поля читаются как «уточнить»
   Замер до правки: на 375x812 первое число стояло на y=927 — человек не видел
   ни одного доллара без прокрутки, а инструмент разворачивался скриптом и
   сдвигал всё ниже на 748 px. Теперь ответ отрисован на сборке и стоит первым,
   а поля приходят следом уже видимыми. */
/* Заголовок карточки занимал 68 px ровно между h1 и ответом и повторял h1.
   Как надстрочная метка он весит втрое меньше и структуру заголовков не
   ломает. */
/* До инициализации поля отдаются выключенными: без скрипта они честно
   ничего не делают, а вёрстка при включении не прыгает. */

/* Ссылки грейдов с суммой внутри: «GS-12 $76,463» вместо «GS-12». */
.chips-pay{display:grid;gap:6px;margin:var(--s3) 0;
  grid-template-columns:repeat(auto-fill,minmax(132px,1fr))}
.chips-pay a{display:flex;justify-content:space-between;align-items:baseline;
  gap:8px;padding:8px 10px;border:1px solid var(--line);border-radius:3px;
  background:var(--card);text-decoration:none;color:var(--ink)}
.chips-pay a:hover{border-color:var(--accent)}
.chips-pay b{font:800 13px/1 var(--face)}
.chips-pay span{font:500 13px/1 var(--face);color:var(--muted)}

/* Заголовок-сортировщик: кликает вложенная кнопка, а <th> остаётся
   заголовком столбца. role="button" на самом <th> стирал columnheader, и
   таблица из 58 строк оставалась для скринридера без заголовков вообще. */
thead th[data-sort] button{all:unset;display:block;width:100%;cursor:pointer;
  font:inherit;color:inherit;letter-spacing:inherit;text-transform:inherit}
thead th.num button{text-align:right}
thead th[data-sort] button:focus-visible{outline:2px solid var(--accent);
  outline-offset:2px}

/* ---------- подвал */
.disclaimer{color:var(--ink-soft);font-weight:600}

@media (max-width:1080px){
  /* Рельс уходит ПОД содержимое. В одну колонку он вставал первым, и на
     телефоне человек видел оглавление и рекламный блок раньше заголовка
     страницы — на странице грейда это пятнадцать ссылок до первой строки
     текста. Навигация не должна стоять между читателем и ответом. */
  main{order:1}
  /* Четыре поля в столбик — 291 px, из них в видимую область iOS Safari
     (635 px, а не 812 «экрана устройства») попадало одно. */
  .ad-rail{min-height:110px}
}
@media (max-width:640px){
  body{font-size:15.5px}
  /* На телефоне липкая полоса в две строки съедала пятую часть экрана.
     Вторичные числа стоят в карточке сразу под ней, поэтому в полосе
     остаётся только то, ради чего она липкая: где, что и сколько. */
  :root{--stick:52px}
  .ab-more{display:none}
  .ab-in{gap:var(--s3);padding:8px var(--s3)}
  .ab-where{font-size:11px;max-width:none;flex:1 1 100%}
  .ab-main{margin-left:auto}
  section.q{padding:var(--s3)}
  table{font-size:13px}
  th,td{padding:6px 8px}
  .bars li{grid-template-columns:minmax(0,1fr) max-content;gap:4px var(--s2)}
  .bars .nm{white-space:normal;grid-column:1}
  .bars .v{grid-column:2}
  .bars .bar{grid-column:1 / -1;margin-top:2px}
}
@media print{
  .answerbar{position:static}
  html,body{background:#fff;color:#000}
  section.q,.fact,.scroll{border:1px solid #000;break-inside:avoid}
  thead th,.answerbar{background:#fff !important;color:#000 !important;
    border-bottom:2px solid #000}
  td.capped,tr.you td,td.sel{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .scroll{overflow:visible;background:none}
  table{font-size:9pt}
}
/* ---------- табличные цифры: восстановление после сокращений font:
   На body объявлено font-variant-numeric:tabular-nums, но по CSS Fonts 4
   сокращение `font:` сбрасывает его в исходное значение — а таких сокращений
   в этом файле больше полусотни, и среди них КАЖДЫЙ элемент с числом. Сайт
   про деньги набирал суммы пропорциональными цифрами, объявив табличные, и
   колонка долларов не выравнивалась по разрядам.
   Селекторы повторены один в один: та же специфичность, более поздний
   порядок. Иначе `.fp-hero p.fp-big` (0,1,2) побеждает общий `.fp-big`. */
table,th,td,
.ab-big,
.fact .fact-k,.fact .kpi,.fact .kpi-sub,
.ledger dt,.ledger dd,
.fp-out p.fp-big,.fp-lines dt,.fp-lines dd,
.fp-hero p.fp-big,.fp-hero p.fp-ranks,
.tlegend,.chips-pay b,.chips-pay span{
  font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}

/* ============================================================ каркас выпуска
   Шапка перестаёт быть строкой ссылок и становится ШАПКОЙ ВЫПУСКА: знак
   издателя, название, номер и дата издания. Меню уезжает в собственную
   полосу. Между ними — полоса юридической границы: в теме, где сайт можно
   принять за государственный, оговорка обязана стоять на первом экране и
   быть проведена приёмом оформления, а не мелким шрифтом в подвале. */
.mast{background:var(--deep);color:var(--deep-ink)}
.mast-in{max-width:1180px;margin:0 auto;
  padding:14px clamp(18px,3.4vw,40px) 12px;
  display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.seal{width:50px;height:50px;flex:none;display:block}
.s-ring{fill:none;stroke:currentColor}
.s-w2{stroke-width:2.4}
.s-w1{stroke-width:1}
.s-t{font-family:var(--sans);font-size:9.5px;font-weight:600;
  letter-spacing:.13em;fill:currentColor}
.s-mono{font-family:var(--sans);font-size:var(--s-fine);font-weight:700;
  letter-spacing:.04em;fill:currentColor}
.s-step{fill:currentColor}
.mast-name{display:flex;flex-direction:column;margin-right:auto;min-width:0}
.brand{font-family:var(--sans);font-size:var(--s-lead);font-weight:700;
  letter-spacing:-.005em;text-transform:uppercase;text-decoration:none;
  color:var(--deep-ink);line-height:1.1}
.tagline{font-size:var(--s-fine);color:var(--deep-ink-2);line-height:1.4;
  margin-top:2px;font-family:var(--serif)}
.edition{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.11em;text-transform:uppercase;color:var(--deep-ink-2);
  text-align:right;line-height:1.5}

.menu{background:var(--deep);border-top:1px solid var(--deep-hair)}
.menu-in{max-width:1180px;margin:0 auto;padding:0 clamp(18px,3.4vw,40px);
  display:flex;flex-wrap:wrap}
.menu a{font-family:var(--sans);font-size:var(--s-stamp);font-weight:500;
  letter-spacing:.08em;text-transform:uppercase;color:var(--deep-ink-2);
  text-decoration:none;padding:10px 15px 9px;
  border-bottom:3px solid transparent}
.menu a:first-child{padding-left:0}
.menu a:hover{color:var(--deep-ink)}
.menu a[aria-current]{color:var(--deep-ink);border-bottom-color:var(--seal-fill)}
/* Кольцо фокуса на тёмной полосе: --focus на --deep даёт 1.52:1. */
.menu a:focus-visible,.mast a:focus-visible,footer a:focus-visible{
  outline-color:var(--focus-on-band)}

.notice{background:var(--tint-2);border-top:3px solid var(--seal-fill);
  border-bottom:1px solid var(--hair)}
.notice-in{max-width:1180px;margin:0 auto;
  padding:7px clamp(18px,3.4vw,40px);
  font-family:var(--sans);font-size:var(--s-fine);line-height:1.45;
  color:var(--ink-2)}
.notice-in b{color:var(--ink);font-weight:600}
.nt-long{display:inline}
.nt-short{display:none}

/* ---------- лист документа лежит на столе. Единственная глубина облика:
   не «карточка с рамкой», а оттиск. */
.wrap{max-width:1220px;margin:0 auto;
  padding:clamp(10px,1.5vw,18px) clamp(0px,2.2vw,20px) clamp(28px,4vw,54px)}
.sheet{background:var(--sheet);box-shadow:var(--sheet-shadow)}
.col{max-width:1060px;margin:0 auto;
  padding-left:clamp(18px,3.4vw,40px);padding-right:clamp(18px,3.4vw,40px)}
.measure{max-width:34em}

/* Содержание выпуска строкой. Прежде это был левый рельс: 230 px ширины на
   153 страницах под дубликат верхнего меню. */
.contents{border-bottom:1px solid var(--hair);
  padding:9px clamp(18px,3.4vw,40px);
  max-width:1060px;margin:0 auto}
.contents h2{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.11em;text-transform:uppercase;color:var(--ink-2);
  display:inline;margin:0}
.contents h2::after{content:":";margin-right:10px}
.contents ol{display:inline;list-style:none;margin:0;padding:0}
.contents li{display:inline}
.contents li+li::before{content:"";display:inline-block;width:1px;height:.8em;
  margin:0 9px -.05em;background:var(--rule);vertical-align:baseline}
.contents a{font-family:var(--sans);font-size:var(--s-fine);
  color:var(--ink-2);text-decoration:none}
.contents a:hover{color:var(--seal);text-decoration:underline}
.contents .ad-slot,.contents .rail-note{display:none}
/* Переключатель области живёт в той же строке содержания: в документе это
   «перейти к другому выпуску», и место ему рядом с оглавлением. */
.contents .switch{display:inline-flex;align-items:baseline;gap:8px;
  margin-left:14px;padding-left:14px;border-left:1px solid var(--rule)}
.contents .switch label{font-family:var(--sans);font-size:var(--s-stamp);
  font-weight:600;letter-spacing:.11em;text-transform:uppercase;
  color:var(--ink-2)}
.contents .switch select{font-family:var(--sans);font-size:var(--s-fine);
  color:var(--ink);background:var(--field);
  border:1px solid var(--field-line);border-radius:0;padding:3px 6px;
  max-width:min(46vw,320px)}

/* ---------- подвал */
footer{background:var(--deep);color:var(--deep-ink);margin-top:0}
.foot-in{max-width:1180px;margin:0 auto;
  padding:var(--sp4) clamp(18px,3.4vw,40px);
  display:grid;gap:var(--sp3) clamp(26px,4vw,64px);
  grid-template-columns:minmax(0,1fr)}
.foot-seal{width:110px;height:110px;color:var(--deep-ink-2)}
.foot-disc{font-size:var(--s-lead);line-height:1.4;max-width:28em;
  margin:0 0 var(--sp2);color:var(--deep-ink);font-family:var(--serif)}
.foot-in p{color:var(--deep-ink-2);font-family:var(--sans);
  font-size:var(--s-fine);line-height:1.55;max-width:44em}
.foot-links{display:flex;flex-wrap:wrap;gap:6px 18px;margin:var(--sp2) 0}
.foot-links a{font-family:var(--sans);font-size:var(--s-stamp);
  letter-spacing:.09em;text-transform:uppercase;text-decoration:none;
  color:var(--deep-ink)}
.foot-links a:hover{text-decoration:underline}
.foot-rule{border-top:1px solid var(--deep-hair);margin:var(--sp2) 0;
  height:0;padding:0}

/* ---------- крошки остаются списком: гейт крошек считает <li> и сверяет с
   разметкой BreadcrumbList. Разделитель рисуется чертой, а не глифом:
   U+203A не входит в подрезанную гарнитуру и уехал бы на системный шрифт. */
.crumbs{list-style:none;display:flex;flex-wrap:wrap;align-items:center;
  margin:0;padding:var(--sp2) 0 0;
  font-family:var(--sans);font-size:var(--s-stamp);letter-spacing:.08em;
  text-transform:uppercase;color:var(--ink-2)}
.crumbs a{text-decoration:none}
.crumbs a:hover{text-decoration:underline}
.crumbs li+li::before{content:"";display:inline-block;width:1px;height:.75em;
  margin:0 8px -.05em;background:var(--rule)}

@media (min-width:820px){
  .foot-in{grid-template-columns:120px minmax(0,1fr)}
}
@media (max-width:700px){
  .nt-long{display:none}
  .nt-short{display:inline}
  .edition{display:none}
}

/* ============================================================ лист выпуска
   Прежде пять разделов главной вычислялись одинаково до пикселя: белая
   карточка, рамка 1 px, радиус 4 px, ноль теней, — и отличались только
   высотой. Теперь раздел различается ЗЕМЛЁЙ во всю ширину листа, а рамки
   нет ни у одного. */
main{counter-reset:secn}
section.q{padding:var(--sp4) 0;margin:0;border:0;border-radius:0;
  background:transparent}
section.q.paper{background:var(--sheet)}
section.q.register{background:var(--tint)}
/* Тёмная полоса переопределяет ТОКЕНЫ, а не перечисляет классы. Иначе
   пришлось бы вспомнить все служебные стили до единого, и любой забытый
   давал бы тёмное на тёмном: проверка контраста нашла три таких сразу, от
   1.16 до 1.83:1. В самом макете этот дефект тоже есть — подпись под
   главным числом там 1.83:1. Смена земли обязана менять краску целиком. */
section.q.plate{background:var(--deep);color:var(--deep-ink);
  --ink:var(--deep-ink);
  --ink-2:var(--deep-ink-2);
  --ink-3:var(--deep-ink-2);
  --seal:var(--deep-ink);
  --sheet:var(--deep);
  --tint:var(--deep);
  --tint-2:var(--deep);
  --hair:var(--deep-hair);
  --rule:var(--deep-hair);
  --heavy:var(--deep-ink);
  --focus:var(--focus-on-band);
  /* Алиасы прежних имён приходится переопределять ОТДЕЛЬНО: значение вида
     --card:var(--sheet) вычисляется там, где объявлено, то есть на :root, и
     наследуется уже вычисленным. Переопределение --sheet ниже по дереву его
     не трогает. Из-за этого карточка внутри тёмной полосы осталась светлой
     бумагой со светлым текстом — 1.07:1. Слой алиасов уйдёт вместе с
     последним перенесённым блоком, и это одна из причин его убрать. */
  --card:var(--deep);
  --page:var(--deep);
  --muted:var(--deep-ink-2);
  --ink-soft:var(--deep-ink-2);
  --line:var(--deep-hair);
  --line-strong:var(--deep-hair);
  --control-line:var(--deep-hair);
  --accent:var(--deep-ink);
  --accent-soft:var(--deep);
  --warn:#e8a49b;
  --warn-soft:var(--deep);
  --up:#93cfa8}
.plate a{color:var(--deep-ink)}

/* Номер раздела — счётчиком: генератору о номерах знать незачем. */
/* Считает РАЗДЕЛ, а не заголовок: на странице расчёта заголовок вложен в
   сам инструмент, и счётчик по заголовку пропускал этот раздел молча. */
section.q{counter-increment:secn}
section.q>.col::before{content:"Section " counter(secn);
  font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;color:var(--seal);
  display:block;margin-bottom:var(--sp1)}

/* ---------- титул выпуска: у документа обязаны быть выходные данные */
.titleblock{padding-top:var(--sp2);padding-bottom:var(--sp3)}
.docline{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.11em;text-transform:uppercase;color:var(--ink-2);
  margin:var(--sp2) 0;display:flex;flex-wrap:wrap;gap:4px 14px}
.docline span{white-space:nowrap}

/* Линейки трёх весов вместо одной в 1 px на всю страницу. */
.rd{height:0;border-top:3px solid var(--heavy);
  border-bottom:1px solid var(--heavy);padding-top:3px;margin:var(--sp2) 0 0}
.rs{height:0;border-top:1px solid var(--rule);margin:0}
.rh{height:0;border-top:1px solid var(--hair);margin:0}

/* ---------- набор: антиква читает, гротеск служит */
h1{font-family:var(--serif);font-size:var(--s-title);line-height:1.08;
  letter-spacing:-.022em;font-weight:600;max-width:19em;text-wrap:balance;
  margin:0}
h2{font-family:var(--serif);font-size:var(--s-head);line-height:1.2;
  letter-spacing:-.012em;font-weight:600;max-width:22em;text-wrap:balance;
  margin:0 0 var(--sp2)}
h3{font-family:var(--serif);font-size:var(--s-lead);line-height:1.3;
  font-weight:600;margin:0}
.sub{font-family:var(--serif);font-size:var(--s-lead);line-height:1.45;
  letter-spacing:-.005em;color:var(--ink-2);max-width:32em;
  margin:var(--sp1) 0 0}
.q-lead{font-family:var(--serif);font-size:var(--s-lead);line-height:1.45;
  letter-spacing:-.005em;color:var(--ink-2);max-width:32em;
  margin:0 0 var(--sp3)}
.q-lead strong{color:var(--ink);font-weight:600}
.plate .q-lead strong{color:var(--deep-ink)}
section.q p{max-width:34em}

/* ======================================================== ордер на оплату
   Карточка ответа перестаёт быть «блоком с рамкой» и становится ордером:
   тёмная плашка с реквизитами сверху, крупное число, подпись под чертой.
   В тёмной теме плашка инвертируется в пергамент — самая громкая мелкая
   поверхность страницы не должна тонуть в фоне. */
.fp-calc{border:0;border-radius:0;background:transparent;margin:0}
.fp-calc>h2{margin:0;padding:0;border:0;font-family:var(--serif);
  font-size:var(--s-head);font-weight:600;letter-spacing:-.012em}

.fp-lead .fp-hero{background:var(--band);color:var(--band-ink);
  padding:var(--sp2) clamp(18px,3vw,34px) var(--sp3);margin-top:var(--sp2)}
.fp-hero .fp-what{font-family:var(--serif);font-size:var(--s-lead);
  line-height:1.35;color:var(--band-ink);letter-spacing:0;
  text-transform:none;margin:0 0 var(--sp1);max-width:26em;
  /* Две строки заранее: смена зоны перерисовывает именно эту строку, и без
     запаса первый же выбор двигал бы число на 39 px. */
  min-height:calc(2 * 1.35 * var(--s-lead));
  padding-bottom:8px;border-bottom:1px solid var(--band-hair);font-weight:400}
.fp-hero .fp-big{font-family:var(--serif);font-size:var(--s-figure);
  line-height:1;font-weight:600;letter-spacing:-.02em;color:var(--band-ink);
  margin:var(--sp1) 0 0}
/* Подпись под числом — своим токеном. Наследование служебных чернил даёт
   на этой плашке 1.83:1, и это дефект исходного макета. */
.fp-hero .fp-ranks{font-family:var(--sans);font-size:var(--s-fine);
  line-height:1.5;color:var(--band-ink-2);margin:var(--sp2) 0 0;
  border-top:1px solid var(--band-hair);padding-top:9px}
.fp-hero .fp-ranks b{color:var(--band-ink);font-weight:700}

/* ---------- поля бланка: подчёркнутая строка, а не коробка */
.fp-fields{display:grid;gap:var(--sp2) clamp(16px,2.4vw,30px);
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
  padding:var(--sp3) clamp(18px,3vw,34px) 0;background:transparent;border:0}
.fp-field{display:flex;flex-direction:column;gap:4px;min-width:0;flex:none}
.fp-field label{font-family:var(--sans);font-size:var(--s-stamp);
  font-weight:600;letter-spacing:.11em;text-transform:uppercase;
  color:var(--ink-2);margin:0}
.fp-field select,.fp-field input{font-family:var(--sans);
  font-size:var(--s-text);line-height:1.3;color:var(--ink);
  background:var(--field);border:1px solid var(--field-line);
  border-bottom-width:2px;border-radius:0;padding:8px 10px;width:100%;
  min-width:0;appearance:none;-webkit-appearance:none}
.fp-field select{background-image:
  linear-gradient(45deg,transparent 49%,currentColor 50%,currentColor 58%,transparent 59%),
  linear-gradient(-45deg,transparent 49%,currentColor 50%,currentColor 58%,transparent 59%);
  background-size:7px 7px,7px 7px;
  background-position:right 15px top 55%,right 10px top 55%;
  background-repeat:no-repeat;padding-right:30px}
.fp-field select:hover,.fp-field input:hover{border-color:var(--ink-2)}
/* Выключенное поле меняет только краску: размер и отбивка неизменны, иначе
   включение скриптом сдвинуло бы вёрстку. */
.fp-field select:disabled,.fp-field input:disabled{color:var(--ink-3);
  background:var(--tint);border-color:var(--hair);cursor:not-allowed;
  opacity:1}
.fp-field.fp-wide{grid-column:span 2}

.fp-hint{font-family:var(--serif);font-size:var(--s-fine);line-height:1.55;
  color:var(--ink-2);background:transparent;
  padding:var(--sp2) clamp(18px,3vw,34px) 0;margin:0;max-width:44em}
.fp-note{font-family:var(--sans);font-size:var(--s-fine);line-height:1.5;
  color:var(--ink-2);padding:var(--sp2) clamp(18px,3vw,34px) 0;margin:0;
  max-width:44em}
/* Отметка о приёме индекса: без :not(:empty) пустой отступ висел бы на
   всех 75 страницах с инструментом. */
.fp-zipmsg:not(:empty){font-family:var(--sans);font-size:var(--s-fine);
  color:var(--seal);background:transparent;border:0;border-top:1px solid var(--rule);
  margin:var(--sp2) clamp(18px,3vw,34px) 0;padding:9px 0 0}

/* ---------- вывод скрипта: ведомость на бумаге, без рамки */
.fp-out{padding:var(--sp3) clamp(18px,3vw,34px) 0}
.fp-out p.fp-what{font-family:var(--sans);font-size:var(--s-stamp);
  font-weight:600;letter-spacing:.11em;text-transform:uppercase;
  color:var(--ink-2);margin:0 0 var(--sp1)}
.fp-out p.fp-big{font-family:var(--serif);
  font-size:clamp(34px,6vw,var(--s-figure));line-height:1;font-weight:600;
  letter-spacing:-.02em;margin:0 0 var(--sp2);color:var(--ink)}
.fp-lines{display:grid;grid-template-columns:1fr max-content;
  margin:0 0 var(--sp3);border-top:3px solid var(--heavy)}
.fp-lines dt{font-family:var(--sans);font-size:var(--s-fine);line-height:1.5;
  color:var(--ink-2)}
.fp-lines dd{margin:0;font-family:var(--sans);font-size:var(--s-fine);
  font-weight:700;text-align:right;line-height:1.5}
.fp-lines dt,.fp-lines dd{padding:7px 0;border-bottom:1px solid var(--hair)}
.fp-out p{margin-bottom:var(--sp2);max-width:44em}
.fp-out p.fp-src{margin-bottom:0}

@media (max-width:760px){
  /* Одна колонка полей загоняла в видимую область iOS одно поле из
     четырёх. Два в ряд помещаются: 2 x 150 + зазор < 335. */
  .fp-fields{grid-template-columns:repeat(2,minmax(0,1fr))}
  .fp-field.fp-wide{grid-column:1/-1}
}

/* ==================================== первый экран телефона: считано, не на глаз
   После переноса каркаса цифра ответа стояла на y=1047 при видимой области
   iOS Safari в 635 px. Разбор по элементам: шапка 138, меню 130, полоса
   границы 62, титул 378, отступ раздела 54, заголовок инструмента 65, строка
   выбранной клетки 122. Меню переносилось на три строки, шапка на две,
   строка выходных данных на три.
   Ниже — статические медиазапросы: скрипт их не трогает, поэтому нулевой
   сдвиг вёрстки при инициализации сохраняется по построению. */
@media (max-width:760px){
  /* шапка в одну строку: знак меньше, подзаголовок и издание не нужны —
     то же самое сказано полосой границы строкой ниже */
  .mast-in{padding:9px clamp(14px,4vw,20px);gap:11px}
  .seal{width:34px;height:34px}
  .brand{font-size:var(--s-text)}
  .tagline{display:none}

  /* меню — горизонтальный свиток вместо переноса на три строки */
  .menu-in{flex-wrap:nowrap;overflow-x:auto;overscroll-behavior-x:contain;
    scrollbar-width:none;padding:0 clamp(14px,4vw,20px)}
  .menu-in::-webkit-scrollbar{display:none}
  .menu a{white-space:nowrap;padding:8px 12px 7px;border-bottom-width:2px}

  .notice-in{padding:5px clamp(14px,4vw,20px);line-height:1.35}

  /* титул: один реквизит вместо четырёх, лид мельче */
  .wrap{padding-top:0}
  .titleblock{padding-top:var(--sp2);padding-bottom:var(--sp2)}
  .docline{margin:var(--sp1) 0;gap:2px 12px}
  .docline span:not(:first-child){display:none}
  .sub{font-size:var(--s-text);margin-top:6px}
  .rd{margin-top:var(--sp2)}

  section.q{padding:var(--sp3) 0}
  .col{padding-left:clamp(14px,4vw,20px);padding-right:clamp(14px,4vw,20px)}
  section.q>.col::before{margin-bottom:2px}
  /* Заголовок инструмента — на ступень ниже: он повторяет то, что и так
     сказано номером раздела и строкой выбранной клетки. Не прячем: раздел
     без заголовка ломает структуру документа. */
  #find .fp-calc>h2{font-size:var(--s-lead);line-height:1.25}

  .fp-lead .fp-hero{padding:11px clamp(14px,4vw,20px) var(--sp2);
    margin-top:var(--sp2)}
  /* Строка выбранной клетки: кегль служебного слоя и запас в четыре строки.
     Запас нужен потому, что скрипт перерисовывает именно её при смене зоны,
     а названия зон различаются вчетверо по длине — от «Laredo, TX» до
     «Atlanta--Athens-Clarke County--Sandy Springs, GA-AL». Без запаса первый
     же выбор двигал бы число над собой. */
  .fp-hero .fp-what{font-size:var(--s-fine);line-height:1.4;
    min-height:calc(4 * 1.4 * var(--s-fine));margin-bottom:6px;padding-bottom:6px}
  .fp-hero .fp-big{font-size:clamp(34px,9vw,44px)}
  .fp-hero .fp-ranks{margin-top:var(--sp2);padding-top:7px}
  .fp-fields{padding:var(--sp2) clamp(14px,4vw,20px) 0}
}
@media (max-width:400px){
  /* На 320 длинное название зоны занимает пять строк. */
  .fp-hero .fp-what{min-height:calc(5 * 1.4 * var(--s-fine))}
}

/* ---------- добор первого экрана, по замеру стека, а не на глаз.
   375: шапка 52 + меню 39 + полоса 55 + титул 233 + отступ 50 + заголовок 53
   + строка клетки 105 = число на 618 при сгибе 635. Ниже снято 108.
   1280: то же самое даёт 705 при сгибе 800; снято 67. */
.notice-in{padding-top:6px;padding-bottom:6px}
.docline{margin:var(--sp1) 0}
.titleblock{padding-bottom:var(--sp2)}
.rd{margin-top:var(--sp2)}
@media (min-width:761px){
  .mast-in{padding-top:11px;padding-bottom:10px}
  .docline{font-size:var(--s-stamp);gap:3px 16px}
  section.q{padding-top:var(--sp3);padding-bottom:var(--sp4)}
}
@media (max-width:760px){
  .notice-in{font-size:var(--s-stamp);letter-spacing:.01em}
  h1{font-size:clamp(25px,6.4vw,29px)}
  #find .fp-calc>h2{font-size:var(--s-text);line-height:1.3}
  .titleblock{padding-bottom:var(--sp1)}
  .rd{margin-top:var(--sp1)}
  section.q{padding-top:var(--sp2)}
  .fp-lead .fp-hero{margin-top:var(--sp1);padding-top:9px}
  /* Кегль служебного слоя и запас в пять строк: название зоны различается
     вчетверо по длине, а перерисовывает эту строку скрипт. */
  .fp-hero .fp-what{font-size:var(--s-stamp);line-height:1.4;
    min-height:calc(4 * 1.4 * var(--s-stamp))}
  .fp-hero .fp-ranks{font-size:var(--s-stamp);line-height:1.45;
    margin-top:var(--sp1);padding-top:6px}
}
@media (max-width:400px){
  .fp-hero .fp-what{min-height:calc(5 * 1.4 * var(--s-stamp))}
}
"""

MARK = ""
