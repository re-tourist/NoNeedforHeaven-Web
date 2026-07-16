"""Pure deterministic character-creation generation and confirmation tests."""

from dataclasses import replace

import pytest

from buxianxian.domain import (
    APTITUDE_OPTION_COUNT,
    MAX_CHARACTER_NAME_LENGTH,
    TRAIT_OPTION_COUNT,
    CandidatesGenerated,
    CharacterCreationCandidates,
    CharacterCreationConfirmed,
    CharacterCreationErrorCode,
    CharacterCreationRejected,
    TraitDefinition,
    confirm_character_creation,
    generate_character_creation_candidates,
)
from buxianxian.infrastructure import XorShift64StarRandom


class OutOfRangeRandomSource:
    """Return an invalid value to test the random-source contract boundary."""

    def integer_inclusive(self, minimum: int, maximum: int, /) -> int:
        return maximum + 1


def _trait_catalog(count: int = 8) -> tuple[TraitDefinition, ...]:
    return tuple(
        TraitDefinition(
            trait_id=f"trait.test_{index}",
            name=f"测试词条{index}",
            description=f"用于验证创建流程的中性说明{index}",
        )
        for index in range(1, count + 1)
    )


def _generated(seed: int = 1234) -> CandidatesGenerated:
    result = generate_character_creation_candidates(
        XorShift64StarRandom.from_seed(seed),
        _trait_catalog(),
    )
    assert isinstance(result, CandidatesGenerated)
    return result


def test_same_rng_state_produces_identical_candidates_and_rng_result() -> None:
    first_random = XorShift64StarRandom.from_seed(0x1234)
    second_random = XorShift64StarRandom.from_seed(0x1234)

    first = generate_character_creation_candidates(first_random, _trait_catalog())
    second = generate_character_creation_candidates(
        second_random, tuple(reversed(_trait_catalog()))
    )

    assert first == second
    assert first_random.snapshot() == second_random.snapshot()


def test_different_rng_states_produce_different_candidates() -> None:
    first = generate_character_creation_candidates(
        XorShift64StarRandom.from_seed(1),
        _trait_catalog(),
    )
    second = generate_character_creation_candidates(
        XorShift64StarRandom.from_seed(2),
        _trait_catalog(),
    )

    assert isinstance(first, CandidatesGenerated)
    assert isinstance(second, CandidatesGenerated)
    assert first.candidates != second.candidates


def test_generated_candidate_counts_ranges_totals_and_uniqueness() -> None:
    candidates = _generated().candidates

    assert len(candidates.aptitude_options) == APTITUDE_OPTION_COUNT == 3
    assert len({option.aptitudes for option in candidates.aptitude_options}) == 3
    for option in candidates.aptitude_options:
        values = option.aptitudes.as_tuple()
        assert all(1 <= value <= 10 for value in values)
        assert sum(values) == 25

    assert len(candidates.trait_options) == TRAIT_OPTION_COUNT == 6
    assert len({trait.trait_id for trait in candidates.trait_options}) == 6


def test_insufficient_valid_trait_catalog_is_structured() -> None:
    result = generate_character_creation_candidates(
        XorShift64StarRandom.from_seed(1),
        _trait_catalog(count=5),
    )

    assert result == CharacterCreationRejected(CharacterCreationErrorCode.INSUFFICIENT_TRAITS)


def test_duplicate_or_invalid_trait_catalog_is_structured() -> None:
    catalog = _trait_catalog()
    duplicate_catalog = (*catalog, catalog[0])

    duplicate_result = generate_character_creation_candidates(
        XorShift64StarRandom.from_seed(1),
        duplicate_catalog,
    )
    invalid_result = generate_character_creation_candidates(
        XorShift64StarRandom.from_seed(1),
        (replace(catalog[0], trait_id="Invalid ID"), *catalog[1:]),
    )

    expected = CharacterCreationRejected(CharacterCreationErrorCode.INVALID_TRAIT_CATALOG)
    assert duplicate_result == expected
    assert invalid_result == expected


def test_broken_random_source_is_a_structured_generation_failure() -> None:
    result = generate_character_creation_candidates(OutOfRangeRandomSource(), _trait_catalog())

    assert result == CharacterCreationRejected(
        CharacterCreationErrorCode.RANDOM_SOURCE_CONTRACT_ERROR
    )


def test_valid_confirmation_builds_complete_normalized_initial_state() -> None:
    candidates = _generated().candidates
    aptitude_option = candidates.aptitude_options[1]
    selected_trait_ids = (
        candidates.trait_options[1].trait_id,
        candidates.trait_options[0].trait_id,
    )

    result = confirm_character_creation(
        candidates,
        name="  测试者  ",
        aptitude_option_id=aptitude_option.option_id,
        selected_trait_ids=selected_trait_ids,
    )

    assert isinstance(result, CharacterCreationConfirmed)
    assert result.state.revision == 0
    assert result.state.elapsed_days == 0
    assert result.state.player.name == "测试者"
    assert result.state.player.aptitudes == aptitude_option.aptitudes
    assert result.state.player.trait_ids == tuple(sorted(selected_trait_ids))


@pytest.mark.parametrize(
    "name",
    ["", "   ", "测试\n角色", "x" * (MAX_CHARACTER_NAME_LENGTH + 1)],
)
def test_invalid_names_are_structured(name: str) -> None:
    candidates = _generated().candidates

    result = confirm_character_creation(
        candidates,
        name=name,
        aptitude_option_id=candidates.aptitude_options[0].option_id,
        selected_trait_ids=tuple(trait.trait_id for trait in candidates.trait_options[:2]),
    )

    assert result == CharacterCreationRejected(CharacterCreationErrorCode.INVALID_NAME)


def test_forged_aptitude_option_cannot_be_confirmed() -> None:
    candidates = _generated().candidates

    result = confirm_character_creation(
        candidates,
        name="测试者",
        aptitude_option_id="aptitude_option_forged",
        selected_trait_ids=tuple(trait.trait_id for trait in candidates.trait_options[:2]),
    )

    assert result == CharacterCreationRejected(
        CharacterCreationErrorCode.INVALID_APTITUDE_SELECTION
    )


def test_wrong_trait_count_duplicate_and_unoffered_trait_are_distinct() -> None:
    candidates = _generated().candidates
    first_trait = candidates.trait_options[0].trait_id

    wrong_count = confirm_character_creation(
        candidates,
        "测试者",
        candidates.aptitude_options[0].option_id,
        (first_trait,),
    )
    duplicate = confirm_character_creation(
        candidates,
        "测试者",
        candidates.aptitude_options[0].option_id,
        (first_trait, first_trait),
    )
    unoffered = confirm_character_creation(
        candidates,
        "测试者",
        candidates.aptitude_options[0].option_id,
        (first_trait, "trait.not_offered"),
    )

    assert wrong_count == CharacterCreationRejected(
        CharacterCreationErrorCode.INVALID_TRAIT_SELECTION_COUNT
    )
    assert duplicate == CharacterCreationRejected(CharacterCreationErrorCode.DUPLICATE_TRAIT)
    assert unoffered == CharacterCreationRejected(CharacterCreationErrorCode.TRAIT_NOT_OFFERED)


def test_invalid_candidate_contract_is_rejected_at_confirmation() -> None:
    candidates = _generated().candidates
    invalid_candidates = CharacterCreationCandidates(
        aptitude_options=candidates.aptitude_options[:2],
        trait_options=candidates.trait_options,
    )

    result = confirm_character_creation(
        invalid_candidates,
        "测试者",
        candidates.aptitude_options[0].option_id,
        tuple(trait.trait_id for trait in candidates.trait_options[:2]),
    )

    assert result == CharacterCreationRejected(
        CharacterCreationErrorCode.INVALID_CANDIDATE_CONTRACT
    )
