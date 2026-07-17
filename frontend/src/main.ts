import "./style.css";

import { GameController, type AppState, type CreatingState } from "./app";
import { HttpGameApi, type Aptitudes, type GameStateView } from "./api/game";

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
      shell.append(renderOverview(state.game, state.busy, state.error, game));
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

function renderOverview(
  state: GameStateView,
  busy: boolean,
  error: string | null,
  game: GameController,
): HTMLElement {
  const panel = element("section", "panel panel--wide");
  panel.append(element("h2", "section-title", "游戏总览"));
  if (error !== null) {
    panel.append(renderError(error));
  }
  const summary = element("div", "summary-grid");
  summary.append(
    summaryCard("角色", state.player.name),
    summaryCard("累计游戏时间", `第 ${String(state.elapsed_days)} 天`),
    summaryCard("状态修订", String(state.revision)),
  );
  panel.append(summary);

  panel.append(element("h3", "subheading", "先天禀赋"));
  const aptitudeList = element("dl", "aptitudes");
  for (const [label, value] of aptitudeEntries(state.player.aptitudes)) {
    aptitudeList.append(
      element("dt", "", label),
      element("dd", "", String(value)),
    );
  }
  panel.append(aptitudeList);

  panel.append(element("h3", "subheading", "已选原型词条"));
  const traits = element("div", "choice-grid choice-grid--traits");
  for (const trait of state.player.traits) {
    const card = element("article", "choice-card choice-card--trait");
    card.append(
      element("strong", "choice-card__title", trait.name),
      element("span", "choice-card__description", trait.description),
    );
    traits.append(card);
  }
  panel.append(traits);

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
  waitInput.disabled = busy;
  const waitButton = button("等待", "button button--primary");
  waitButton.type = "submit";
  waitButton.disabled = busy;
  waitForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void game.wait(Number(waitInput.value));
  });
  waitForm.append(waitLabel, waitInput, waitButton);
  panel.append(waitForm);
  if (busy) {
    panel.append(element("p", "loading", "正在结算并保存…"));
  }
  return panel;
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
