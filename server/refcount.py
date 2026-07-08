# ruff: noqa
import os
import time
import uuid
from pathlib import Path


def _start_time(pid):
    return time.monotonic()


class Refcount:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, ref):
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in ref)
        return self.root / safe

    def _attach(self, prefix, value):
        ref = f"{prefix}-{os.getpid()}-{uuid.uuid4().hex}"
        self._path(ref).write_text(str(value), encoding="utf-8")
        return ref

    def attach(self, tool, session):
        return self._attach("ref", f"{tool}:{session}")

    def attach_turn(self, turn_id):
        return self._attach("turn", turn_id)

    def detach(self, ref):
        path = self._path(ref)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return not any(self.root.iterdir())

    def detach_turn(self, turn_id):
        for path in self.root.glob("turn-*"):
            try:
                if path.read_text(encoding="utf-8") == str(turn_id):
                    path.unlink()
            except OSError:
                pass
        return not any(self.root.iterdir())
