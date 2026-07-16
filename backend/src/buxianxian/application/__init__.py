"""Public contracts for headless application orchestration."""

from buxianxian.application.new_game import (
    CharacterCreationDraft,
    CharacterCreationPreparationFailed,
    CharacterCreationPreparationResult,
    CharacterCreationPrepared,
    InitialSaveFailed,
    NewGameConfirmationResult,
    NewGameCreated,
    NewGameRejected,
    NewGameService,
)
from buxianxian.application.ports import (
    LoadedSession,
    PersistenceError,
    SessionRepository,
    TransactionalRandomSource,
)
from buxianxian.application.session import (
    CommandRejected,
    CommitSucceeded,
    PersistenceFailed,
    PersistentGameSession,
    RevisionConflict,
    SessionResult,
)

__all__ = [
    "CharacterCreationDraft",
    "CharacterCreationPreparationFailed",
    "CharacterCreationPreparationResult",
    "CharacterCreationPrepared",
    "CommandRejected",
    "CommitSucceeded",
    "InitialSaveFailed",
    "LoadedSession",
    "NewGameConfirmationResult",
    "NewGameCreated",
    "NewGameRejected",
    "NewGameService",
    "PersistenceError",
    "PersistenceFailed",
    "PersistentGameSession",
    "RevisionConflict",
    "SessionRepository",
    "SessionResult",
    "TransactionalRandomSource",
]
