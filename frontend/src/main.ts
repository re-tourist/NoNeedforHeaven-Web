import "./style.css";

import { fetchHealth } from "./api/health";

const root = document.querySelector<HTMLElement>("#app");

if (root === null) {
  throw new Error("缺少应用挂载节点。");
}

const title = document.createElement("h1");
title.textContent = "不羡仙";

const description = document.createElement("p");
description.className = "description";
description.textContent = "工程环境连通性检查";

const status = document.createElement("p");
status.className = "status status--loading";
status.setAttribute("role", "status");
status.setAttribute("aria-live", "polite");
status.textContent = "正在连接后端…";

root.append(title, description, status);

try {
  const health = await fetchHealth();
  status.className = "status status--connected";
  status.textContent = `已连接到后端：${health.app_name}（${health.version}）`;
} catch (error: unknown) {
  const message = error instanceof Error ? error.message : "发生未知连接错误。";
  status.className = "status status--error";
  status.textContent = `后端不可用：${message}`;
}
