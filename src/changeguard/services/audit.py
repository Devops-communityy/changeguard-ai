import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class AuditLog:
    """Append-only hash-chained JSONL audit log."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()

    def append(self, event: str, actor: str, payload: dict[str, Any]) -> str:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            previous_hash = self._last_hash()
            record = {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": event,
                "actor": actor,
                "payload": payload,
                "previous_hash": previous_hash,
            }
            digest = hashlib.sha256(
                json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            record["hash"] = digest
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, separators=(",", ":")) + "\n")
            return digest

    def _last_hash(self) -> str | None:
        if not self.path.exists():
            return None
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return json.loads(lines[-1])["hash"] if lines else None
