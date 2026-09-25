import "./style.css";

import {
  GameController,
  type AppState,
  type CreatingState,
  type GamePage,
  type OverviewState,
} from "./app";
import { HttpGameApi, type Aptitudes, type ItemStackView } from "./api/game";

const root = document.querySelector<HTMLElement>("#app");
if (root === null) {
  throw new Error("缺少应用挂载节点。");
}

const controller = new GameController(new HttpGameApi());
controller.subscribe(() => {
  render(root, controller);
});
document.addEventListener("keydown", (event) => {
  // Escape is a game shortcut, but must never interrupt an active IME
  // composition (the browser marks IME key events with isComposing).
  if (event.key === "Escape" && !event.isComposing) {
    controller.toggleMenu();
  }
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
  panel.append(element("h2", "section-title", "主菜单"));
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
  const readButton = button("读取存档", "button button--secondary");
  readButton.disabled = state.busy || !state.saveAvailable;
  readButton.addEventListener("click", () => void game.continueGame());
  actions.append(readButton);
  const settingsButton = button("设置", "button button--secondary");
  settingsButton.disabled = state.busy;
  settingsButton.addEventListener("click", () => {
    const existing = panel.querySelector(".start-settings");
    if (existing !== null) {
      existing.remove();
      return;
    }
    panel.append(
      element(
        "div",
        "start-settings",
        "设置功能尚未开放。当前使用本地单存档和默认界面配置。",
      ),
    );
  });
  actions.append(settingsButton);
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
  let confirmButton: HTMLButtonElement | null = null;
  nameInput.addEventListener("input", () => {
    game.updateName(nameInput.value);
    panel.querySelector(".error")?.remove();
    if (confirmButton !== null) {
      confirmButton.disabled = !game.canConfirm();
    }
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
  confirmButton = confirm;
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
  panel.classList.add("game-panel");
  panel.append(renderGameStatusBar(state, game));
  const layout = element("div", "game-layout");
  layout.append(renderGameNavigation(state, game));
  const main = element("main", "game-main");
  if (state.page === "cultivation") {
    main.append(renderCultivation(state, game));
  } else if (state.page === "items") {
    main.append(renderItems(state, game));
  } else if (state.page === "overview") {
    main.append(renderOverview(state, game));
  } else {
    main.append(renderPlaceholder(state.page));
  }
  layout.append(main, renderCharacterInfo(state));
  panel.append(layout);
  panel.append(renderGameFeedback(state));
  if (state.menuOpen) {
    panel.append(renderGameMenu(state, game));
  }
  if (state.busy) {
    panel.append(element("p", "loading", "正在结算并保存…"));
  }
  return panel;
}

function renderGameStatusBar(
  state: OverviewState,
  game: GameController,
): HTMLElement {
  const bar = element("div", "game-statusbar");
  bar.append(
    statusChip("当前角色", state.game.player.name),
    statusChip("游戏时间", `第 ${String(state.game.elapsed_days)} 天`),
    statusChip("修订", String(state.game.revision)),
    statusChip(
      "修炼状态",
      state.game.cultivation.wheel_status === "suspected_sighting"
        ? "疑见"
        : "寻轮中",
    ),
  );
  const menuButton = button(
    "菜单 · Esc",
    "button button--secondary status-menu-button",
  );
  menuButton.addEventListener("click", () => {
    game.toggleMenu();
  });
  menuButton.disabled = state.busy;
  bar.append(menuButton);
  return bar;
}

function statusChip(label: string, value: string): HTMLElement {
  const chip = element("div", "status-chip");
  chip.append(
    element("span", "status-chip__label", label),
    element("strong", "status-chip__value", value),
  );
  return chip;
}

function renderCharacterInfo(state: OverviewState): HTMLElement {
  const aside = element("aside", "character-info");
  aside.append(
    element("p", "character-info__eyebrow", "人物信息"),
    element("h2", "character-info__name", state.game.player.name),
    element("p", "character-info__meta", "当前旅程 · 单存档"),
  );
  const aptitudeList = element("dl", "character-info__aptitudes");
  for (const [label, value] of aptitudeEntries(state.game.player.aptitudes)) {
    aptitudeList.append(
      element("dt", "", label),
      element("dd", "", String(value)),
    );
  }
  aside.append(
    element("h3", "character-info__heading", "先天禀赋"),
    aptitudeList,
    element("h3", "character-info__heading", "已选词条"),
  );
  const traits = element("ul", "character-info__traits");
  for (const trait of state.game.player.traits) {
    traits.append(element("li", "", trait.name));
  }
  aside.append(traits);
  return aside;
}

function renderGameNavigation(
  state: OverviewState,
  game: GameController,
): HTMLElement {
  const navigation = element("nav", "game-nav game-sidebar");
  navigation.setAttribute("aria-label", "游戏内页面");
  const entries: readonly [GamePage, string][] = [
    ["overview", "总览"],
    ["cultivation", "修炼"],
    ["items", "背包"],
    ["map", "地图"],
    ["quests", "任务"],
    ["log", "日志"],
  ];
  for (const [page, label] of entries) {
    const item = button(
      label,
      `game-nav__item${state.page === page ? " game-nav__item--active" : ""}`,
    );
    item.setAttribute("aria-current", state.page === page ? "page" : "false");
    item.disabled = state.busy;
    item.addEventListener("click", () => {
      game.showPage(page);
    });
    navigation.append(item);
  }
  return navigation;
}

function renderPlaceholder(
  page: Exclude<GamePage, "overview" | "cultivation" | "items">,
): DocumentFragment {
  const labels: Record<typeof page, [string, string]> = {
    map: ["地图", "地图功能尚未开放。后续将用于查看旅途与地点。"],
    quests: ["任务", "任务功能尚未开放。当前没有可接取任务。"],
    log: ["日志", "日志功能尚未开放。重要行动记录将在后续版本显示。"],
  };
  const [title, message] = labels[page];
  const content = document.createDocumentFragment();
  content.append(
    element("h2", "section-title", title),
    element("div", "placeholder-page", message),
  );
  return content;
}

function renderGameFeedback(state: OverviewState): HTMLElement {
  const feedback = element("div", "game-feedback");
  feedback.setAttribute("aria-live", "polite");
  if (state.error !== null) {
    feedback.append(renderError(state.error));
  } else if (state.menuMessage !== null) {
    feedback.append(element("p", "notice", state.menuMessage));
  } else {
    feedback.append(
      element("p", "game-feedback__hint", "所有行动都会在结算成功后自动保存。"),
    );
  }
  return feedback;
}

function renderGameMenu(
  state: OverviewState,
  game: GameController,
): HTMLElement {
  const backdrop = element("div", "game-menu-backdrop");
  const menu = element("section", "game-menu");
  menu.setAttribute("role", "dialog");
  menu.setAttribute("aria-modal", "true");
  menu.setAttribute("aria-label", "游戏菜单");
  menu.append(
    element("p", "eyebrow", "暂停菜单"),
    element("h2", "section-title", "游戏菜单"),
  );
  const actions = element("div", "game-menu__actions");
  const continueButton = button("继续游戏", "button button--primary");
  continueButton.addEventListener("click", () => {
    game.toggleMenu();
  });
  const saveButton = button("保存游戏", "button button--secondary");
  saveButton.addEventListener("click", () => {
    game.saveGame();
  });
  const settingsButton = button("设置", "button button--secondary");
  settingsButton.addEventListener("click", () => {
    game.toggleSettings();
  });
  const mainMenuButton = button("返回主菜单", "button button--secondary");
  mainMenuButton.addEventListener("click", () => {
    game.returnToMainMenu();
  });
  actions.append(continueButton, saveButton, settingsButton, mainMenuButton);
  menu.append(actions);
  if (state.menuMessage !== null) {
    menu.append(element("p", "notice", state.menuMessage));
  }
  backdrop.append(menu);
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop) {
      game.toggleMenu();
    }
  });
  return backdrop;
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

function renderItems(
  state: OverviewState,
  game: GameController,
): DocumentFragment {
  const content = document.createDocumentFragment();
  const storage = state.game.storage;
  content.append(
    element("h2", "section-title", "物品"),
    element(
      "p",
      "storage-capacity",
      `背包已使用 ${String(storage.backpack_used_slots)} / ${String(storage.backpack_capacity)} 个槽位`,
    ),
    element("h3", "subheading", "背包"),
    renderItemCollection(storage.backpack, "store", state, game),
    element("h3", "subheading", "仓库"),
    renderItemCollection(storage.warehouse, "retrieve", state, game),
    element(
      "p",
      "notice notice--subtle",
      "当前 pre-alpha 物品仅支持在背包与仓库间转移，尚不能使用、装备或丢弃。",
    ),
  );
  return content;
}

function renderItemCollection(
  items: readonly ItemStackView[],
  action: "store" | "retrieve",
  state: OverviewState,
  game: GameController,
): HTMLElement {
  const collection = element("div", "item-grid");
  if (items.length === 0) {
    collection.append(
      element(
        "p",
        "storage-empty",
        action === "store" ? "背包为空。" : "仓库为空。",
      ),
    );
    return collection;
  }
  for (const item of items) {
    const card = element("article", "item-card");
    const header = element("div", "item-card__header");
    header.append(
      element("strong", "item-card__name", item.name),
      element("span", "item-card__quantity", `× ${String(item.quantity)}`),
    );
    const category = element("span", "item-card__category", item.category);
    const description = element(
      "p",
      "item-card__description",
      item.description,
    );
    const form = element("form", "item-transfer");
    const inputId = `${action}-${item.item_id}`;
    const label = element("label", "field__label", "数量");
    label.htmlFor = inputId;
    const input = document.createElement("input");
    input.id = inputId;
    input.className = "input input--number";
    input.type = "number";
    input.min = "1";
    input.max = String(item.quantity);
    input.step = "1";
    input.value = "1";
    input.disabled = state.busy;
    const submit = button(
      action === "store" ? "存入仓库" : "取回背包",
      "button button--secondary",
    );
    submit.type = "submit";
    submit.disabled = state.busy;
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const quantity = Number(input.value);
      if (action === "store") {
        void game.storeItem(item.item_id, quantity);
      } else {
        void game.retrieveItem(item.item_id, quantity);
      }
    });
    form.append(label, input, submit);
    card.append(header, category, description, form);
    collection.append(card);
  }
  return collection;
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
