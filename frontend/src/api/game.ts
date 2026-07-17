export type ApiErrorCode =
  | "invalid_request"
  | "no_active_session"
  | "save_not_found"
  | "save_corrupt"
  | "save_unsupported"
  | "save_load_failed"
  | "draft_not_found"
  | "draft_creation_failed"
  | "invalid_name"
  | "invalid_aptitude_selection"
  | "invalid_trait_selection"
  | "save_overwrite_required"
  | "revision_conflict"
  | "time_command_rejected"
  | "cultivation_command_rejected"
  | "persistence_failed";

export type ClientErrorCode =
  ApiErrorCode | "network_error" | "invalid_response";

export interface Aptitudes {
  readonly constitution: number;
  readonly comprehension: number;
  readonly spiritual_sense: number;
  readonly temperament: number;
  readonly fortune: number;
}

export interface TraitSummary {
  readonly trait_id: string;
  readonly name: string;
  readonly description: string;
}

export interface PlayerSummary {
  readonly name: string;
  readonly aptitudes: Aptitudes;
  readonly traits: readonly TraitSummary[];
}

export interface GameStateView {
  readonly revision: number;
  readonly elapsed_days: number;
  readonly player: PlayerSummary;
  readonly cultivation: CultivationStateView;
}

export interface CultivationStateView {
  readonly stage: "seeking_wheel";
  readonly wheel_insight: number;
  readonly wheel_status: "seeking" | "suspected_sighting";
  readonly suspected_sighting_threshold: number;
}

export interface ApiErrorDetail {
  readonly code: ApiErrorCode;
  readonly message: string;
}

export interface GameStatus {
  readonly save_exists: boolean;
  readonly save_available: boolean;
  readonly session_active: boolean;
  readonly state: GameStateView | null;
  readonly error: ApiErrorDetail | null;
}

export interface AptitudeOption {
  readonly option_id: string;
  readonly aptitudes: Aptitudes;
}

export interface CharacterDraft {
  readonly draft_id: string;
  readonly aptitude_options: readonly AptitudeOption[];
  readonly trait_options: readonly TraitSummary[];
  readonly required_trait_count: number;
}

export interface ConfirmNewGameInput {
  readonly draft_id: string;
  readonly name: string;
  readonly aptitude_option_id: string;
  readonly trait_ids: readonly string[];
  readonly overwrite_existing_save: boolean;
}

export interface WaitInput {
  readonly days: number;
  readonly expected_revision: number;
}

export interface SeekWheelInput {
  readonly max_days: number;
  readonly expected_revision: number;
}

export interface CultivationResultView {
  readonly requested_max_days: number;
  readonly actual_days_elapsed: number;
  readonly previous_insight: number;
  readonly current_insight: number;
  readonly ordinary_insight_gained: number;
  readonly inspiration_insight_gained: number;
  readonly reached_suspected_sighting: boolean;
  readonly previous_elapsed_days: number;
  readonly current_elapsed_days: number;
}

export interface CultivationResponse {
  readonly state: GameStateView;
  readonly cultivation_result: CultivationResultView;
}

export interface GameApi {
  getStatus(): Promise<GameStatus>;
  createDraft(): Promise<CharacterDraft>;
  confirmNewGame(input: ConfirmNewGameInput): Promise<GameStateView>;
  loadGame(): Promise<GameStateView>;
  wait(input: WaitInput): Promise<GameStateView>;
  seekWheel(input: SeekWheelInput): Promise<CultivationResponse>;
}

export class ApiClientError extends Error {
  readonly code: ClientErrorCode;
  readonly state: GameStateView | null;

  constructor(
    code: ClientErrorCode,
    message: string,
    state: GameStateView | null = null,
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.state = state;
  }
}

export class HttpGameApi implements GameApi {
  readonly #fetcher: typeof fetch;

  constructor(fetcher: typeof fetch = (input, init) => fetch(input, init)) {
    this.#fetcher = fetcher;
  }

  async getStatus(): Promise<GameStatus> {
    return parseGameStatus(await this.#request("/api/game", { method: "GET" }));
  }

  async createDraft(): Promise<CharacterDraft> {
    return parseCharacterDraft(
      await this.#request("/api/game/drafts", { method: "POST" }),
    );
  }

  async confirmNewGame(input: ConfirmNewGameInput): Promise<GameStateView> {
    const payload = await this.#request("/api/game/new", {
      method: "POST",
      body: JSON.stringify(input),
    });
    return parseStateEnvelope(payload);
  }

  async loadGame(): Promise<GameStateView> {
    return parseStateEnvelope(
      await this.#request("/api/game/load", { method: "POST" }),
    );
  }

  async wait(input: WaitInput): Promise<GameStateView> {
    const payload = await this.#request("/api/game/wait", {
      method: "POST",
      body: JSON.stringify(input),
    });
    return parseStateEnvelope(payload);
  }

  async seekWheel(input: SeekWheelInput): Promise<CultivationResponse> {
    return parseCultivationEnvelope(
      await this.#request("/api/game/cultivation/seek-wheel", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    );
  }

  async #request(path: string, init: RequestInit): Promise<unknown> {
    let response: Response;
    try {
      response = await this.#fetcher(path, {
        ...init,
        headers: {
          Accept: "application/json",
          ...(init.body === undefined
            ? {}
            : { "Content-Type": "application/json" }),
        },
      });
    } catch {
      throw new ApiClientError(
        "network_error",
        "无法连接到不羡仙后端。请确认后端正在运行。",
      );
    }

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      throw new ApiClientError(
        "invalid_response",
        "后端返回了无法解析的数据。",
      );
    }

    if (!response.ok) {
      const error = parseErrorEnvelope(payload);
      throw new ApiClientError(
        error.detail.code,
        error.detail.message,
        error.state,
      );
    }
    return payload;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isApiErrorCode(value: unknown): value is ApiErrorCode {
  return (
    typeof value === "string" &&
    [
      "invalid_request",
      "no_active_session",
      "save_not_found",
      "save_corrupt",
      "save_unsupported",
      "save_load_failed",
      "draft_not_found",
      "draft_creation_failed",
      "invalid_name",
      "invalid_aptitude_selection",
      "invalid_trait_selection",
      "save_overwrite_required",
      "revision_conflict",
      "time_command_rejected",
      "cultivation_command_rejected",
      "persistence_failed",
    ].includes(value)
  );
}

function parseAptitudes(value: unknown): Aptitudes {
  if (
    !isRecord(value) ||
    !isNumber(value.constitution) ||
    !isNumber(value.comprehension) ||
    !isNumber(value.spiritual_sense) ||
    !isNumber(value.temperament) ||
    !isNumber(value.fortune)
  ) {
    throw invalidResponse();
  }
  return {
    constitution: value.constitution,
    comprehension: value.comprehension,
    spiritual_sense: value.spiritual_sense,
    temperament: value.temperament,
    fortune: value.fortune,
  };
}

function parseTrait(value: unknown): TraitSummary {
  if (
    !isRecord(value) ||
    !isString(value.trait_id) ||
    !isString(value.name) ||
    !isString(value.description)
  ) {
    throw invalidResponse();
  }
  return {
    trait_id: value.trait_id,
    name: value.name,
    description: value.description,
  };
}

function parseGameState(value: unknown): GameStateView {
  if (
    !isRecord(value) ||
    !isNumber(value.revision) ||
    !isNumber(value.elapsed_days) ||
    !isRecord(value.player) ||
    !isString(value.player.name) ||
    !Array.isArray(value.player.traits)
  ) {
    throw invalidResponse();
  }
  return {
    revision: value.revision,
    elapsed_days: value.elapsed_days,
    player: {
      name: value.player.name,
      aptitudes: parseAptitudes(value.player.aptitudes),
      traits: value.player.traits.map(parseTrait),
    },
    cultivation: parseCultivationState(value.cultivation),
  };
}

function parseCultivationState(value: unknown): CultivationStateView {
  if (
    !isRecord(value) ||
    value.stage !== "seeking_wheel" ||
    !isNumber(value.wheel_insight) ||
    (value.wheel_status !== "seeking" &&
      value.wheel_status !== "suspected_sighting") ||
    !isNumber(value.suspected_sighting_threshold)
  ) {
    throw invalidResponse();
  }
  return {
    stage: value.stage,
    wheel_insight: value.wheel_insight,
    wheel_status: value.wheel_status,
    suspected_sighting_threshold: value.suspected_sighting_threshold,
  };
}

function parseApiErrorDetail(value: unknown): ApiErrorDetail {
  if (
    !isRecord(value) ||
    !isApiErrorCode(value.code) ||
    !isString(value.message)
  ) {
    throw invalidResponse();
  }
  return { code: value.code, message: value.message };
}

function parseGameStatus(value: unknown): GameStatus {
  if (
    !isRecord(value) ||
    typeof value.save_exists !== "boolean" ||
    typeof value.save_available !== "boolean" ||
    typeof value.session_active !== "boolean"
  ) {
    throw invalidResponse();
  }
  return {
    save_exists: value.save_exists,
    save_available: value.save_available,
    session_active: value.session_active,
    state: value.state === null ? null : parseGameState(value.state),
    error: value.error === null ? null : parseApiErrorDetail(value.error),
  };
}

function parseCharacterDraft(value: unknown): CharacterDraft {
  if (
    !isRecord(value) ||
    !isString(value.draft_id) ||
    !Array.isArray(value.aptitude_options) ||
    !Array.isArray(value.trait_options) ||
    !isNumber(value.required_trait_count)
  ) {
    throw invalidResponse();
  }
  return {
    draft_id: value.draft_id,
    aptitude_options: value.aptitude_options.map((option: unknown) => {
      if (!isRecord(option) || !isString(option.option_id)) {
        throw invalidResponse();
      }
      return {
        option_id: option.option_id,
        aptitudes: parseAptitudes(option.aptitudes),
      };
    }),
    trait_options: value.trait_options.map(parseTrait),
    required_trait_count: value.required_trait_count,
  };
}

function parseStateEnvelope(value: unknown): GameStateView {
  if (!isRecord(value)) {
    throw invalidResponse();
  }
  return parseGameState(value.state);
}

function parseCultivationEnvelope(value: unknown): CultivationResponse {
  if (!isRecord(value)) {
    throw invalidResponse();
  }
  return {
    state: parseGameState(value.state),
    cultivation_result: parseCultivationResult(value.cultivation_result),
  };
}

function parseCultivationResult(value: unknown): CultivationResultView {
  if (
    !isRecord(value) ||
    !isNumber(value.requested_max_days) ||
    !isNumber(value.actual_days_elapsed) ||
    !isNumber(value.previous_insight) ||
    !isNumber(value.current_insight) ||
    !isNumber(value.ordinary_insight_gained) ||
    !isNumber(value.inspiration_insight_gained) ||
    typeof value.reached_suspected_sighting !== "boolean" ||
    !isNumber(value.previous_elapsed_days) ||
    !isNumber(value.current_elapsed_days)
  ) {
    throw invalidResponse();
  }
  return {
    requested_max_days: value.requested_max_days,
    actual_days_elapsed: value.actual_days_elapsed,
    previous_insight: value.previous_insight,
    current_insight: value.current_insight,
    ordinary_insight_gained: value.ordinary_insight_gained,
    inspiration_insight_gained: value.inspiration_insight_gained,
    reached_suspected_sighting: value.reached_suspected_sighting,
    previous_elapsed_days: value.previous_elapsed_days,
    current_elapsed_days: value.current_elapsed_days,
  };
}

function parseErrorEnvelope(value: unknown): {
  readonly detail: ApiErrorDetail;
  readonly state: GameStateView | null;
} {
  if (!isRecord(value)) {
    throw invalidResponse();
  }
  return {
    detail: parseApiErrorDetail(value.error),
    state: value.state === null ? null : parseGameState(value.state),
  };
}

function invalidResponse(): ApiClientError {
  return new ApiClientError("invalid_response", "后端返回的数据合同无效。");
}
