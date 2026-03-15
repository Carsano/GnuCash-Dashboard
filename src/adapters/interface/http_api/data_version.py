"""In-memory data version state for HTTP API responses."""

from threading import Lock


class DataVersionStore:
    """Thread-safe counter used as API data version."""

    def __init__(self, initial: int = 1) -> None:
        self._value = initial
        self._lock = Lock()

    def get(self) -> int:
        """Return current data version."""
        with self._lock:
            return self._value

    def bump(self) -> int:
        """Increment data version and return the new value."""
        with self._lock:
            self._value += 1
            return self._value

