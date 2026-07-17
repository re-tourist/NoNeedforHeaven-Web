import { describe, expect, it } from "vitest";

import {
  GameController,
  type CreatingState,
  type OverviewState,
  type StartState,
} from "./app";
import {
  ApiClientError,
  type CharacterDraft,
  type ConfirmNewGameInput,
  type GameApi,
  type GameStateView,
  type GameStatus,
  type WaitInput,
} from "./api/game";

const INITIAL_GAME: GameStateView = {
  revision: 0,
  elapsed_days: 0,
  player: {
    name: "测试角色",
    aptitudes: {
      constitution: 5,
      comprehension: 5,
      spiritual_sense: 5,
      temperament: 5,
      fortune: 5,
    },
    traits: [
      {
        trait_id: "prototype.calm",
        name: "沉着",
        description: "中性测试说明。",
      },
      {
        trait_id: "prototype.steady",
        name: "稳健",
        description: "中性测试说明。",
      },
    ],
  },
};

const WAITED_GAME: GameStateView = {
  ...INITIAL_GAME,
  revision: 1,
  elapsed_days: 3,
};

function draft(id: string): CharacterDraft {
  const aptitudes = INITIAL_GAME.player.aptitudes;
  return {
    draft_id: id,
    aptitude_options: [
      { option_id: `${id}-option-1`, aptitudes },
      {
        option_id: `${id}-option-2`,
        aptitudes: { ...aptitudes, fortune: 6, temperament: 4 },
      },
      {
        option_id: `${id}-option-3`,
        aptitudes: { ...aptitudes, fortune: 4, temperament: 6 },
      },
    ],
    trait_options: Array.from({ length: 6 }, (_, index) => ({
      trait_id: `prototype.test_${String(index + 1)}`,
      name: `测试词条${String(index + 1)}`,
      description: "中性测试说明。",
    })),
    required_trait_count: 2,
  };
}

class FakeGameApi implements GameApi {
  status: GameStatus = {
    save_exists: false,
    save_available: false,
    session_active: false,
    state: null,
    error: null,
  };
  drafts: CharacterDraft[] = [draft("draft-1")];
  confirmResult: GameStateView = INITIAL_GAME;
  loadResult: GameStateView = INITIAL_GAME;
  waitResult: GameStateView = WAITED_GAME;
  statusError: Error | null = null;
  draftError: Error | null = null;
  confirmError: Error | null = null;
  loadError: Error | null = null;
  waitError: Error | null = null;
  confirmPromise: Promise<GameStateView> | null = null;
  confirmCalls = 0;
  waitCalls = 0;
  lastConfirmation: ConfirmNewGameInput | null = null;
  lastWait: WaitInput | null = null;

  getStatus(): Promise<GameStatus> {
    if (this.statusError !== null) {
      return Promise.reject(this.statusError);
    }
    return Promise.resolve(this.status);
  }

  createDraft(): Promise<CharacterDraft> {
    if (this.draftError !== null) {
      return Promise.reject(this.draftError);
    }
    const next = this.drafts.shift();
    if (next === undefined) {
      return Promise.reject(new Error("缺少测试草稿。"));
    }
    return Promise.resolve(next);
  }

  async confirmNewGame(input: ConfirmNewGameInput): Promise<GameStateView> {
    this.confirmCalls += 1;
    this.lastConfirmation = input;
    if (this.confirmError !== null) {
      throw this.confirmError;
    }
    return this.confirmPromise ?? this.confirmResult;
  }

  loadGame(): Promise<GameStateView> {
    if (this.loadError !== null) {
      return Promise.reject(this.loadError);
    }
    return Promise.resolve(this.loadResult);
  }

  wait(input: WaitInput): Promise<GameStateView> {
    this.waitCalls += 1;
    this.lastWait = input;
    if (this.waitError !== null) {
      return Promise.reject(this.waitError);
    }
    return Promise.resolve(this.waitResult);
  }
}

class Deferred<Value> {
  readonly promise: Promise<Value>;
  #resolver: ((value: Value) => void) | null = null;

  constructor() {
    this.promise = new Promise((resolve) => {
      this.#resolver = resolve;
    });
  }

  resolve(value: Value): void {
    const resolver = this.#resolver;
    if (resolver === null) {
      throw new Error("测试 Promise 尚未初始化。");
    }
    resolver(value);
  }
}

async function creatingController(
  api: FakeGameApi,
  options: { readonly saveExists?: boolean } = {},
): Promise<GameController> {
  const saveExists = options.saveExists ?? false;
  api.status = {
    ...api.status,
    save_exists: saveExists,
    save_available: saveExists,
  };
  const controller = new GameController(api);
  await controller.initialize();
  await controller.startNewGame();
  return controller;
}

function startState(controller: GameController): StartState {
  const state = controller.state;
  if (state.kind !== "start") {
    throw new Error("预期开始状态。 ");
  }
  return state;
}

function creatingState(controller: GameController): CreatingState {
  const state = controller.state;
  if (state.kind !== "creating") {
    throw new Error("预期角色创建状态。 ");
  }
  return state;
}

function overviewState(controller: GameController): OverviewState {
  const state = controller.state;
  if (state.kind !== "overview") {
    throw new Error("预期游戏总览状态。 ");
  }
  return state;
}

function fillRequiredSelections(controller: GameController): void {
  const state = creatingState(controller);
  controller.updateName("测试角色");
  controller.selectAptitude(
    requiredAt(state.draft.aptitude_options, 0).option_id,
  );
  controller.toggleTrait(requiredAt(state.draft.trait_options, 0).trait_id);
  controller.toggleTrait(requiredAt(state.draft.trait_options, 1).trait_id);
}

function requiredAt<Value>(values: readonly Value[], index: number): Value {
  const value = values[index];
  if (value === undefined) {
    throw new Error(`缺少索引 ${String(index)} 的测试数据。`);
  }
  return value;
}

describe("GameController", () => {
  it("shows a start state without Continue when no save exists", async () => {
    const controller = new GameController(new FakeGameApi());

    await controller.initialize();

    const state = startState(controller);
    expect(state.saveExists).toBe(false);
    expect(state.saveAvailable).toBe(false);
    expect(state.busy).toBe(false);
  });

  it("loads an available save into the overview", async () => {
    const api = new FakeGameApi();
    api.status = {
      ...api.status,
      save_exists: true,
      save_available: true,
    };
    const controller = new GameController(api);
    await controller.initialize();

    await controller.continueGame();

    expect(overviewState(controller).game).toEqual(INITIAL_GAME);
  });

  it("requires a name, aptitude, and exactly two traits", async () => {
    const api = new FakeGameApi();
    const controller = await creatingController(api);
    const state = creatingState(controller);

    expect(controller.canConfirm()).toBe(false);
    controller.updateName("测试角色");
    controller.selectAptitude(
      requiredAt(state.draft.aptitude_options, 0).option_id,
    );
    controller.toggleTrait(requiredAt(state.draft.trait_options, 0).trait_id);
    expect(controller.canConfirm()).toBe(false);
    controller.toggleTrait(requiredAt(state.draft.trait_options, 1).trait_id);
    expect(controller.canConfirm()).toBe(true);
    controller.toggleTrait(requiredAt(state.draft.trait_options, 2).trait_id);
    expect(creatingState(controller).traitIds).toHaveLength(2);
  });

  it("requires explicit overwrite consent when any save exists", async () => {
    const api = new FakeGameApi();
    const controller = await creatingController(api, { saveExists: true });
    fillRequiredSelections(controller);

    expect(controller.canConfirm()).toBe(false);
    controller.setOverwriteConfirmed(true);
    expect(controller.canConfirm()).toBe(true);
  });

  it("regeneration replaces candidates and clears prior selections", async () => {
    const api = new FakeGameApi();
    api.drafts = [draft("draft-1"), draft("draft-2")];
    const controller = await creatingController(api);
    fillRequiredSelections(controller);

    await controller.regenerateDraft();

    const state = creatingState(controller);
    expect(state.draft.draft_id).toBe("draft-2");
    expect(state.name).toBe("测试角色");
    expect(state.aptitudeOptionId).toBeNull();
    expect(state.traitIds).toEqual([]);
  });

  it("submits current server IDs and enters overview after creation", async () => {
    const api = new FakeGameApi();
    const controller = await creatingController(api);
    fillRequiredSelections(controller);
    const selected = creatingState(controller);

    await controller.confirmNewGame();

    expect(overviewState(controller).game).toEqual(INITIAL_GAME);
    expect(api.lastConfirmation).toEqual({
      draft_id: selected.draft.draft_id,
      name: "测试角色",
      aptitude_option_id: selected.aptitudeOptionId,
      trait_ids: selected.traitIds,
      overwrite_existing_save: false,
    });
  });

  it("refreshes time and revision only from a successful wait response", async () => {
    const api = new FakeGameApi();
    api.status = {
      ...api.status,
      session_active: true,
      state: INITIAL_GAME,
    };
    const controller = new GameController(api);
    await controller.initialize();

    await controller.wait(3);

    expect(overviewState(controller).game).toEqual(WAITED_GAME);
    expect(api.lastWait).toEqual({ days: 3, expected_revision: 0 });
  });

  it("shows backend errors without leaving the recoverable current page", async () => {
    const api = new FakeGameApi();
    api.draftError = new ApiClientError(
      "persistence_failed",
      "候选暂时不可用。 ",
    );
    const controller = new GameController(api);
    await controller.initialize();

    await controller.startNewGame();

    const state = startState(controller);
    expect(state.error).toBe("候选暂时不可用。 ");
    expect(state.busy).toBe(false);
  });

  it("prevents duplicate confirmation while one request is pending", async () => {
    const api = new FakeGameApi();
    const confirmation = new Deferred<GameStateView>();
    api.confirmPromise = confirmation.promise;
    const controller = await creatingController(api);
    fillRequiredSelections(controller);

    const first = controller.confirmNewGame();
    const second = controller.confirmNewGame();

    expect(api.confirmCalls).toBe(1);
    expect(creatingState(controller).busy).toBe(true);
    confirmation.resolve(INITIAL_GAME);
    await Promise.all([first, second]);
    expect(overviewState(controller).busy).toBe(false);
  });

  it("adopts server state on revision conflict without blind retry", async () => {
    const api = new FakeGameApi();
    api.status = {
      ...api.status,
      session_active: true,
      state: INITIAL_GAME,
    };
    api.waitError = new ApiClientError(
      "revision_conflict",
      "状态已刷新。 ",
      WAITED_GAME,
    );
    const controller = new GameController(api);
    await controller.initialize();

    await controller.wait(2);

    const state = overviewState(controller);
    expect(state.game).toEqual(WAITED_GAME);
    expect(state.error).toBe("状态已刷新。 ");
    expect(api.waitCalls).toBe(1);
  });
});
