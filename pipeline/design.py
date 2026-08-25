"""Оформление GS Pay Tables — «приборная панель ведомости».

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
  /* Доведён с #7c7360: на тонированной зебре тот давал 3.81:1, а именно
     там он и стоит — официальное имя области под коротким и прочерк в
     графе без данных. Теперь 5.20 на зебре, 6.15 на бумаге. */
  --ink-3:#665e4e;       /* третий слой: подписи, заглушки, прочерк */

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
     сайта фермы, и провал загрузки превратил бы GS Pay Tables в его двойника. */
  --serif:"Source Serif 4","Iowan Old Style","Palatino Linotype",
    "Times New Roman",serif;
  --sans:"Libre Franklin","Helvetica Neue",Arial,sans-serif;

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
    --ink-3:#b3a892;
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
  --ink-3:#b3a892;
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
[id]{scroll-margin-top:var(--stick)}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}

/* Ссылка «к содержимому»: видна только при фокусе с клавиатуры. Никакого
   position:absolute — она просто схлопнута в точку, пока не понадобится. */
.skip{display:block;width:0;height:0;overflow:hidden;
  white-space:nowrap;clip-path:inset(50%)}
.skip:focus-visible{display:inline-block;width:auto;height:auto;overflow:visible;clip-path:none;
  margin:var(--sp1);padding:var(--sp1) var(--sp2);background:var(--sheet);
  color:var(--ink);box-shadow:inset 0 0 0 2px var(--seal-fill);
  text-decoration:none;font-weight:700}
html{-webkit-text-size-adjust:100%;background:var(--ground)}
body{margin:0;background:var(--ground);color:var(--ink);
  font:400 var(--s-text)/1.62 var(--serif);font-variant-numeric:tabular-nums;
  font-feature-settings:"tnum" 1;-webkit-font-smoothing:antialiased}

/* ---------- шапка: узкая полоса, не занимающая первый экран */

/* ---------- ПОЛОСА ОТВЕТА: главное структурное отличие.
   Липнет к верху, поэтому ответ никогда не уезжает из виду. */

/* ---------- раскладка: рельс и основная колонка */
/* Страницы без рельса: одна колонка разумной ширины, а не дыра в сетке. */
/* Широкая одноколоночная: главная. Рельса нет — он дублировал верхнее меню
   и отбирал 230 px слева, — но и 820 px колонки мало таблице на семь
   колонок и 58 строк. */

/* ---------- места под рекламу: заложены в раскладку заранее */
/* Сеть не подключена. Пустые пунктирные рамки с надписью Advertisement —
   это не «место под рекламу», это признак недоделанного сайта на странице,
   которая продаёт себя точностью. Показывать их будем вместе с реальными
   блоками, зарезервировав высоту под конкретный формат. */

/* ---------- типографика основной колонки */
p{margin:0 0 var(--sp2);max-width:34em;color:var(--ink)}
/* Ссылка наследует цвет своего окружения и опознаётся подчёркиванием, а не
   краской. Прежде она была жёстко цвета акцента — и в подвале на тёмной
   полосе давала 1.52:1. В печатной форме ссылка и не должна быть цветной:
   цветом там помечают величины, а не переходы. */
a{color:inherit;text-underline-offset:.18em;text-decoration-thickness:.06em}
a:hover{color:var(--seal)}
.plate a:hover,footer a:hover,.mast a:hover,.menu a:hover{color:var(--deep-ink)}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}

/* ---------- раздел-вопрос */
section.q>:last-child{margin-bottom:0}

/* ---------- сетка фактов на первом экране */
/* Ровно две колонки: при auto-fit четвёртая карточка оставалась одна в
   строке и выглядела остатком, а не частью набора. */
@media (max-width:560px){.facts{grid-template-columns:minmax(0,1fr)}}

/* ---------- оговорка. Не цветная плашка посреди чтения, а полоса на поле:
   тот же приём, что у заметок, чтобы текст ничем не разрывался. */

/* ---------- карточка вердикта. Нужна там, где ответ не одно число в полосе,
   а сопоставление двух зон: на страницах сравнения. */

/* ---------- опорная клетка: отмечена сервером, видна и без скрипта.
   Со скриптом её сменяет выбранная, и метка снимается. */

/* ---------- бухгалтерский разбор */

/* ---------- заметки на полях: оговорки больше не рвут текст */

/* ---------- таблицы */
/* overflow-x:auto делает overflow-y тоже auto, поэтому sticky в шапке
   цеплялся за контейнер, который по вертикали не прокручивается, и не липнул
   НИ НА ОДНОЙ странице. Ограниченная высота даёт настоящую прокрутку. */
/* Заголовок как кнопка сортировки: стрелка появляется только у активного
   столбца, чтобы шапка не превращалась в частокол значков. */
/* Приглушённый цвет колонки рангов относится к ТЕЛУ таблицы. В шапке она
   лежит на тёмной плашке, и служебные чернила давали там 1.83:1 — ровно тот
   дефект, что нашли в макете, только здесь его создавала специфичность:
   .rank (0,1,1) перебивал thead th (0,0,2). */


/* клетка как элемент управления: выбирается мышью и с клавиатуры */


/* ---------- полосы сравнения */

/* ---------- подписи и источники */
figure.ex{margin:0;padding:0}

/* ---------- плитки и списки */

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

/* Заголовок-сортировщик: кликает вложенная кнопка, а <th> остаётся
   заголовком столбца. role="button" на самом <th> стирал columnheader, и
   таблица из 58 строк оставалась для скринридера без заголовков вообще. */

/* ---------- подвал */
.disclaimer{color:var(--deep-ink-2);font-weight:600}

@media (max-width:1080px){
  /* Рельс уходит ПОД содержимое. В одну колонку он вставал первым, и на
     телефоне человек видел оглавление и рекламный блок раньше заголовка
     страницы — на странице грейда это пятнадцать ссылок до первой строки
     текста. Навигация не должна стоять между читателем и ответом. */
  main{order:1}
  /* Четыре поля в столбик — 291 px, из них в видимую область iOS Safari
     (635 px, а не 812 «экрана устройства») попадало одно. */
}
@media (max-width:640px){
  body{font-size:15.5px}
  /* На телефоне липкая полоса в две строки съедала пятую часть экрана.
     Вторичные числа стоят в карточке сразу под ней, поэтому в полосе
     остаётся только то, ради чего она липкая: где, что и сколько. */
  section.q{padding:var(--sp3) 0}
}
/* ---------- печать: бланк остаётся бланком, но без навигации и без земель.
   Прежнее правило обводило каждый раздел рамкой в 1 px — печатной форме
   рамки не нужны, ей нужны неразрезанные таблицы и видимые адреса ссылок. */
@media print{
  html,body{background:#fff;color:#000}
  .menu,.contents,.ad-slot,.answerbar,.skip,.fp-fields,.fp-hint{display:none}
  .mast,footer{background:#fff;color:#000;border-bottom:1px solid #000}
  .mast .brand,.mast .tagline,.mast .edition,.foot-in p,.foot-links a{color:#000}
  .sheet{box-shadow:none}
  section.q,section.q.paper,section.q.register,section.q.plate{
    background:#fff;color:#000;padding:0 0 var(--sp3);break-inside:avoid}
  .plate .fp-hero,.fp-lead .fp-hero{background:#fff;color:#000;
    border:1px solid #000}
  .scroll{max-height:none;overflow:visible;background:none}
  thead th{background:#fff;color:#000;border-bottom:1px solid #000;
    position:static}
  tbody tr:nth-child(even) th,tbody tr:nth-child(even) td{background:#fff}
  tr,img,figure{break-inside:avoid}
  h1,h2{break-after:avoid}
  main a[href^="/"]::after{content:" (@HOST@" attr(href) ")";
    font-size:11px;color:#444}
}

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
  --focus:var(--focus-on-band)}
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

/* ==================================== корешок формы: липкая полоса ответа
   Не панель приложения, а поле формы, повторяющееся на каждом листе: та же
   земля, что у ордера, реквизиты слева, поля бланка в середине, число
   справа. Ни скруглений, ни тени.

   Высота задаётся ЯВНО, а не набирается отступами. Прежде переменная --stick
   объявляла 52 px, а замеренная высота при 375 была 112.8 — метка зоны
   уходила на свою строку, и якорные ссылки из содержания промахивались на
   61 px. Число и реальность не могут разойтись, если высота одна. */
/* Правило полосы восстановлено: моя же чистка сняла его по префиксу —
   селектор `.answer` совпал с началом `.answerbar`. Тот же класс ошибки,
   что был в гейте «класс без правила», только теперь в правящем скрипте. */
.answerbar{position:sticky;top:0;z-index:20;background:var(--band);
  color:var(--band-ink);
  box-shadow:0 3px 0 var(--band),0 4px 0 var(--band-hair)}
.ab-in{max-width:1180px;margin:0 auto;
  padding:0 clamp(18px,3.4vw,40px);height:56px;box-sizing:border-box;
  display:flex;align-items:center;gap:clamp(12px,2vw,26px);flex-wrap:nowrap}
.ab-where{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.11em;text-transform:uppercase;color:var(--band-ink-2);
  flex:0 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.ab-pick{display:flex;align-items:center;gap:7px;flex:none}
.ab-pick label{font-family:var(--sans);font-size:var(--s-stamp);
  font-weight:600;letter-spacing:.11em;text-transform:uppercase;
  color:var(--band-ink-2)}
.ab-pick select{font-family:var(--sans);font-size:var(--s-fine);
  font-weight:600;color:var(--band-ink);background:transparent;
  border:0;border-bottom:1px solid var(--band-hair);border-radius:0;
  padding:2px 2px 1px;appearance:none;-webkit-appearance:none}
.ab-pick select:hover{border-bottom-color:var(--band-ink)}
.ab-pick select option{color:#191610;background:#fdfaf3}
.ab-pick select:focus-visible{outline-color:var(--focus-on-band)}
.ab-main{display:flex;align-items:baseline;gap:8px;margin-left:auto;flex:none}
.ab-big{font-family:var(--serif);font-size:clamp(21px,2.6vw,27px);
  line-height:1;font-weight:600;letter-spacing:-.02em;color:var(--band-ink)}
.ab-unit{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.11em;text-transform:uppercase;color:var(--band-ink-2)}
.ab-more{display:flex;gap:clamp(14px,2vw,26px);flex:none}
.ab-more div{display:flex;flex-direction:column;gap:1px}
.ab-more .v{font-family:var(--sans);font-size:var(--s-fine);font-weight:700;
  line-height:1.2;color:var(--band-ink)}
.ab-more .k{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.1em;text-transform:uppercase;color:var(--band-ink-2);
  line-height:1.2}

/* ---------- одна переменная кормит и отступ якоря, и липкую шапку таблицы.
   Прежде обе объявляли top:0 и спорили: полоса выигрывала, и шапка матрицы
   ставок на 58 страницах не была видна ни разу — строки с одиннадцатой по
   пятнадцатую читались без подписей столбцов. Гейты при этом были зелёными:
   конфликт живёт в разложенном документе, а не в тексте. */
/* Переменная кормит ОТСТУП ЯКОРЯ. Липкой шапке таблицы она не нужна:
   таблица лежит в своём контейнере с ограниченной высотой, шапка липнет к
   его краю, и смещение на высоту полосы оставляло бы внутри контейнера
   пустую полосу в 44-56 px, над которой уезжали бы строки. */
body{--stick:0px}
/* Признак «на странице есть липкая полоса». Правило было снесено чисткой
   Ш8 (её шаблон начинался с body и захватил body.withbar), и отступ
   якоря на десктопе молча обнулился на 58 страницах. */
body.withbar{--stick:56px}
/* Дополнительные цифры полосы требуют около 600 px сверх остального и не
   помещаются вплоть до 1080: при 768 они уезжали за правый край на 291 px и
   давали горизонтальную прокрутку всей странице. Полоса без них по-прежнему
   отвечает на главный вопрос: область, клетка, число. */
@media (max-width:1200px){.ab-more{display:none}}
@media (max-width:760px){
  .ab-in{height:44px;gap:10px}
  .ab-pick label{display:none}
  /* Отступ якоря обязан идти за высотой полосы: иначе переход из содержания
     перелетает заголовок на 12 px. Правило было снесено той же чисткой Ш8. */
  body.withbar{--stick:44px}
}
@media (max-width:520px){
  .ab-where{display:none}
}

/* ======================================================== ведомость и сетка
   Два разных документа. Ведомость — перечень областей, её набирают антиквой
   и просторно. Тарифная сетка — 8 700 клеток, её печатают служебной
   гарнитурой и плотно: при плотности ведомости она растянулась бы примерно
   на 1200 px в окне 330, то есть на 3.6 экрана боковой прокрутки. */
.scroll{overflow:auto;max-height:calc(min(74vh,760px) - var(--stick));
  overscroll-behavior-x:contain;
  border-top:3px solid var(--heavy);border-bottom:3px solid var(--heavy);
  /* Признак боковой прокрутки: два градиента на местных координатах дают
     край листа, два на прокрутке — тень. Тень видна только с той стороны,
     куда ещё можно ехать. У макета этого нет вовсе, а при 375 таблица едет
     вбок в 2.3 раза. */
  background:
    linear-gradient(to right,var(--sheet),transparent) 0 0/22px 100% no-repeat local,
    linear-gradient(to left,var(--sheet),transparent) 100% 0/22px 100% no-repeat local,
    linear-gradient(to right,var(--shade),transparent) 0 0/12px 100% no-repeat scroll,
    linear-gradient(to left,var(--shade),transparent) 100% 0/12px 100% no-repeat scroll}

table{width:100%;border-collapse:separate;border-spacing:0;
  font-family:var(--serif);font-size:var(--s-text);line-height:1.35}
thead th{position:sticky;top:0;z-index:2;
  background:var(--band);color:var(--band-ink);
  font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.1em;text-transform:uppercase;text-align:left;padding:0;
  border-bottom:1px solid var(--band)}
thead th:not(:has(button)){padding:12px 16px}
thead th button{all:unset;display:block;width:100%;box-sizing:border-box;
  padding:12px 16px;cursor:pointer;color:inherit;font-family:var(--sans);
  font-size:var(--s-stamp);font-weight:600;line-height:1.3;
  letter-spacing:.1em;text-transform:uppercase}
thead th button:hover{background:var(--seal-fill);color:var(--seal-on)}
thead th:focus-within{outline:2px solid var(--focus-on-band);outline-offset:-2px}
thead th.num button,thead th.num{text-align:right}
thead th[aria-sort="ascending"] button::after{content:"";display:inline-block;
  width:0;height:0;margin-left:7px;vertical-align:.1em;
  border-left:4px solid transparent;border-right:4px solid transparent;
  border-bottom:5px solid currentColor}
thead th[aria-sort="descending"] button::after{content:"";display:inline-block;
  width:0;height:0;margin-left:7px;vertical-align:.1em;
  border-left:4px solid transparent;border-right:4px solid transparent;
  border-top:5px solid currentColor}

tbody th{text-align:left;font-weight:400;font-family:var(--serif);
  padding:11px 16px;border-bottom:1px solid var(--hair);
  background:var(--sheet)}
tbody td{padding:11px 16px;border-bottom:1px solid var(--hair);
  white-space:nowrap;background:var(--sheet)}
tbody td.num{text-align:right}
tbody td.rank{font-family:var(--sans);font-size:var(--s-fine);font-weight:600;
  color:var(--ink-2);width:1%;padding-left:20px;text-align:right}
tbody tr:nth-child(even) th,tbody tr:nth-child(even) td{background:var(--tint)}
tbody tr:hover th,tbody tr:hover td{background:var(--tint-2)}
/* Опорная линия каждые десять строк: ведомость на 58 строк без них не
   читается, а линия работает при любой сортировке. */
tbody tr:nth-child(10n) th,tbody tr:nth-child(10n) td{
  border-bottom:1px solid var(--rule)}
tbody th a{text-decoration:underline;text-decoration-color:var(--hair);
  text-decoration-thickness:1px;text-underline-offset:.2em}
tbody th a:hover{text-decoration-color:var(--seal)}
tbody tr.you th,tbody tr.you td{background:var(--loss-soft);font-weight:600}
tbody tr.you th{box-shadow:inset 4px 0 0 var(--seal-fill)}
td.up{color:var(--gain);font-weight:600}
td.down{color:var(--loss);font-weight:600}
td.flat{color:var(--ink-3)}

.tlegend{display:grid;gap:5px;margin:10px 0 0;font-family:var(--sans);
  font-size:var(--s-fine);line-height:1.5;color:var(--ink-2);max-width:52em}

/* ---------- тарифная сетка: та же разлиновка, но плотнее и служебным
   шрифтом. 8 700 клеток — это таблица, а не перечень. */
table.pay{font-family:var(--sans);font-size:var(--s-fine);width:auto;
  min-width:100%}
table.pay tbody th,table.pay tbody td{padding:7px 10px;white-space:nowrap;
  line-height:1.3}
table.pay thead th{padding:0}
table.pay thead th button{padding:9px 10px}
table.pay thead th:not(:has(button)){padding:9px 10px;text-align:right}
table.pay tbody th[scope="row"]{position:sticky;left:0;z-index:1;
  font-family:var(--sans);font-weight:600;min-width:7ch;
  border-right:2px solid var(--rule)}
table.pay thead th:first-child{position:sticky;left:0;z-index:3;
  border-right:2px solid var(--rule)}
table.pay th.gut,table.pay td.gut{border-left:2px solid var(--rule)}
table.pay td.cell{text-align:right;cursor:pointer}
table.pay td.cell:hover{background:var(--tint-2);
  box-shadow:inset 0 0 0 1px var(--rule)}
/* Выбранная клетка получает ту же краску, что корешок формы и колонтитул
   ведомости: одна плашка на весь документ, а не третий акцент. */
table.pay td.sel{background:var(--band);color:var(--band-ink);font-weight:700}
table.pay td.ref{box-shadow:inset 0 0 0 2px var(--seal-fill)}
table.pay td.capped{color:var(--loss)}
table.pay td.cell:focus-visible{outline:2px solid var(--focus);
  outline-offset:-2px}

@media (max-width:760px){
  tbody th,tbody td{padding:9px 12px}
  tbody td.rank{padding-left:12px}
  /* Графа наименования примораживается к краю. Липкий столбец обязан иметь
     непрозрачный фон во ВСЕХ четырёх состояниях, иначе сквозь него видны
     уезжающие цифры. */
  table:not(.pay) tbody th{position:sticky;left:0;z-index:1;
    border-right:1px solid var(--rule)}
  table:not(.pay) thead th:nth-child(2){position:sticky;left:0;z-index:3;
    border-right:1px solid var(--band-hair)}
  table.pay tbody th[scope="row"]{min-width:6ch}
  .scroll{max-height:calc(min(70vh,620px) - var(--stick))}
}

/* Табличные цифры объявлены один раз на body и наследуются: блок
   восстановления больше не нужен, потому что сокращений font: в этом
   файле не осталось нигде, кроме самого body, где длинная запись
   стоит следом. Гейт табличных цифр остаётся: он покраснеет, если
   сокращение вернётся. */

/* Графа наименования: короткое имя крупно, официальное — мелко и одной
   строкой. Прежде официальное имя переносилось на шесть строк, и строки
   ведомости прыгали от 42 до 180 px. */
tbody th .full{display:block;font-family:var(--sans);font-size:var(--s-stamp);
  line-height:1.4;color:var(--ink-3);white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;max-width:26ch;margin-top:1px}
tbody th a{white-space:nowrap}

/* ================================================ врезки чисел и перечни
   Ни одной рамки вокруг блока: числа отделяются тяжёлой линейкой сверху,
   как графы в бланке. Число набирается антиквой, подпись — гротеском
   прописными. */
.facts{display:grid;gap:0 clamp(26px,3.4vw,52px);
  grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
  margin:var(--sp3) 0 0}
.fact{padding:var(--sp2) 0;border:0;border-radius:0;background:transparent;
  border-top:3px solid var(--rule)}
.fact .fact-k{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.11em;text-transform:uppercase;color:var(--ink-2);
  margin:0 0 var(--sp1)}
.fact .kpi{display:block;font-family:var(--serif);font-size:var(--s-kpi);
  line-height:1.05;font-weight:600;letter-spacing:-.02em;color:var(--ink)}
.fact .kpi-sub{display:block;font-family:var(--sans);font-size:var(--s-fine);
  line-height:1.5;color:var(--ink-2);margin-top:var(--sp1);max-width:32em}

/* ---------- ведомость слагаемых: как расчётная часть формы */
.ledger{margin:var(--sp3) 0 0;border-top:3px solid var(--heavy)}
.ledger div{display:flex;justify-content:space-between;gap:16px;
  padding:8px 0;border-bottom:1px solid var(--hair)}
.ledger dt{font-family:var(--sans);font-size:var(--s-fine);color:var(--ink-2);
  margin:0}
.ledger dd{margin:0;font-family:var(--sans);font-size:var(--s-fine);
  font-weight:700;white-space:nowrap}
.ledger div.total{border-bottom:0;border-top:1px solid var(--heavy);
  padding-top:11px;margin-top:3px}
.ledger div.total dt{color:var(--ink);font-weight:600}
.ledger div.total dd{font-family:var(--serif);font-size:var(--s-lead);
  font-weight:600}

/* ---------- ответ на странице сравнения */
.answer{border:0;border-radius:0;background:transparent;
  border-top:3px solid var(--heavy);padding:var(--sp2) 0 0;margin:var(--sp3) 0 0}
.answer .what{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.11em;text-transform:uppercase;color:var(--ink-2);margin:0}
.answer .big{display:block;font-family:var(--serif);font-size:var(--s-kpi);
  line-height:1.1;font-weight:600;letter-spacing:-.02em;margin:var(--sp1) 0 0}
.answer .body{display:block;font-family:var(--sans);font-size:var(--s-fine);
  line-height:1.5;color:var(--ink-2);margin-top:var(--sp1);max-width:40em}

/* ---------- полосы величин. Полоса всегда идёт рядом с числом, а шкала
   объявлена в подписи: полоса без объявленной шкалы врёт ровно так, как
   соврала гистограмма с неравными корзинами на соседнем сайте. */
.bars{margin:var(--sp2) 0 0;padding:0;list-style:none}
.bars li{display:grid;grid-template-columns:minmax(0,1fr) max-content;
  gap:3px 14px;align-items:baseline;padding:7px 0;
  border-bottom:1px solid var(--hair)}
.bars .nm{font-family:var(--serif);font-size:var(--s-fine);color:var(--ink)}
.bars .v{font-family:var(--sans);font-size:var(--s-fine);font-weight:700;
  text-align:right;white-space:nowrap}
.bar{grid-column:1/-1;display:block;height:9px;background:var(--tint-2);
  border-radius:0}
.bar span{display:block;height:100%;background:var(--band);border-radius:0}
.bars li.hi .bar span{background:var(--seal-fill)}
.bars li.hi .nm{font-weight:600}

/* ---------- экспонат: то, чего нет ни у кого, помечено как приложение */
.ex{margin:var(--sp3) 0 0;border-top:3px solid var(--heavy);
  padding-top:var(--sp2)}
.ex-kicker{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;color:var(--seal);margin:0}
.ex-title{font-family:var(--serif);font-size:var(--s-lead);font-weight:600;
  line-height:1.3;margin:var(--sp1) 0 var(--sp2);max-width:30em}
.ex-note{font-family:var(--sans);font-size:var(--s-fine);line-height:1.5;
  color:var(--ink-2);margin:var(--sp2) 0 0;max-width:44em}
figcaption{font-family:var(--sans);font-size:var(--s-fine);line-height:1.5;
  color:var(--ink-2);margin-top:var(--sp2)}

/* ---------- плитки потолка */
.grid2{display:grid;gap:0 clamp(20px,3vw,44px);
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr));margin:var(--sp2) 0 0}
.tile{border:0;border-radius:0;background:transparent;
  border-top:1px solid var(--rule);padding:var(--sp2) 0}
.tile .k{display:block;font-family:var(--sans);font-size:var(--s-stamp);
  font-weight:600;letter-spacing:.11em;text-transform:uppercase;
  color:var(--ink-2)}
.tile .v{display:block;font-family:var(--serif);font-size:var(--s-lead);
  font-weight:600;margin:2px 0 4px}
.tile .d{display:block;font-family:var(--sans);font-size:var(--s-fine);
  line-height:1.5;color:var(--ink-2)}

/* ---------- перечни: не «плашки», а строки указателя */
.chips,.chips-plain,.counties{display:flex;flex-wrap:wrap;gap:0 0;
  margin:var(--sp2) 0 0;padding:0;list-style:none}
.chips a,.chips-plain li,.counties li{display:inline-block;
  font-family:var(--sans);font-size:var(--s-fine);color:var(--ink);
  text-decoration:none;padding:5px 0;margin-right:0;border:0;border-radius:0}
.chips a::after,.chips-plain li:not(:last-child)::after,
.counties li:not(:last-child)::after{content:"";display:inline-block;width:1px;
  height:.75em;margin:0 11px -.05em;background:var(--rule)}
.chips a:hover{color:var(--seal);text-decoration:underline}

.chips-pay{display:grid;gap:0;margin:var(--sp2) 0 0;
  grid-template-columns:repeat(auto-fill,minmax(160px,1fr))}
.chips-pay a{display:flex;justify-content:space-between;align-items:baseline;
  gap:10px;padding:9px 0;border:0;border-radius:0;background:transparent;
  border-bottom:1px solid var(--hair);text-decoration:none;color:var(--ink);
  margin-right:clamp(16px,2.4vw,34px)}
.chips-pay a:hover{border-bottom-color:var(--seal)}
.chips-pay b{font-family:var(--sans);font-size:var(--s-fine);font-weight:700}
.chips-pay span{font-family:var(--sans);font-size:var(--s-fine);
  color:var(--ink-2)}

/* ---------- оговорка: отступ и линейка вместо рамки. Курсива нет — его
   начертание не вшито, а наклонять римское значит подделывать. */
.caveat{border:0;border-radius:0;background:transparent;
  border-left:3px solid var(--seal-fill);padding:2px 0 2px var(--sp2);
  margin:var(--sp3) 0 0;color:var(--ink-2);max-width:38em}
.caveat p{margin:0}
.caveat strong{color:var(--ink)}

.rail-note{font-family:var(--sans);font-size:var(--s-fine);color:var(--ink-2);
  margin:0}

/* ================================================== места под объявления
   Сеть не подключена, места скрыты: читатель не должен видеть три пустые
   рамки на сайте, который продаёт себя точностью. Но место существует уже
   сейчас, с правильной зарезервированной высотой — иначе в день подключения
   объявление раздвинет вёрстку, и работа над нулевым сдвигом пропадёт.

   Формат выбирается ПО ЗАМЕРУ, а не по желанию: на 768 полоса даёт 667 px,
   значит ни 970x250, ни 728x90 туда не входят. */
.ad-slot{display:none;margin:0;padding:0;border:0;background:transparent}
.ad-slot.on{display:flex;align-items:center;justify-content:center;
  background:var(--tint-2);border-top:1px solid var(--hair);
  border-bottom:1px solid var(--hair);
  font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);
  overflow:hidden}
/* Полоса в потоке: высота под конкретный формат на каждой ширине. */
.ad-band.on{width:100%;min-height:280px;margin:var(--sp3) 0}
/* Пороги считаны от ширины КОЛОНКИ, а не окна: место живёт внутри листа с
   полями, и на окне 1010 оно всего 886 px — объявление 970 там обрезалось
   бы. Колонка достигает 728 на окне 840 и 970 на окне 1090. */
@media (min-width:840px){.ad-band.on{min-height:90px}}
@media (min-width:1110px){.ad-band.on{min-height:250px}}
/* Башня на полях: живёт в маргиналиях и держит свою ширину. */
.ad-rail.on{width:300px;min-height:600px;margin:var(--sp3) 0 0}

/* Полоса объявления во всю ширину листа. .adzone существует всегда, чтобы
   разметка не менялась при подключении сети; высоту держит само место. */
.adzone{padding:0 clamp(14px,2.2vw,20px)}
.adzone .ad-band.on{margin:0 auto}

/* ================================================== поля документа
   У бланка есть поля, и на них выносят пометки — как сбоку печатают «см.
   п. 4». Сюда уходит легенда таблицы: под таблицей её не читают, потому что
   глаз уже уехал дальше. Сюда же встаёт рекламная башня — в одноколоночном
   документе ей иначе негде стоять. */
.grid{display:grid;grid-template-columns:minmax(0,1fr);gap:var(--sp3) 0}
@media (min-width:1000px){
  /* Колонка полей меряется по содержимому: пока сеть не подключена и на поле
     нет ничего, кроме скрытой башни, она занимает ноль и содержание
     пользуется всей шириной. */
  .grid{grid-template-columns:minmax(0,1fr) auto;
    gap:0 clamp(26px,3.6vw,56px)}
  .marg{max-width:300px}
}
.marg{min-width:0}
.marg .note{border-top:1px solid var(--rule);padding-top:9px;
  margin-bottom:var(--sp3)}
.marg .note:last-child{margin-bottom:0}
.marg .note-k{font-family:var(--sans);font-size:var(--s-stamp);font-weight:600;
  letter-spacing:.11em;text-transform:uppercase;color:var(--seal);
  margin:0 0 5px}
.marg .tlegend{margin:0}
.marg .ad-rail.on{margin-top:var(--sp3)}

/* Широкая таблица полей себе позволить не может: главная ведомость на семь
   граф сжималась с 965 до 634. Её пометки и башня встают под таблицей. */
.marg-under{display:flex;flex-wrap:wrap;align-items:flex-start;
  gap:var(--sp3) clamp(26px,3.6vw,56px);margin-top:var(--sp2)}
.marg-under .note{flex:1 1 320px;max-width:44em}
.marg-under .ad-rail.on{flex:none;margin-top:0}
"""

MARK = ""
