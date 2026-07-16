"""Pre-session character creation with save-before-session semantics."""

from collections.abc import Sequence
from dataclasses import dataclass

from buxianxian.application.ports import (
    PersistenceError,
    SessionRepository,
    TransactionalRandomSource,
)
from buxianxian.application.session import PersistentGameSession
from buxianxian.domain import (
    CharacterCreationCandidates,
    CharacterCreationErrorCode,
    CharacterCreationRejected,
    TraitDefinition,
    confirm_character_creation,
    generate_character_creation_candidates,
)


class CharacterCreationDraft[RandomT: TransactionalRandomSource]:
    """Generated choices and the private post-generation RNG position."""

    __slots__ = ("_candidates", "_random_source")

    def __init__(
        self,
        candidates: CharacterCreationCandidates,
        random_source: RandomT,
    ) -> None:
        self._candidates = candidates
        self._random_source = random_source

    @property
    def candidates(self) -> CharacterCreationCandidates:
        """Return immutable generated choices."""

        return self._candidates

    def fork_random_source(self) -> RandomT:
        """Return a defensive copy at the post-generation sequence position."""

        return self._random_source.fork()


@dataclass(frozen=True, slots=True)
class CharacterCreationPrepared[RandomT: TransactionalRandomSource]:
    """A valid draft ready for player confirmation."""

    draft: CharacterCreationDraft[RandomT]


@dataclass(frozen=True, slots=True)
class CharacterCreationPreparationFailed:
    """Candidate generation failed without advancing the caller's RNG."""

    error: CharacterCreationErrorCode


type CharacterCreationPreparationResult[RandomT: TransactionalRandomSource] = (
    CharacterCreationPrepared[RandomT] | CharacterCreationPreparationFailed
)


@dataclass(frozen=True, slots=True)
class NewGameCreated[RandomT: TransactionalRandomSource]:
    """A persisted complete initial state exposed through a formal session."""

    session: PersistentGameSession[RandomT]


@dataclass(frozen=True, slots=True)
class NewGameRejected:
    """Player confirmation was invalid; no save or session was created."""

    error: CharacterCreationErrorCode


@dataclass(frozen=True, slots=True)
class InitialSaveFailed:
    """Valid initial state could not be persisted, so no session was created."""

    error: PersistenceError


type NewGameConfirmationResult[RandomT: TransactionalRandomSource] = (
    NewGameCreated[RandomT] | NewGameRejected | InitialSaveFailed
)


class NewGameService[RandomT: TransactionalRandomSource]:
    """Coordinate deterministic choices, confirmation, persistence, and session creation."""

    __slots__ = ("_repository", "_trait_catalog")

    def __init__(
        self,
        repository: SessionRepository[RandomT],
        trait_catalog: Sequence[TraitDefinition],
    ) -> None:
        self._repository = repository
        self._trait_catalog = tuple(trait_catalog)

    def begin(self, random_source: RandomT) -> CharacterCreationPreparationResult[RandomT]:
        """Generate a draft on an independent candidate RNG."""

        candidate_random_source = random_source.fork()
        generation = generate_character_creation_candidates(
            candidate_random_source,
            self._trait_catalog,
        )
        if isinstance(generation, CharacterCreationRejected):
            return CharacterCreationPreparationFailed(error=generation.error)
        return CharacterCreationPrepared(
            CharacterCreationDraft(generation.candidates, candidate_random_source)
        )

    def confirm(
        self,
        draft: CharacterCreationDraft[RandomT],
        name: str,
        aptitude_option_id: str,
        selected_trait_ids: Sequence[str],
    ) -> NewGameConfirmationResult[RandomT]:
        """Persist a valid complete initial state before creating its formal session."""

        confirmation = confirm_character_creation(
            draft.candidates,
            name,
            aptitude_option_id,
            selected_trait_ids,
        )
        if isinstance(confirmation, CharacterCreationRejected):
            return NewGameRejected(error=confirmation.error)

        candidate_random_source = draft.fork_random_source()
        try:
            self._repository.save(confirmation.state, candidate_random_source)
        except PersistenceError as error:
            return InitialSaveFailed(error=error)

        session: PersistentGameSession[RandomT] = PersistentGameSession[RandomT].from_initial(
            confirmation.state,
            candidate_random_source,
            self._repository,
        )
        return NewGameCreated(session=session)
