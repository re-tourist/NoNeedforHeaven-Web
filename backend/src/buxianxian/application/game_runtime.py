"""Single-save application runtime for session and character-draft lifecycle."""

from collections.abc import Sequence
from dataclasses import dataclass

from buxianxian.application.new_game import (
    CharacterCreationDraft,
    CharacterCreationPreparationFailed,
    InitialSaveFailed,
    NewGameCreated,
    NewGameRejected,
    NewGameService,
)
from buxianxian.application.ports import (
    DraftIdentifierSource,
    PersistenceError,
    SingleSaveRepository,
    TransactionalRandomSource,
    TransactionalRandomSourceFactory,
)
from buxianxian.application.session import PersistentGameSession, SessionResult
from buxianxian.domain import (
    AdvanceTime,
    CharacterCreationCandidates,
    CharacterCreationErrorCode,
    GameState,
    SeekWheel,
    TraitDefinition,
)


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """Current save/session availability without exposing persistence details."""

    save_exists: bool
    save_available: bool
    session_active: bool
    state: GameState | None
    load_error: PersistenceError | None = None


@dataclass(frozen=True, slots=True)
class DraftCreated:
    """One server-owned draft projected through its opaque identifier."""

    draft_id: str
    candidates: CharacterCreationCandidates


@dataclass(frozen=True, slots=True)
class DraftCreationFailed:
    """Expected candidate-generation failure with no retained draft."""

    error: CharacterCreationErrorCode


type DraftCreationResult = DraftCreated | DraftCreationFailed


@dataclass(frozen=True, slots=True)
class DraftNotFound:
    """Submitted identifier does not name the current server draft."""


@dataclass(frozen=True, slots=True)
class SaveOverwriteRequired:
    """A save exists and explicit replacement consent was absent."""


@dataclass(frozen=True, slots=True)
class SaveInspectionFailed:
    """The configured save location could not be inspected safely."""

    error: PersistenceError


type RuntimeNewGameResult[RandomT: TransactionalRandomSource] = (
    NewGameCreated[RandomT]
    | NewGameRejected
    | InitialSaveFailed
    | DraftNotFound
    | SaveOverwriteRequired
    | SaveInspectionFailed
)


@dataclass(frozen=True, slots=True)
class GameLoaded:
    """A valid save is now the active session."""

    state: GameState


@dataclass(frozen=True, slots=True)
class GameLoadFailed:
    """A save could not be loaded into an active session."""

    error: PersistenceError


type GameLoadResult = GameLoaded | GameLoadFailed


@dataclass(frozen=True, slots=True)
class NoActiveSession:
    """A command was requested before a game session existed."""


type RuntimeCommandResult = SessionResult | NoActiveSession


@dataclass(frozen=True, slots=True)
class _StoredDraft[RandomT: TransactionalRandomSource]:
    draft_id: str
    draft: CharacterCreationDraft[RandomT]


class SingleGameRuntime[RandomT: TransactionalRandomSource]:
    """Own the mutable single-save runtime beneath transport adapters."""

    __slots__ = (
        "_draft",
        "_draft_identifier_source",
        "_new_game_service",
        "_random_source_factory",
        "_repository",
        "_session",
        "_trait_catalog",
    )

    def __init__(
        self,
        repository: SingleSaveRepository[RandomT],
        trait_catalog: Sequence[TraitDefinition],
        random_source_factory: TransactionalRandomSourceFactory[RandomT],
        draft_identifier_source: DraftIdentifierSource,
    ) -> None:
        self._repository = repository
        self._trait_catalog = tuple(trait_catalog)
        self._new_game_service = NewGameService[RandomT](repository, self._trait_catalog)
        self._random_source_factory = random_source_factory
        self._draft_identifier_source = draft_identifier_source
        self._session: PersistentGameSession[RandomT] | None = None
        self._draft: _StoredDraft[RandomT] | None = None

    @property
    def trait_catalog(self) -> tuple[TraitDefinition, ...]:
        """Return immutable prototype definitions for presentation projection."""

        return self._trait_catalog

    @property
    def active_session(self) -> PersistentGameSession[RandomT] | None:
        """Return the current session without exposing its mutable RNG."""

        return self._session

    def inspect_status(self) -> RuntimeStatus:
        """Inspect save loadability and current in-memory session state."""

        if self._session is not None:
            return RuntimeStatus(
                save_exists=True,
                save_available=True,
                session_active=True,
                state=self._session.state,
            )

        try:
            save_exists = self._repository.exists()
        except PersistenceError as error:
            return RuntimeStatus(
                save_exists=False,
                save_available=False,
                session_active=False,
                state=None,
                load_error=error,
            )

        if not save_exists:
            return RuntimeStatus(
                save_exists=False,
                save_available=False,
                session_active=False,
                state=None,
            )

        try:
            self._repository.load()
        except PersistenceError as error:
            return RuntimeStatus(
                save_exists=True,
                save_available=False,
                session_active=False,
                state=None,
                load_error=error,
            )

        return RuntimeStatus(
            save_exists=True,
            save_available=True,
            session_active=False,
            state=None,
        )

    def create_draft(self) -> DraftCreationResult:
        """Invalidate any previous draft and generate a fresh server-owned replacement."""

        self._draft = None
        preparation = self._new_game_service.begin(self._random_source_factory.create())
        if isinstance(preparation, CharacterCreationPreparationFailed):
            return DraftCreationFailed(error=preparation.error)

        draft_id = self._draft_identifier_source.create()
        if not draft_id:
            raise RuntimeError("draft identifier source returned an empty identifier")
        self._draft = _StoredDraft(draft_id=draft_id, draft=preparation.draft)
        return DraftCreated(draft_id=draft_id, candidates=preparation.draft.candidates)

    def confirm_new_game(
        self,
        draft_id: str,
        name: str,
        aptitude_option_id: str,
        selected_trait_ids: Sequence[str],
        *,
        overwrite_existing_save: bool,
    ) -> RuntimeNewGameResult[RandomT]:
        """Validate and atomically persist the current draft before replacing the session."""

        stored_draft = self._draft
        if stored_draft is None or stored_draft.draft_id != draft_id:
            return DraftNotFound()

        try:
            save_exists = self._repository.exists()
        except PersistenceError as error:
            return SaveInspectionFailed(error=error)
        if save_exists and not overwrite_existing_save:
            return SaveOverwriteRequired()

        result = self._new_game_service.confirm(
            stored_draft.draft,
            name,
            aptitude_option_id,
            selected_trait_ids,
        )
        if isinstance(result, NewGameCreated):
            self._session = result.session
            self._draft = None
        return result

    def load_game(self) -> GameLoadResult:
        """Load the configured save and make it the active session."""

        try:
            session = PersistentGameSession[RandomT].from_save(self._repository)
        except PersistenceError as error:
            return GameLoadFailed(error=error)

        self._session = session
        self._draft = None
        return GameLoaded(state=session.state)

    def wait(self, days: int, expected_revision: int) -> RuntimeCommandResult:
        """Delegate authoritative time advancement to the active persistent session."""

        if self._session is None:
            return NoActiveSession()
        return self._session.submit(AdvanceTime(days=days), expected_revision)

    def seek_wheel(
        self,
        max_days: int,
        expected_revision: int,
    ) -> RuntimeCommandResult:
        """Submit one atomic wheel-seeking cultivation action."""

        if self._session is None:
            return NoActiveSession()
        return self._session.submit(
            SeekWheel(max_days=max_days),
            expected_revision,
        )
