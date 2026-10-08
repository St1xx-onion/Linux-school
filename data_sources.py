"""Чтение данных из двух мест: локальная машина и домашний сервер по SSH.

Удалённый доступ сделан через системные ssh/scp, чтобы не ставить
сторонние пакеты (paramiko и т.п.) на машинах с ограничениями.
Аутентификация — по ключу, настройка в README.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from config import RemoteConfig, settings


class LocalSource:
    """Источник №1 — файлы на текущей машине."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def list_files(self) -> list[Path]:
        if not self.data_dir.exists():
            return []
        return sorted(p for p in self.data_dir.rglob("*") if p.is_file())

    def read_text(self, relative_path: str) -> str:
        return (self.data_dir / relative_path).read_text(encoding="utf-8")


class RemoteSSHSource:
    """Источник №2 — домашний сервер по SSH (ключевая аутентификация)."""

    def __init__(self, cfg: RemoteConfig) -> None:
        self.cfg = cfg

    def _ssh_base(self) -> list[str]:
        cmd = ["ssh", "-p", str(self.cfg.port)]
        if self.cfg.identity_file:
            cmd += ["-i", self.cfg.identity_file]
        # Fail fast вместо зависания, если сервер недоступен.
        cmd += ["-o", "ConnectTimeout=10", "-o", "BatchMode=yes"]
        cmd.append(f"{self.cfg.user}@{self.cfg.host}")
        return cmd

    def _require_configured(self) -> None:
        if not self.cfg.is_configured:
            raise RuntimeError(
                "Домашний сервер не настроен: впишите HOME_SERVER_HOST в .env "
                "(IP вы вспомните позже) — см. README."
            )

    def list_files(self) -> list[str]:
        self._require_configured()
        remote_cmd = f"find {self.cfg.data_dir} -type f"
        result = subprocess.run(
            self._ssh_base() + [remote_cmd],
            capture_output=True,
            text=True,
            check=True,
        )
        return [line for line in result.stdout.splitlines() if line]

    def read_text(self, relative_path: str) -> str:
        """Скачивает один файл во временную папку и возвращает его содержимое."""
        self._require_configured()
        remote_path = f"{self.cfg.data_dir.rstrip('/')}/{relative_path}"
        with tempfile.TemporaryDirectory() as tmp:
            local_copy = Path(tmp) / "downloaded"
            scp = ["scp", "-P", str(self.cfg.port)]
            if self.cfg.identity_file:
                scp += ["-i", self.cfg.identity_file]
            scp += [
                "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
                f"{self.cfg.user}@{self.cfg.host}:{remote_path}",
                str(local_copy),
            ]
            subprocess.run(scp, capture_output=True, text=True, check=True)
            return local_copy.read_text(encoding="utf-8")


def load_all() -> dict[str, list[str]]:
    """Собирает списки файлов из обоих источников.

    Если домашний сервер ещё не настроен или недоступен — локальная
    часть всё равно возвращается, а по удалённой кладётся пометка.
    """
    local = LocalSource(settings.local.data_dir)
    remote = RemoteSSHSource(settings.remote)

    out: dict[str, list[str]] = {
        "local": [str(p) for p in local.list_files()],
    }

    try:
        out["remote"] = remote.list_files()
    except RuntimeError as exc:
        out["remote"] = [f"[не настроено] {exc}"]
    except subprocess.CalledProcessError as exc:
        out["remote"] = [f"[недоступен] ssh/scp ошибка: {exc.stderr.strip()}"]
    except FileNotFoundError:
        out["remote"] = ["[нет ssh/scp] установите openssh-client"]

    return out
