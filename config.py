"""Конфигурация проекта и описание двух источников данных.

Значения можно переопределять через переменные окружения или файл .env
(см. .env.example), чтобы не хранить IP и пути в коде.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Минимальный разбор .env без внешних зависимостей.

    Строки вида KEY=VALUE попадают в окружение, если такой переменной
    ещё нет (реальное окружение имеет приоритет над файлом).
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


# Подхватываем .env рядом с этим файлом, если он есть.
_load_dotenv(Path(__file__).resolve().parent / ".env")


@dataclass
class LocalConfig:
    """Источник №1 — данные на текущей (рабочей) машине."""

    # Папка с данными проекта на этой машине.
    data_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("LOCAL_DATA_DIR", "./data")
        ).expanduser()
    )


@dataclass
class RemoteConfig:
    """Источник №2 — домашний сервер, доступ по SSH.

    IP пока неизвестен — впишите его в .env (HOME_SERVER_HOST) или
    задайте алиас хоста в ~/.ssh/config (см. README) и используйте его.
    """

    # IP или имя хоста домашнего сервера. ЗАПОЛНИТЕ позже.
    host: str = os.environ.get("HOME_SERVER_HOST", "CHANGE_ME_IP_OR_HOSTNAME")
    port: int = int(os.environ.get("HOME_SERVER_PORT", "22"))
    user: str = os.environ.get("HOME_SERVER_USER", "user")
    # Папка с данными проекта на домашнем сервере.
    data_dir: str = os.environ.get("HOME_SERVER_DATA_DIR", "/srv/project/data")
    # Путь к приватному ключу (не к паролю). Пустая строка = ключ по умолчанию.
    identity_file: str = os.environ.get("HOME_SERVER_IDENTITY", "")

    @property
    def is_configured(self) -> bool:
        return self.host not in ("", "CHANGE_ME_IP_OR_HOSTNAME")


@dataclass
class Settings:
    local: LocalConfig = field(default_factory=LocalConfig)
    remote: RemoteConfig = field(default_factory=RemoteConfig)


settings = Settings()
