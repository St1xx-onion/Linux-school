#!/usr/bin/env python3
"""Точка входа: показывает, что проект видит данные из двух источников.

Запуск:  python3 main.py
"""

from __future__ import annotations

from config import settings
from data_sources import load_all


def main() -> None:
    print("Источник №1 (локально):", settings.local.data_dir)
    print(
        "Источник №2 (сервер):   ",
        settings.remote.host if settings.remote.is_configured else "НЕ НАСТРОЕН",
    )
    print("-" * 48)

    data = load_all()
    for name, files in data.items():
        print(f"[{name}] файлов: {len(files)}")
        for f in files[:20]:
            print(f"    {f}")
    print("-" * 48)
    print("Готово. Заполните .env (из .env.example), чтобы подключить сервер.")


if __name__ == "__main__":
    main()
