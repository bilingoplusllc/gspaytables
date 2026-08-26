"""Иконка вкладки и картинка для соцсетей.

Зачем. Без иконки вкладка выглядит недоделанной, а без og:image ссылка,
брошенная в Reddit — а наша аудитория сидит именно там, — разворачивается голым
текстом и читается как сломанная. Обе вещи дешёвые и обе видны всем.

Почему рисуем сами. Зависимостей у проекта нет по решению D-009, а PNG — формат
простой: заголовок, несколько блоков с контрольной суммой, сжатие через zlib.
Всё это есть в стандартной библиотеке.

Шрифт. Растеризатора у нас нет, поэтому шесть букв слова FEDPAY заданы вручную
матрицей 5x7. Больше ничего писать и не нужно: заголовок и описание площадки
подставляют сами, рядом с картинкой.

Знак. Сайт про то, что рейтинг переворачивается: кто платит больше всех, тот не
обязательно оставляет больше всех. Знак это и показывает — три полосы, где
короткая подсвечена.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# Палитра совпадает с сайтом.
INK = (19, 36, 64)      # тёмно-синяя плашка облика
PAPER = (253, 250, 243)  # лист документа
OCHRE = (123, 30, 43)   # печать облика
MUTED = (120, 128, 140)

# Шесть букв 5x7. Единица — закрашенный пиксель.
GLYPHS = {
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    # Имя сайта сменилось на GS Pay Tables, и марке понадобились новые буквы.
    # Растеризатора нет, поэтому каждая набирается матрицей 5x7 руками.
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
}


class Canvas:
    """Простейший холст RGB. Никаких зависимостей."""

    def __init__(self, w: int, h: int, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def rect(self, x, y, w, h, colour):
        r, g, b = colour
        for yy in range(max(0, y), min(self.h, y + h)):
            row = yy * self.w
            for xx in range(max(0, x), min(self.w, x + w)):
                i = (row + xx) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def text(self, s: str, x: int, y: int, scale: int, colour):
        """Пишет слово матричным шрифтом. Неизвестные символы пропускаются."""
        cx = x
        for ch in s.upper():
            rows = GLYPHS.get(ch)
            if rows is None:
                cx += 6 * scale
                continue
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + rx * scale, y + ry * scale, scale, scale,
                                  colour)
            cx += 6 * scale
        return cx

    def png(self) -> bytes:
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)                       # фильтр строки: без фильтра
            start = y * self.w * 3
            raw += self.px[start:start + self.w * 3]

        def chunk(tag: bytes, data: bytes) -> bytes:
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2,
                                             0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                + chunk(b"IEND", b""))


def _mark(c: Canvas, x: int, y: int, unit: int):
    """Знак: лестница вверх — ступени оклада.

    Прежде это были три УБЫВАЮЩИЕ полосы, и на 16 пикселях они читались как
    значок «меню», а не как знак сайта о зарплатах. Лестница повторяет фигуру
    на знаке издателя и ни на что другое не похожа.
    """
    heights = (3, 6, 9)
    base = y + unit * 10
    for i, h in enumerate(heights):
        colour = OCHRE if i == 2 else PAPER
        c.rect(x + i * unit * 4, base - h * unit, unit * 3, h * unit, colour)


def favicon_svg() -> str:
    """Векторная иконка: её понимают все современные браузеры."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" fill="#132440"/>'
        '<rect x="5" y="19" width="6" height="8" fill="#fdfaf3"/>'
        '<rect x="13" y="13" width="6" height="14" fill="#fdfaf3"/>'
        '<rect x="21" y="7" width="6" height="20" fill="#7b1e2b"/>'
        '</svg>')


def favicon_png(size: int = 32) -> bytes:
    c = Canvas(size, size, INK)
    unit = max(1, size // 16)
    _mark(c, unit * 2, unit * 3, unit)
    return c.png()


def ico(png_bytes: bytes, size: int = 32) -> bytes:
    """ICO с вложенным PNG — формат это разрешает, и так делают все.

    Нужен ради старых браузеров и ради того, что часть сервисов до сих пор
    запрашивает /favicon.ico вслепую.
    """
    return (struct.pack("<HHH", 0, 1, 1)
            + struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32,
                          len(png_bytes), 22)
            + png_bytes)


def og_image(headline: str = "") -> bytes:
    """Картинка для соцсетей, 1200x630.

    Текста на ней ровно столько, сколько можно написать честно: марка. Заголовок
    и описание площадки подставляют сами, и дублировать их картинкой незачем.
    Остальное — знак и полосы, которые показывают предмет сайта.
    """
    W, H = 1200, 630
    c = Canvas(W, H, INK)

    # Полоса-подложка под марку.
    c.rect(0, 0, W, 12, OCHRE)

    # Марка. Две строки: одно слово в одиннадцатикратном масштабе не влезает
    # в 1200 px, а резать имя нельзя.
    c.text("GS PAY", 80, 78, 11, PAPER)
    c.text("TABLES", 80, 168, 11, PAPER)

    # Полосы: убывающая длина, короткая подсвечена — тот же знак, крупно.
    bars = ((760, PAPER), (610, PAPER), (470, PAPER), (880, OCHRE))
    for i, (ln, colour) in enumerate(bars):
        y = 330 + i * 70
        c.rect(80, y, ln, 44, colour)
        c.rect(80, y + 44, ln, 4, INK)

    # Тонкая линия внизу: подпись остаётся площадке.
    c.rect(0, H - 10, W, 10, OCHRE)
    return c.png()


def write_all(dist: Path) -> list:
    """Кладёт иконки в сборку и возвращает список файлов."""
    out = []
    (dist / "favicon.svg").write_text(favicon_svg(), encoding="utf-8")
    out.append(dist / "favicon.svg")

    png32 = favicon_png(32)
    (dist / "favicon.ico").write_bytes(ico(png32, 32))
    out.append(dist / "favicon.ico")

    (dist / "apple-touch-icon.png").write_bytes(favicon_png(180))
    out.append(dist / "apple-touch-icon.png")

    (dist / "og.png").write_bytes(og_image())
    out.append(dist / "og.png")
    return out
