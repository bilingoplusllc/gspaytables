# GS Pay Tables

Federal General Schedule pay tables for every locality pay area, with one thing the
official tables and the existing reference sites do not show: what each salary is
actually worth once local prices are taken into account.

The site is static. There is no database, no framework and no dependency outside the
Python standard library; the whole thing is six scripts that turn three public datasets
into 102 pages, plus a calculator that runs entirely in the browser.

## Sources

| Data | Source | Licence |
|---|---|---|
| Salary tables, locality percentages | U.S. Office of Personnel Management | public domain (work of the U.S. government) |
| Locality pay area definitions | U.S. Office of Personnel Management | public domain |
| Regional Price Parities, metro and state | U.S. Bureau of Economic Analysis | public domain |
| ZIP code to county relationships | U.S. Census Bureau | public domain |

GS Pay Tables is independent. It is not affiliated with, endorsed by, or connected to OPM or
any government agency.

## Build

```
python pipeline/fetch.py        # таблицы OPM, архивы BEA, связка ZIP-округ
python pipeline/parse.py        # разбирает XML в JSON, сверяет каждую ячейку
python pipeline/localities.py   # округа и штаты каждой зоны
python pipeline/rpp.py          # сопоставляет зоны с ценовыми индексами BEA
python pipeline/zips.py         # мост «почтовый индекс -> зона»
python pipeline/render.py       # собирает dist/
```

Порядок обязателен: каждый следующий шаг читает то, что записал предыдущий.

## Проверки

`parse.py` не доверяет опубликованной ставке: он пересчитывает её сам из базовой
таблицы и процента надбавки, применяет потолок в правильном порядке и сверяет с
файлом OPM. Расхождение хотя бы в одной ячейке останавливает сборку. На таблицах
2026 года сошлись все 8 700 ячеек.

`render.py` заканчивается одиннадцатью гейтами по **отрендеренному** HTML, а не по
исходникам. Каждый из них стоит там, потому что соответствующая ошибка уже была
допущена — здесь или на соседнем проекте:

| Гейт | Что ловит |
|---|---|
| кириллица | русский текст, утёкший на англоязычный сайт |
| битые вычисления | `NaN`, `None`, `$0` в готовой странице |
| дисклеймер | страница без указания на независимость от OPM |
| ссылки | внутренняя ссылка в никуда |
| объём | контентная страница тоньше 700 слов |
| направление | оговорка и карточка ответа сообщают разное о зоне |
| полнота охвата | зона молча выпала со страниц грейдов |
| пунктуация | «Rest of U.S..» — вторая точка подряд |
| крошки | разметка BreadcrumbList разошлась с видимой цепочкой |
| клиентский расчёт | формула в браузере разошлась с таблицами OPM |
| экранирование | читателю показывают \uXXXX вместо символа |

Каждый гейт проверен контролем: заведомо испорченная сборка обязана падать.
Зелёный гейт, который никогда не краснел, ничего не доказывает.

## Deploy

Cloudflare Pages, каталог `dist`. Пересборка — ежемесячно по расписанию и на
каждый push в `pipeline/`. OPM публикует новые таблицы в конце декабря, BEA
обновляет индексы цен там же; расписание существует ради этих двух недель.
