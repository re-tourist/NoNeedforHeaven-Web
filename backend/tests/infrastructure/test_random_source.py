"""Compatibility and state-recovery tests for the concrete random source."""

import pytest

from buxianxian.infrastructure import RandomStateSnapshot, XorShift64StarRandom

UINT64_MAX = (1 << 64) - 1
SEED_ONE_KNOWN_OUTPUTS = [
    5_180_492_295_206_395_165,
    12_380_297_144_915_551_517,
    13_389_498_078_930_870_103,
    5_599_127_315_341_312_413,
    1_036_278_371_763_004_928,
]


def test_same_seed_matches_frozen_xorshift64star_v1_vector() -> None:
    first = XorShift64StarRandom.from_seed(1)
    second = XorShift64StarRandom.from_seed(1)

    first_values = [first.integer_inclusive(0, UINT64_MAX) for _ in range(5)]
    second_values = [second.integer_inclusive(0, UINT64_MAX) for _ in range(5)]

    assert first_values == second_values == SEED_ONE_KNOWN_OUTPUTS
    assert first.snapshot() == RandomStateSnapshot(
        algorithm="xorshift64star",
        version=1,
        state="081fd0210eb25e00",
    )


def test_snapshot_restore_continues_at_the_same_sequence_position() -> None:
    uninterrupted = XorShift64StarRandom.from_seed(0x1234_5678_9ABC_DEF0)
    interrupted = XorShift64StarRandom.from_seed(0x1234_5678_9ABC_DEF0)

    assert [uninterrupted.integer_inclusive(1, 100) for _ in range(4)] == [
        interrupted.integer_inclusive(1, 100) for _ in range(4)
    ]
    restored = XorShift64StarRandom.from_snapshot(interrupted.snapshot())

    assert [uninterrupted.integer_inclusive(1, 100) for _ in range(20)] == [
        restored.integer_inclusive(1, 100) for _ in range(20)
    ]
    assert uninterrupted.snapshot() == restored.snapshot()


@pytest.mark.parametrize("invalid_state", [0, -1, 1 << 64, True])
def test_invalid_internal_state_is_rejected(invalid_state: int) -> None:
    with pytest.raises(ValueError, match="nonzero unsigned 64-bit"):
        XorShift64StarRandom.from_seed(invalid_state)


def test_interval_larger_than_source_width_is_rejected() -> None:
    source = XorShift64StarRandom.from_seed(1)

    with pytest.raises(ValueError, match=r"more than 2\*\*64"):
        source.integer_inclusive(0, 1 << 64)
