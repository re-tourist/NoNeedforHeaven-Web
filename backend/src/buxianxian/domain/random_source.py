"""Injectable deterministic-randomness boundary for pure domain code."""

from typing import Protocol


class RandomSource(Protocol):
    """Supply a controlled integer within the requested inclusive bounds."""

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        """Return an integer in the inclusive interval [minimum, maximum]."""
        ...
