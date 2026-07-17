import {
  ApiClientError,
  type CharacterDraft,
  type CultivationResultView,
  type GameApi,
  type GameStateView,
} from "./api/game";

export interface BootingState {
  readonly kind: "booting";
  readonly message: string;
}

export interface StartState {
  readonly kind: "start";
  readonly saveExists: boolean;
  readonly saveAvailable: boolean;
  readonly busy: boolean;
  readonly error: string | null;
}

export interface CreatingState {
  readonly kind: "creating";
  readonly draft: CharacterDraft;
  readonly saveExists: boolean;
  readonly name: string;
  readonly aptitudeOptionId: string | null;
  readonly traitIds: readonly string[];
  readonly overwriteConfirmed: boolean;
  readonly busy: boolean;
  readonly error: string | null;
}

export interface OverviewState {
  readonly kind: "overview";
  readonly page: "overview" | "cultivation";
  readonly game: GameStateView;
  readonly lastCultivation: CultivationResultView | null;
  readonly busy: boolean;
  readonly error: string | null;
}

export type AppState =
  BootingState | StartState | CreatingState | OverviewState;

type Listener = () => void;

export class GameController {
  readonly #api: GameApi;
  readonly #listeners = new Set<Listener>();
  #state: AppState = { kind: "booting", message: "正在检查本地游戏状态…" };

  constructor(api: GameApi) {
    this.#api = api;
  }

  get state(): AppState {
    return this.#state;
  }

  subscribe(listener: Listener): () => void {
    this.#listeners.add(listener);
    return () => this.#listeners.delete(listener);
  }

  async initialize(): Promise<void> {
    this.#setState({ kind: "booting", message: "正在检查本地游戏状态…" });
    try {
      const status = await this.#api.getStatus();
      if (status.session_active && status.state !== null) {
        this.#setState({
          kind: "overview",
          page: "overview",
          game: status.state,
          lastCultivation: null,
          busy: false,
          error: status.error?.message ?? null,
        });
        return;
      }
      this.#setState({
        kind: "start",
        saveExists: status.save_exists,
        saveAvailable: status.save_available,
        busy: false,
        error: status.error?.message ?? null,
      });
    } catch (error: unknown) {
      this.#setState({
        kind: "start",
        saveExists: false,
        saveAvailable: false,
        busy: false,
        error: errorMessage(error),
      });
    }
  }

  async startNewGame(): Promise<void> {
    const current = this.#state;
    if (current.kind !== "start" || current.busy) {
      return;
    }
    this.#setState({ ...current, busy: true, error: null });
    try {
      const draft = await this.#api.createDraft();
      this.#setState({
        kind: "creating",
        draft,
        saveExists: current.saveExists,
        name: "",
        aptitudeOptionId: null,
        traitIds: [],
        overwriteConfirmed: false,
        busy: false,
        error: null,
      });
    } catch (error: unknown) {
      this.#setState({ ...current, busy: false, error: errorMessage(error) });
    }
  }

  async continueGame(): Promise<void> {
    const current = this.#state;
    if (current.kind !== "start" || current.busy || !current.saveAvailable) {
      return;
    }
    this.#setState({ ...current, busy: true, error: null });
    try {
      const game = await this.#api.loadGame();
      this.#setState(overviewState(game));
    } catch (error: unknown) {
      this.#setState({ ...current, busy: false, error: errorMessage(error) });
    }
  }

  updateName(name: string): void {
    if (this.#state.kind === "creating" && !this.#state.busy) {
      this.#setState({ ...this.#state, name, error: null });
    }
  }

  selectAptitude(optionId: string): void {
    if (this.#state.kind === "creating" && !this.#state.busy) {
      this.#setState({
        ...this.#state,
        aptitudeOptionId: optionId,
        error: null,
      });
    }
  }

  toggleTrait(traitId: string): void {
    if (this.#state.kind !== "creating" || this.#state.busy) {
      return;
    }
    const current = this.#state;
    const selected = current.traitIds.includes(traitId);
    const traitIds = selected
      ? current.traitIds.filter((candidate) => candidate !== traitId)
      : current.traitIds.length < current.draft.required_trait_count
        ? [...current.traitIds, traitId]
        : current.traitIds;
    this.#setState({ ...current, traitIds, error: null });
  }

  setOverwriteConfirmed(confirmed: boolean): void {
    if (this.#state.kind === "creating" && !this.#state.busy) {
      this.#setState({ ...this.#state, overwriteConfirmed: confirmed });
    }
  }

  canConfirm(): boolean {
    const current = this.#state;
    return (
      current.kind === "creating" &&
      !current.busy &&
      current.name.trim().length > 0 &&
      current.aptitudeOptionId !== null &&
      current.traitIds.length === current.draft.required_trait_count &&
      (!current.saveExists || current.overwriteConfirmed)
    );
  }

  async regenerateDraft(): Promise<void> {
    const current = this.#state;
    if (current.kind !== "creating" || current.busy) {
      return;
    }
    this.#setState({ ...current, busy: true, error: null });
    try {
      const draft = await this.#api.createDraft();
      this.#setState({
        ...current,
        draft,
        aptitudeOptionId: null,
        traitIds: [],
        busy: false,
        error: null,
      });
    } catch (error: unknown) {
      this.#setState({ ...current, busy: false, error: errorMessage(error) });
    }
  }

  async confirmNewGame(): Promise<void> {
    const current = this.#state;
    if (current.kind !== "creating" || !this.canConfirm()) {
      return;
    }
    const aptitudeOptionId = current.aptitudeOptionId;
    if (aptitudeOptionId === null) {
      return;
    }
    this.#setState({ ...current, busy: true, error: null });
    try {
      const game = await this.#api.confirmNewGame({
        draft_id: current.draft.draft_id,
        name: current.name,
        aptitude_option_id: aptitudeOptionId,
        trait_ids: current.traitIds,
        overwrite_existing_save: current.overwriteConfirmed,
      });
      this.#setState(overviewState(game));
    } catch (error: unknown) {
      this.#setState({ ...current, busy: false, error: errorMessage(error) });
    }
  }

  async wait(days: number): Promise<void> {
    const current = this.#state;
    if (current.kind !== "overview" || current.busy) {
      return;
    }
    if (!Number.isInteger(days) || days <= 0) {
      this.#setState({ ...current, error: "等待天数必须是正整数。" });
      return;
    }
    this.#setState({ ...current, busy: true, error: null });
    try {
      const game = await this.#api.wait({
        days,
        expected_revision: current.game.revision,
      });
      this.#setState({
        ...current,
        game,
        busy: false,
        error: null,
      });
    } catch (error: unknown) {
      const refreshed = error instanceof ApiClientError ? error.state : null;
      this.#setState({
        ...current,
        game: refreshed ?? current.game,
        busy: false,
        error: errorMessage(error),
      });
    }
  }

  showOverview(): void {
    if (this.#state.kind === "overview" && !this.#state.busy) {
      this.#setState({ ...this.#state, page: "overview", error: null });
    }
  }

  showCultivation(): void {
    if (this.#state.kind === "overview" && !this.#state.busy) {
      this.#setState({ ...this.#state, page: "cultivation", error: null });
    }
  }

  canSeekWheel(): boolean {
    return (
      this.#state.kind === "overview" &&
      !this.#state.busy &&
      this.#state.game.cultivation.wheel_status === "seeking"
    );
  }

  async seekWheel(maxDays: number): Promise<void> {
    const current = this.#state;
    if (current.kind !== "overview" || current.busy) {
      return;
    }
    if (!Number.isInteger(maxDays) || maxDays < 1 || maxDays > 30) {
      this.#setState({
        ...current,
        page: "cultivation",
        error: "寻轮天数必须是 1 至 30 的整数。",
      });
      return;
    }
    this.#setState({
      ...current,
      page: "cultivation",
      busy: true,
      error: null,
    });
    try {
      const response = await this.#api.seekWheel({
        max_days: maxDays,
        expected_revision: current.game.revision,
      });
      this.#setState({
        kind: "overview",
        page: "cultivation",
        game: response.state,
        lastCultivation: response.cultivation_result,
        busy: false,
        error: null,
      });
    } catch (error: unknown) {
      const refreshed = error instanceof ApiClientError ? error.state : null;
      this.#setState({
        ...current,
        page: "cultivation",
        game: refreshed ?? current.game,
        busy: false,
        error: errorMessage(error),
      });
    }
  }

  #setState(state: AppState): void {
    this.#state = state;
    for (const listener of this.#listeners) {
      listener();
    }
  }
}

function overviewState(game: GameStateView): OverviewState {
  return {
    kind: "overview",
    page: "overview",
    game,
    lastCultivation: null,
    busy: false,
    error: null,
  };
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "发生未知错误，请重试。";
}
