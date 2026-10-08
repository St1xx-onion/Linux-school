#!/usr/bin/env python3
"""Проверка окружения перед запуском проекта.

Ничего не устанавливает сам (установка системных пакетов требует sudo).
Показывает, что есть, чего не хватает, и даёт точную команду установки.

Запуск:  python3 check_env.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Проекту нужны только эти модули стандартной библиотеки:
STDLIB_MODULES = [
    "os", "subprocess", "tempfile", "dataclasses", "pathlib",
]

# Внешние (pip) зависимости: их НЕТ. Список оставлен на будущее.
PIP_PACKAGES: list[str] = []

# Системные утилиты, нужные для доступа к домашнему серверу.
SYSTEM_TOOLS = ["ssh", "scp"]


def ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def bad(msg: str) -> None:
    print(f"  [НЕТ]  {msg}")


def detect_install_cmd(pkg: str) -> str:
    """Подбирает команду установки системного пакета под дистрибутив."""
    if shutil.which("apt"):
        return f"sudo apt update && sudo apt install -y {pkg}"
    if shutil.which("dnf"):
        return f"sudo dnf install -y {pkg}"
    if shutil.which("yum"):
        return f"sudo yum install -y {pkg}"
    if shutil.which("pacman"):
        return f"sudo pacman -S --noconfirm {pkg}"
    if shutil.which("zypper"):
        return f"sudo zypper install -y {pkg}"
    if shutil.which("apk"):
        return f"sudo apk add {pkg}"
    return f"(установите пакет {pkg} менеджером пакетов вашего дистрибутива)"


def main() -> int:
    problems: list[str] = []

    print("1. Версия Python")
    v = sys.version_info
    if (v.major, v.minor) >= (3, 8):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        bad(f"Python {v.major}.{v.minor} — нужен 3.8+")
        problems.append("Обновите Python до 3.8 или новее.")

    print("\n2. Модули стандартной библиотеки")
    for mod in STDLIB_MODULES:
        try:
            __import__(mod)
            ok(mod)
        except ImportError:
            bad(mod)
            problems.append(f"Модуль {mod} недоступен (повреждённый Python?).")

    print("\n3. Внешние (pip) пакеты")
    if not PIP_PACKAGES:
        ok("не требуются — проект на чистой стандартной библиотеке")

    print("\n4. Системные утилиты (для SSH к домашнему серверу)")
    for tool in SYSTEM_TOOLS:
        path = shutil.which(tool)
        if path:
            ok(f"{tool} -> {path}")
        else:
            bad(f"{tool} не найден")
            cmd = detect_install_cmd("openssh-client")
            problems.append(f"Нет {tool}. Установите openssh-client:\n       {cmd}")

    print("\n5. Файлы проекта")
    here = Path(__file__).resolve().parent
    for name in ["config.py", "data_sources.py", "main.py"]:
        if (here / name).exists():
            ok(name)
        else:
            bad(name)
            problems.append(f"Файл {name} отсутствует рядом со скриптом.")

    env_file = here / ".env"
    if env_file.exists():
        ok(".env найден")
    else:
        print("  [i]    .env не создан — скопируйте: cp .env.example .env")

    print("\n" + "=" * 52)
    if not problems:
        print("Всё готово. Запускайте:  python3 main.py")
        return 0
    print("Нужно доделать:")
    for i, p in enumerate(problems, 1):
        print(f"  {i}. {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
