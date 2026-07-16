"""Deterministic character-creation candidates and pure confirmation rules."""

import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from buxianxian.domain.model import (
    TRAIT_SELECTION_COUNT,
    GameState,
    InnateAptitudes,
    PlayerCharacter,
    is_valid_trait_id,
    normalize_character_name,
)
from buxianxian.domain.random_source import RandomSource

APTITUDE_OPTION_COUNT = 3
TRAIT_OPTION_COUNT = 6

type _AptitudeValues = tuple[int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class TraitDefinition:
    """Minimal caller-supplied trait catalog entry without effect semantics."""

    trait_id: str
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class AptitudeOption:
    """One candidate-local selectable innate-aptitude distribution."""

    option_id: str
    aptitudes: InnateAptitudes


@dataclass(frozen=True, slots=True)
class CharacterCreationCandidates:
    """Complete choices generated for one character-creation draft."""

    aptitude_options: tuple[AptitudeOption, ...]
    trait_options: tuple[TraitDefinition, ...]


class CharacterCreationErrorCode(StrEnum):
    """Stable expected character-creation failure categories."""

    INVALID_NAME = "invalid_name"
    INVALID_APTITUDE_SELECTION = "invalid_aptitude_selection"
    INVALID_TRAIT_SELECTION_COUNT = "invalid_trait_selection_count"
    DUPLICATE_TRAIT = "duplicate_trait"
    TRAIT_NOT_OFFERED = "trait_not_offered"
    INSUFFICIENT_TRAITS = "insufficient_traits"
    INVALID_TRAIT_CATALOG = "invalid_trait_catalog"
    INVALID_CANDIDATE_CONTRACT = "invalid_candidate_contract"
    RANDOM_SOURCE_CONTRACT_ERROR = "random_source_contract_error"


@dataclass(frozen=True, slots=True)
class CandidatesGenerated:
    """Valid deterministic character-creation choices."""

    candidates: CharacterCreationCandidates


@dataclass(frozen=True, slots=True)
class CharacterCreationRejected:
    """Expected generation or confirmation failure without authoritative state."""

    error: CharacterCreationErrorCode


type CandidateGenerationResult = CandidatesGenerated | CharacterCreationRejected


@dataclass(frozen=True, slots=True)
class CharacterCreationConfirmed:
    """Complete formal initial state produced by valid confirmation."""

    state: GameState


type CharacterConfirmationResult = CharacterCreationConfirmed | CharacterCreationRejected


def generate_character_creation_candidates(
    random_source: RandomSource,
    trait_catalog: Sequence[TraitDefinition],
) -> CandidateGenerationResult:
    """Generate bounded distinct choices using only the injected random source."""

    catalog = tuple(trait_catalog)
    if not _is_valid_trait_catalog(catalog):
        return CharacterCreationRejected(CharacterCreationErrorCode.INVALID_TRAIT_CATALOG)
    if len(catalog) < TRAIT_OPTION_COUNT:
        return CharacterCreationRejected(CharacterCreationErrorCode.INSUFFICIENT_TRAITS)

    ordered_catalog = tuple(sorted(catalog, key=lambda trait: trait.trait_id))
    try:
        aptitude_values = _sample_without_replacement(
            _VALID_APTITUDE_DISTRIBUTIONS,
            APTITUDE_OPTION_COUNT,
            random_source,
        )
        trait_options = _sample_without_replacement(
            ordered_catalog,
            TRAIT_OPTION_COUNT,
            random_source,
        )
    except _RandomSourceContractError:
        return CharacterCreationRejected(CharacterCreationErrorCode.RANDOM_SOURCE_CONTRACT_ERROR)

    aptitude_options = tuple(
        AptitudeOption(
            option_id=f"aptitude_option_{index}",
            aptitudes=InnateAptitudes(*values),
        )
        for index, values in enumerate(aptitude_values, start=1)
    )
    return CandidatesGenerated(
        CharacterCreationCandidates(
            aptitude_options=aptitude_options,
            trait_options=trait_options,
        )
    )


def confirm_character_creation(
    candidates: CharacterCreationCandidates,
    name: str,
    aptitude_option_id: str,
    selected_trait_ids: Sequence[str],
) -> CharacterConfirmationResult:
    """Revalidate caller selections and produce a complete initial formal state."""

    if not _is_valid_candidate_contract(candidates):
        return CharacterCreationRejected(CharacterCreationErrorCode.INVALID_CANDIDATE_CONTRACT)

    normalized_name = normalize_character_name(name)
    if normalized_name is None:
        return CharacterCreationRejected(CharacterCreationErrorCode.INVALID_NAME)

    aptitude = next(
        (
            option.aptitudes
            for option in candidates.aptitude_options
            if option.option_id == aptitude_option_id
        ),
        None,
    )
    if aptitude is None:
        return CharacterCreationRejected(CharacterCreationErrorCode.INVALID_APTITUDE_SELECTION)

    if isinstance(selected_trait_ids, str):
        return CharacterCreationRejected(CharacterCreationErrorCode.INVALID_TRAIT_SELECTION_COUNT)
    trait_ids = tuple(selected_trait_ids)
    if len(trait_ids) != TRAIT_SELECTION_COUNT:
        return CharacterCreationRejected(CharacterCreationErrorCode.INVALID_TRAIT_SELECTION_COUNT)
    if len(set(trait_ids)) != TRAIT_SELECTION_COUNT:
        return CharacterCreationRejected(CharacterCreationErrorCode.DUPLICATE_TRAIT)

    offered_trait_ids = {trait.trait_id for trait in candidates.trait_options}
    if any(
        type(trait_id) is not str or trait_id not in offered_trait_ids for trait_id in trait_ids
    ):
        return CharacterCreationRejected(CharacterCreationErrorCode.TRAIT_NOT_OFFERED)

    player = PlayerCharacter(
        name=normalized_name,
        aptitudes=aptitude,
        trait_ids=tuple(sorted(trait_ids)),
    )
    return CharacterCreationConfirmed(
        GameState(
            revision=0,
            elapsed_days=0,
            player=player,
        )
    )


class _RandomSourceContractError(Exception):
    """Internal signal converted to a structured expected generation failure."""


def _sample_without_replacement[T](
    values: tuple[T, ...],
    count: int,
    random_source: RandomSource,
) -> tuple[T, ...]:
    available_indices = list(range(len(values)))
    selected: list[T] = []
    for position in range(count):
        try:
            selected_index = random_source.integer_inclusive(position, len(values) - 1)
        except (TypeError, ValueError, OverflowError) as error:
            raise _RandomSourceContractError from error
        if type(selected_index) is not int or not position <= selected_index < len(values):
            raise _RandomSourceContractError
        available_indices[position], available_indices[selected_index] = (
            available_indices[selected_index],
            available_indices[position],
        )
        selected.append(values[available_indices[position]])
    return tuple(selected)


def _is_valid_trait_catalog(catalog: tuple[TraitDefinition, ...]) -> bool:
    if any(not _is_valid_trait_definition(trait) for trait in catalog):
        return False
    trait_ids = tuple(trait.trait_id for trait in catalog)
    return len(set(trait_ids)) == len(trait_ids)


def _is_valid_trait_definition(trait: TraitDefinition) -> bool:
    return (
        is_valid_trait_id(trait.trait_id)
        and _is_clean_nonempty_text(trait.name)
        and _is_clean_nonempty_text(trait.description)
    )


def _is_clean_nonempty_text(value: str) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and not any(unicodedata.category(character).startswith("C") for character in value)
    )


def _is_valid_candidate_contract(candidates: CharacterCreationCandidates) -> bool:
    if len(candidates.aptitude_options) != APTITUDE_OPTION_COUNT:
        return False
    expected_option_ids = tuple(
        f"aptitude_option_{index}" for index in range(1, APTITUDE_OPTION_COUNT + 1)
    )
    if tuple(option.option_id for option in candidates.aptitude_options) != expected_option_ids:
        return False
    if len({option.aptitudes for option in candidates.aptitude_options}) != APTITUDE_OPTION_COUNT:
        return False
    if len(candidates.trait_options) != TRAIT_OPTION_COUNT:
        return False
    return _is_valid_trait_catalog(candidates.trait_options)


def _build_valid_aptitude_distributions() -> tuple[_AptitudeValues, ...]:
    distributions: list[_AptitudeValues] = []
    for constitution in range(1, 11):
        for comprehension in range(1, 11):
            for spiritual_sense in range(1, 11):
                for temperament in range(1, 11):
                    fortune = 25 - constitution - comprehension - spiritual_sense - temperament
                    if 1 <= fortune <= 10:
                        distributions.append(
                            (
                                constitution,
                                comprehension,
                                spiritual_sense,
                                temperament,
                                fortune,
                            )
                        )
    return tuple(distributions)


_VALID_APTITUDE_DISTRIBUTIONS = _build_valid_aptitude_distributions()
