"""Application contracts for transactional randomness and snapshot persistence."""

from typing import Protocol, Self

from buxianxian.domain import GameState, RandomSource


class PersistenceError(Exception):
    """Base for expected persistence failures handled by application services."""


class TransactionalRandomSource(RandomSource, Protocol):
    """Random source that can create an independent candidate at its current position."""

    def fork(self) -> Self:
        """Return an independent source at exactly the same sequence position."""
        ...


class LoadedSession[RandomT: TransactionalRandomSource](Protocol):
    """Structurally loaded state and RNG returned by a session repository."""

    @property
    def state(self) -> GameState:
        """Return the loaded authoritative state."""
        ...

    @property
    def random_source(self) -> RandomT:
        """Return the loaded transactional random source."""
        ...


class SessionRepository[RandomT: TransactionalRandomSource](Protocol):
    """Persistence port required by a headless game session."""

    def save(self, state: GameState, random_source: RandomT) -> None:
        """Atomically persist one candidate state and RNG position."""
        ...

    def load(self) -> LoadedSession[RandomT]:
        """Load a previously validated state and RNG position."""
        ...
