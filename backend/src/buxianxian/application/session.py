"""Headless persistent session with save-before-memory-commit semantics."""

from dataclasses import dataclass
from typing import Self

from buxianxian.application.ports import (
    PersistenceError,
    SessionRepository,
    TransactionalRandomSource,
)
from buxianxian.domain import (
    Command,
    DomainEngine,
    DomainEvent,
    GameState,
    Rejected,
    RejectionReason,
)


@dataclass(frozen=True, slots=True)
class CommitSucceeded:
    """State and facts committed to both persistence and session memory."""

    state: GameState
    events: tuple[DomainEvent, ...]


@dataclass(frozen=True, slots=True)
class RevisionConflict:
    """Submission was based on a stale or otherwise mismatched revision."""

    expected_revision: int
    actual_revision: int


@dataclass(frozen=True, slots=True)
class CommandRejected:
    """Domain rejected the command without committing candidate state or RNG use."""

    state: GameState
    reason: RejectionReason


@dataclass(frozen=True, slots=True)
class PersistenceFailed:
    """Domain accepted a candidate that could not be durably committed."""

    state: GameState
    error: PersistenceError


type SessionResult = CommitSucceeded | RevisionConflict | CommandRejected | PersistenceFailed


class PersistentGameSession[RandomT: TransactionalRandomSource]:
    """Own one single-process authoritative state and transactional random source."""

    __slots__ = ("_engine", "_random_source", "_repository", "_state")

    def __init__(
        self,
        state: GameState,
        random_source: RandomT,
        repository: SessionRepository[RandomT],
        engine: DomainEngine,
    ) -> None:
        self._state = state
        self._random_source = random_source
        self._repository = repository
        self._engine = engine

    @classmethod
    def from_initial(
        cls,
        state: GameState,
        random_source: RandomT,
        repository: SessionRepository[RandomT],
        engine: DomainEngine | None = None,
    ) -> Self:
        """Create a session from caller-selected initial contracts without saving yet."""

        return cls(state, random_source, repository, engine or DomainEngine())

    @classmethod
    def from_save(
        cls,
        repository: SessionRepository[RandomT],
        engine: DomainEngine | None = None,
    ) -> Self:
        """Create a session from one valid repository snapshot."""

        loaded = repository.load()
        return cls(loaded.state, loaded.random_source, repository, engine or DomainEngine())

    @property
    def state(self) -> GameState:
        """Return the immutable current authoritative state."""

        return self._state

    def fork_random_source(self) -> RandomT:
        """Return a defensive RNG copy without exposing the official mutable source."""

        return self._random_source.fork()

    def submit(self, command: Command, expected_revision: int) -> SessionResult:
        """Commit one command only if revision, domain, and persistence all succeed."""

        if expected_revision != self._state.revision:
            return RevisionConflict(
                expected_revision=expected_revision,
                actual_revision=self._state.revision,
            )

        candidate_random_source = self._random_source.fork()
        transition = self._engine.transition(self._state, command, candidate_random_source)

        if isinstance(transition, Rejected):
            return CommandRejected(state=self._state, reason=transition.reason)

        try:
            self._repository.save(transition.state, candidate_random_source)
        except PersistenceError as error:
            return PersistenceFailed(state=self._state, error=error)

        self._state = transition.state
        self._random_source = candidate_random_source
        return CommitSucceeded(state=transition.state, events=transition.events)
