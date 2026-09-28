from __future__ import annotations

import asyncio
from pathlib import Path

import clamd

from app.config import Settings
from app.config import settings


class FileScanError(RuntimeError):
    pass


class MalwareDetectedError(FileScanError):
    pass


class FileScanner:
    def __init__(self, model_settings: Settings | None = None) -> None:
        model_settings = model_settings or settings
        self.enabled = model_settings.antivirus_enabled
        self.host = model_settings.antivirus_host
        self.port = model_settings.antivirus_port
        self.timeout = model_settings.antivirus_timeout_seconds

    async def scan(self, path: Path) -> dict[str, str | bool]:
        if not self.enabled:
            return {
                "scanned": False,
                "safe": True,
                "reason": "antivirus_disabled",
            }

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self._scan_sync,
                    path,
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as exc:
            raise FileScanError("antivirus_scan_timeout") from exc
        except Exception as exc:
            raise FileScanError("antivirus_scan_failed") from exc

        if result.get("status") == "FOUND":
            raise MalwareDetectedError(
                str(result.get("reason") or "malware_detected"),
            )

        return {
            "scanned": True,
            "safe": True,
            "reason": str(result.get("reason") or "clean"),
        }

    def _scan_sync(self, path: Path) -> dict[str, str | bool]:
        client = clamd.ClamdNetworkSocket(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )

        with path.open("rb") as handle:
            result = client.scan_stream(handle.read())

        _, data = result["stream"]
        status, reason = data

        return {
            "status": status,
            "reason": reason,
        }
