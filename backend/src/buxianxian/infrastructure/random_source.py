"""Stable deterministic random source with explicit serializable state."""

import re
from dataclasses import dataclass
from typing import ClassVar, Self

_UINT64_MODULUS = 1 << 64
_UINT64_MASK = _UINT64_MODULUS - 1
_OUTPUT_MULTIPLIER = 2_685_821_657_736_338_717
_SERIALIZED_STATE_PATTERN = re.compile(r"[0-9a-f]{16}")


@dataclass(frozen=True, slots=True)
class RandomStateSnapshot:
    """Portable identity, version, and state for one deterministic source."""

    algorithm: str
    version: int
    state: str


@dataclass(slots=True)
class XorShift64StarRandom:
    """Versioned xorshift64* source for deterministic non-cryptographic use."""

    ALGORITHM: ClassVar[str] = "xorshift64star"
    STATE_VERSION: ClassVar[int] = 1

    _state: int

    def __post_init__(self) -> None:
        if type(self._state) is not int or not 0 < self._state < _UINT64_MODULUS:
            raise ValueError("xorshift64star state must be a nonzero unsigned 64-bit integer")

    @classmethod
    def from_seed(cls, seed: int) -> Self:
        """Create version 1 with the seed as its initial nonzero 64-bit state."""

        return cls(_state=seed)

    @classmethod
    def from_snapshot(cls, snapshot: RandomStateSnapshot) -> Self:
        """Restore a source from a supported, explicit state snapshot."""

        if snapshot.algorithm != cls.ALGORITHM:
            raise ValueError("unsupported random algorithm")
        if snapshot.version != cls.STATE_VERSION:
            raise ValueError("unsupported random state version")
        if _SERIALIZED_STATE_PATTERN.fullmatch(snapshot.state) is None:
            raise ValueError("random state must be 16 lowercase hexadecimal digits")

        state = int(snapshot.state, 16)
        return cls(_state=state)

    def snapshot(self) -> RandomStateSnapshot:
        """Return the portable state needed to continue the exact sequence."""

        return RandomStateSnapshot(
            algorithm=self.ALGORITHM,
            version=self.STATE_VERSION,
            state=f"{self._state:016x}",
        )

    def fork(self) -> Self:
        """Return an independent source at the same sequence position."""

        return self.from_snapshot(self.snapshot())

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        """Return an unbiased integer in the inclusive interval."""

        if type(minimum) is not int or type(maximum) is not int:
            raise TypeError("random bounds must be integers")
        if minimum > maximum:
            raise ValueError("minimum cannot exceed maximum")

        span = maximum - minimum + 1
        if span > _UINT64_MODULUS:
            raise ValueError("random interval cannot contain more than 2**64 values")

        acceptance_limit = _UINT64_MODULUS - (_UINT64_MODULUS % span)
        while True:
            value = self._next_u64()
            if value < acceptance_limit:
                return minimum + (value % span)

    def _next_u64(self) -> int:
        state = self._state
        state ^= state >> 12
        state ^= (state << 25) & _UINT64_MASK
        state ^= state >> 27
        self._state = state & _UINT64_MASK
        return (self._state * _OUTPUT_MULTIPLIER) & _UINT64_MASK
