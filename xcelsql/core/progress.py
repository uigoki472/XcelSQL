"""Terminal spinner / progress indicator utilities."""
from __future__ import annotations
import sys
import threading
import time
from contextlib import contextmanager

class Spinner:
    def __init__(self, message: str = "Working", enabled: bool = True, interval: float = 0.1):
        self.message = message
        self.enabled = enabled and sys.stderr.isatty()
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._frames = ['|', '/', '-', '\\']

    def _run(self):
        i = 0
        while not self._stop.is_set():
            frame = self._frames[i % len(self._frames)]
            sys.stderr.write(f"\r{self.message} {frame}")
            sys.stderr.flush()
            time.sleep(self.interval)
            i += 1
        # clear line
        sys.stderr.write("\r" + ' ' * (len(self.message) + 2) + "\r")
        sys.stderr.flush()

    def __enter__(self):
        if self.enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.enabled:
            self._stop.set()
            if self._thread:
                self._thread.join()

@contextmanager
def spinner(message: str = "Working", enabled: bool = True, interval: float = 0.1):
    sp = Spinner(message, enabled=enabled, interval=interval)
    try:
        sp.__enter__()
        yield sp
    finally:
        sp.__exit__(None, None, None)
