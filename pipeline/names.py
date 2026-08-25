"""Короткие имена областей.

Официальные имена длинные по делу: «Atlanta--Athens-Clarke County--Sandy
Springs, GA-AL» перечисляет все города зоны. В заголовке сравнения и в
графе ведомости такое имя переносится на шесть строк и ломает разлиновку.
Правило именования должно быть ОДНО на весь сайт, иначе одна и та же
область назовётся в двух местах по-разному.
"""
from __future__ import annotations


def short_name(name: str) -> str:
    """Короткое имя для заголовка: первый город плюс код штата."""
    head, _, tail = name.partition(",")
    if head.startswith("State of"):
        return head.replace("State of", "").strip()
    if head.startswith("Rest of"):
        return "Rest of U.S."
    first = (head.split("--") if "--" in head else head.split("-"))[0].strip()
    state = tail.strip().split("-")[0].strip() if tail else ""
    return f"{first}, {state}" if state else first


