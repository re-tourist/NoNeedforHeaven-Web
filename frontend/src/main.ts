import "./style.css";

import {
  GameController,
  type AppState,
  type CreatingState,
  type OverviewState,
} from "./app";
import { HttpGameApi, type Aptitudes } from "./api/game";

const root = document.querySelector<HTMLElement>("#app");
if (root === null) {
  throw new Error("缺少应用挂载节点。");
}

const controller = new GameController(new HttpGameApi());
controller.subscribe(() => {
  render(root, controller);
});
render(root, controller);
await controller.initialize();

function render(container: HTMLElement, game: GameController): void {
  const shell = element("div", "app-shell");
  shell.append(renderHeader());
  const state = game.state;
  switch (state.kind) {
    case "booting":
      shell.append(renderLoading(state.message));
      break;
    case "start":
      shell.append(renderStart(state, game));
      break;
    case "creating":
      shell.append(renderCreation(state, game));
      break;
    case "overview":
      shell.append(renderGame(state, game));
      break;
  }
  container.replaceChildren(shell);
}

function renderHeader(): HTMLElement {
  const header = element("header", "brand");
  header.append(
    element("p", "eyebrow", "本地单机文字游戏 · 工程原型"),
    element("h1", "brand__title", "不羡仙"),
    element(
      "p",
      "brand__subtitle",
      "选择你的开局倾向，开启第一段可保存的旅程。",
    ),
  );
  return header;
}

function renderLoading(message: string): HTMLElement {
  const panel = element("section", "panel panel--center");
  panel.setAttribute("aria-busy", "true");
  panel.append(element("p", "loading", message));
  return panel;
}

function renderStart(
  state: Extract<AppState, { kind: "start" }>,
  game: GameController,
): HTMLElement {
  const panel = element("section", "panel");
  panel.append(element("h2", "section-title", "开始"));
  if (state.error !== null) {
    panel.append(renderError(state.error));
  }
  const actions = element("div", "actions");
  const newGame = button("开始新游戏", "button button--primary");
  newGame.disabled = state.busy;
  newGame.addEventListener("click", () => void game.startNewGame());
  actions.append(newGame);
  if (state.saveAvailable) {
    const continueButton = button("继续游戏", "button button--secondary");
    continueButton.disabled = state.busy;
    continueButton.addEventListener("click", () => void game.continueGame());
    actions.append(continueButton);
  }
  if (state.saveExists && !state.saveAvailable) {
    panel.append(
      element(
        "p",
        "notice",
        "检测到无法加载的本地存档。开始新游戏时仍需明确确认覆盖。",
      ),
    );
  }
  panel.append(actions);
  if (state.busy) {
    panel.append(element("p", "loading", "正在准备…"));
  }
  return panel;
}

function renderCreation(
  state: CreatingState,
  game: GameController,
): HTMLElement {
  const panel = element("section", "panel panel--wide");
  panel.append(element("h2", "section-title", "创建角色"));
  if (state.error !== null) {
    panel.append(renderError(state.error));
  }

  const nameGroup = element("div", "field");
  const nameLabel = element("label", "field__label", "角色姓名");
  nameLabel.htmlFor = "character-name";
  const nameInput = document.createElement("input");
  nameInput.id = "character-name";
  nameInput.className = "input";
  nameInput.type = "text";
  nameInput.maxLength = 32;
  nameInput.autocomplete = "off";
  nameInput.value = state.name;
  nameInput.disabled = state.busy;
  nameInput.addEventListener("input", () => {
    game.updateName(nameInput.value);
  });
  nameGroup.append(nameLabel, nameInput);
  panel.append(nameGroup);

  panel.append(element("h3", "subheading", "选择一套先天禀赋"));
  const aptitudeGrid = element("div", "choice-grid choice-grid--aptitudes");
  for (const option of state.draft.aptitude_options) {
    const selected = state.aptitudeOptionId === option.option_id;
    const choice = button(
      aptitudeSummary(option.aptitudes),
      `choice-card${selected ? " choice-card--selected" : ""}`,
    );
    choice.setAttribute("aria-pressed", String(selected));
    choice.disabled = state.busy;
    choice.addEventListener("click", () => {
      game.selectAptitude(option.option_id);
    });
    aptitudeGrid.append(choice);
  }
  panel.append(aptitudeGrid);

  panel.append(
    element(
      "h3",
      "subheading",
      `选择两个原型词条（已选 ${String(state.traitIds.length)}/${String(state.draft.required_trait_count)}）`,
    ),
  );
  const traitGrid = element("div", "choice-grid choice-grid--traits");
  for (const trait of state.draft.trait_options) {
    const selected = state.traitIds.includes(trait.trait_id);
    const unavailable =
      !selected && state.traitIds.length >= state.draft.required_trait_count;
    const choice = button(
      "",
      `choice-card choice-card--trait${selected ? " choice-card--selected" : ""}`,
    );
    choice.append(
      element("strong", "choice-card__title", trait.name),
      element("span", "choice-card__description", trait.description),
    );
    choice.setAttribute("aria-pressed", String(selected));
    choice.disabled = state.busy || unavailable;
    choice.addEventListener("click", () => {
      game.toggleTrait(trait.trait_id);
    });
    traitGrid.append(choice);
  }
  panel.append(traitGrid);

  if (state.saveExists) {
    const overwrite = element("label", "overwrite");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = state.overwriteConfirmed;
    checkbox.disabled = state.busy;
    checkbox.addEventListener("change", () => {
      game.setOverwriteConfirmed(checkbox.checked);
    });
    overwrite.append(
      checkbox,
      element("span", "", "我确认覆盖现有单存档。此操作不可撤销。"),
    );
    panel.append(overwrite);
  }

  const actions = element("div", "actions");
  const regenerate = button("重新生成候选", "button button--secondary");
  regenerate.disabled = state.busy;
  regenerate.addEventListener("click", () => void game.regenerateDraft());
  const confirm = button("确认创建并保存", "button button--primary");
  confirm.disabled = !game.canConfirm();
  confirm.addEventListener("click", () => void game.confirmNewGame());
  actions.append(regenerate, confirm);
  panel.append(actions);
  if (state.busy) {
    panel.append(element("p", "loading", "正在提交，请勿重复操作…"));
  }
  return panel;
}

function renderGame(state: OverviewState, game: GameController): HTMLElement {
  const panel = element("section", "panel panel--wide");
  panel.append(renderGameNavigation(state, game));
  if (state.error !== null) {
    panel.append(renderError(state.error));
  }
  if (state.page === "cultivation") {
    panel.append(renderCultivation(state, game));
  } else {
    panel.append(renderOverview(state, game));
  }
  if (state.busy) {
    panel.append(element("p", "loading", "正在结算并保存…"));
  }
  return panel;
}

function renderGameNavigation(
  state: OverviewState,
  game: GameController,
): HTMLElement {
  const navigation = element("nav", "game-nav");
  navigation.setAttribute("aria-label", "游戏内页面");
  const overview = button(
    "总览",
    `game-nav__item${state.page === "overview" ? " game-nav__item--active" : ""}`,
  );
  overview.setAttribute(
    "aria-current",
    state.page === "overview" ? "page" : "false",
  );
  overview.disabled = state.busy;
  overview.addEventListener("click", () => {
    game.showOverview();
  });
  const cultivation = button(
    "修炼",
    `game-nav__item${state.page === "cultivation" ? " game-nav__item--active" : ""}`,
  );
  cultivation.setAttribute(
    "aria-current",
    state.page === "cultivation" ? "page" : "false",
  );
  cultivation.disabled = state.busy;
  cultivation.addEventListener("click", () => {
    game.showCultivation();
  });
  navigation.append(overview, cultivation);
  return navigation;
}

function renderOverview(
  state: OverviewState,
  game: GameController,
): DocumentFragment {
  const content = document.createDocumentFragment();
  const gameState = state.game;
  content.append(element("h2", "section-title", "游戏总览"));
  const summary = element("div", "summary-grid");
  summary.append(
    summaryCard("角色", gameState.player.name),
    summaryCard("累计游戏时间", `第 ${String(gameState.elapsed_days)} 天`),
    summaryCard("状态修订", String(gameState.revision)),
  );
  content.append(summary);

  content.append(element("h3", "subheading", "先天禀赋"));
  const aptitudeList = element("dl", "aptitudes");
  for (const [label, value] of aptitudeEntries(gameState.player.aptitudes)) {
    aptitudeList.append(
      element("dt", "", label),
      element("dd", "", String(value)),
    );
  }
  content.append(aptitudeList);

  content.append(element("h3", "subheading", "已选原型词条"));
  const traits = element("div", "choice-grid choice-grid--traits");
  for (const trait of gameState.player.traits) {
    const card = element("article", "choice-card choice-card--trait");
    card.append(
      element("strong", "choice-card__title", trait.name),
      element("span", "choice-card__description", trait.description),
    );
    traits.append(card);
  }
  content.append(
    traits,
    element(
      "p",
      "notice notice--subtle",
      "词条效果尚未接入当前 pre-alpha 修炼规则。",
    ),
  );

  const waitForm = element("form", "wait-form");
  const waitLabel = element("label", "field__label", "等待天数");
  waitLabel.htmlFor = "wait-days";
  const waitInput = document.createElement("input");
  waitInput.id = "wait-days";
  waitInput.className = "input input--number";
  waitInput.type = "number";
  waitInput.min = "1";
  waitInput.step = "1";
  waitInput.value = "1";
  waitInput.disabled = state.busy;
  const waitButton = button("等待", "button button--primary");
  waitButton.type = "submit";
  waitButton.disabled = state.busy;
  waitForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void game.wait(Number(waitInput.value));
  });
  waitForm.append(waitLabel, waitInput, waitButton);
  content.append(waitForm);
  return content;
}

function renderCultivation(
  state: OverviewState,
  game: GameController,
): DocumentFragment {
  const content = document.createDocumentFragment();
  const cultivation = state.game.cultivation;
  const suspected = cultivation.wheel_status === "suspected_sighting";
  content.append(
    element("h2", "section-title", "修炼"),
    element("p", "cultivation-method", "当前功法：先天秘境大道（残卷）"),
  );

  const summary = element("div", "summary-grid");
  summary.append(
    summaryCard("当前阶段", "寻轮"),
    summaryCard("当前状态", suspected ? "疑见生命之轮" : "寻轮中"),
    summaryCard(
      "寻轮体悟",
      `${String(cultivation.wheel_insight)} / ${String(cultivation.suspected_sighting_threshold)}`,
    ),
    summaryCard("累计游戏时间", `第 ${String(state.game.elapsed_days)} 天`),
    summaryCard("状态修订", String(state.game.revision)),
  );
  content.append(summary);

  const progressLabel = element(
    "label",
    "progress-label",
    `寻轮体悟 ${String(cultivation.wheel_insight)} / ${String(cultivation.suspected_sighting_threshold)}`,
  );
  progressLabel.htmlFor = "wheel-insight-progress";
  const progress = document.createElement("progress");
  progress.id = "wheel-insight-progress";
  progress.className = "cultivation-progress";
  progress.max = cultivation.suspected_sighting_threshold;
  progress.value = cultivation.wheel_insight;
  content.append(progressLabel, progress);

  if (suspected) {
    content.append(
      element(
        "p",
        "notice cultivation-next-step",
        "你已疑见生命之轮。后续需要完成“见轮三验”；该阶段尚未实现。",
      ),
    );
  } else {
    content.append(
      element(
        "p",
        "cultivation-copy",
        "守静、调息、内照，按日积累体悟。达到疑见时会提前结束本次闭关。",
      ),
    );
  }

  const actions = element("div", "cultivation-actions");
  for (const days of [1, 7, 30] as const) {
    const action = button(`寻轮 ${String(days)} 天`, "button button--primary");
    action.disabled = !game.canSeekWheel();
    action.addEventListener("click", () => void game.seekWheel(days));
    actions.append(action);
  }
  content.append(actions);

  if (state.lastCultivation !== null) {
    const result = state.lastCultivation;
    const resultPanel = element("section", "cultivation-result");
    resultPanel.append(
      element("h3", "subheading cultivation-result__title", "最近一次修炼"),
      element(
        "p",
        "",
        `请求 ${String(result.requested_max_days)} 天，实际经过 ${String(result.actual_days_elapsed)} 天。`,
      ),
      element(
        "p",
        "",
        `体悟 ${String(result.previous_insight)} → ${String(result.current_insight)}；普通体悟 +${String(result.ordinary_insight_gained)}，偶发灵光 +${String(result.inspiration_insight_gained)}。`,
      ),
    );
    if (result.reached_suspected_sighting) {
      resultPanel.append(
        element("p", "cultivation-result__milestone", "本次修炼达到疑见。"),
      );
    }
    content.append(resultPanel);
  }
  content.append(
    element(
      "p",
      "notice notice--subtle",
      "原型词条效果尚未接入当前 pre-alpha 修炼规则。",
    ),
  );
  return content;
}

function renderError(message: string): HTMLElement {
  const error = element("p", "error", message);
  error.setAttribute("role", "alert");
  return error;
}

function summaryCard(label: string, value: string): HTMLElement {
  const card = element("div", "summary-card");
  card.append(
    element("span", "summary-card__label", label),
    element("strong", "summary-card__value", value),
  );
  return card;
}

function aptitudeSummary(aptitudes: Aptitudes): string {
  return aptitudeEntries(aptitudes)
    .map(([label, value]) => `${label} ${String(value)}`)
    .join(" · ");
}

function aptitudeEntries(
  aptitudes: Aptitudes,
): readonly (readonly [string, number])[] {
  return [
    ["根骨", aptitudes.constitution],
    ["悟性", aptitudes.comprehension],
    ["神识", aptitudes.spiritual_sense],
    ["心性", aptitudes.temperament],
    ["气运", aptitudes.fortune],
  ];
}

function button(text: string, className: string): HTMLButtonElement {
  const result = document.createElement("button");
  result.type = "button";
  result.className = className;
  result.textContent = text;
  return result;
}

function element<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const result = document.createElement(tag);
  if (className) {
    result.className = className;
  }
  if (text !== undefined) {
    result.textContent = text;
  }
  return result;
}
