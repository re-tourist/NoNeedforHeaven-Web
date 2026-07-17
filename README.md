# 不羡仙（Buxianxian）

“不羡仙”是一款计划长期开发的独立本地文字游戏。当前仓库已完成**工程基线、确定性领域内核、版本化存档、事务会话、只读内容编译、权威游戏时间、角色创建、第一条 Web 闭环，以及“寻轮”修炼垂直切片**。玩家可以创建并保存角色、重新加载存档、查看状态、等待或按日寻轮，并积累体悟直至“疑见生命之轮”。见轮三验、物品、地图和叙事仍未实现。

## 架构边界

- Python 后端是未来游戏状态和规则的唯一权威。
- Web 前端只负责展示、用户交互和与后端通信，不复制权威规则。
- Obsidian 仅是作者工作环境，不是运行时依赖。
- 作者源文件、未来的编译后内容、存档、展示模型和日志属于不同数据类别。

当前浏览器通过 FastAPI 调用现有应用服务。服务器持有唯一活动会话和服务端角色草稿；前端只提交姓名、候选 ID、命令参数和预期 revision，并使用服务器返回的完整状态刷新界面。正式 `GameState` 包含 revision、累计天数、完整玩家资料和寻轮状态；新游戏、等待或寻轮转换只有在状态与 RNG 一并保存成功后才更新活动会话。

TASK-004 另建立了独立的作者工具链：仅从仓库内 `authoring/published/documents/`
读取受限 Frontmatter Markdown，验证后确定性地生成版本化 `buxianxian-content` JSON 包。
它不接入领域状态、存档、API 或前端，也不扫描私人 Obsidian Vault。

## 环境要求

- [uv](https://docs.astral.sh/uv/) 0.11.28 或兼容的新版本；
- Python 3.14（`uv` 可按 `backend/.python-version` 自动安装）；
- Node.js 24 LTS；
- npm 11（随 Node.js 24 提供）。

Windows、macOS 和 Linux 使用相同的项目命令。命令示例从仓库根目录开始；PowerShell、Command Prompt、bash 和 zsh 均可分别进入所示目录执行。

## 首次安装

安装后端的锁定依赖：

```text
cd backend
uv sync --locked
```

另开一个终端安装前端的锁定依赖：

```text
cd frontend
npm ci
```

`uv sync --locked` 会创建隔离的 `backend/.venv`，`npm ci` 会依据 `package-lock.json` 进行干净安装。两条命令都不会依赖系统级 Python 包或全局前端包。

## 本地开发

终端一启动后端：

```text
cd backend
uv run uvicorn buxianxian.api.app:app --reload --host 127.0.0.1 --port 8000
```

可访问 `http://127.0.0.1:8000/api/health` 验证接口。

默认单存档位于仓库根目录的 `runtime-data/buxianxian.save.json`，该目录已被 Git 忽略。
可在启动后端前设置 `BUXIANXIAN_SAVE_PATH` 覆盖路径，例如 PowerShell：

```text
$env:BUXIANXIAN_SAVE_PATH = "D:\games\buxianxian\save.json"
uv run uvicorn buxianxian.api.app:app --reload --host 127.0.0.1 --port 8000
```

或 bash/zsh：

```text
BUXIANXIAN_SAVE_PATH="$HOME/.local/share/buxianxian/save.json" \
  uv run uvicorn buxianxian.api.app:app --reload --host 127.0.0.1 --port 8000
```

终端二启动前端：

```text
cd frontend
npm run dev
```

打开 Vite 输出的本地地址。开发服务器会把同源 `/api` 请求代理到 `http://127.0.0.1:8000`；代码中没有硬编码生产 API 地址，也不需要启用跨域访问。

页面支持开始新游戏、服务端角色草稿、明确覆盖确认、继续游戏、状态总览、等待操作，
以及“修炼”页中的 1/7/30 天寻轮。寻轮达到疑见后会停用继续操作并明确提示见轮三验
尚未实现。
后端未启动、网络请求失败或响应合同无效时，页面保留当前可恢复状态并显示错误。
角色草稿仅保存在后端内存中，后端重启后需要重新生成。

完整 API 合同见 `docs/api.md`，前端结构见 `frontend/README.md`。

## 自动验证

后端：

```text
cd backend
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
uv run python -m buxianxian.infrastructure.content validate
```

前端：

```text
cd frontend
npm ci
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
```

需要自动修复格式时，分别运行 `uv run ruff format .` 和 `npm run format`。GitHub Actions 在 Ubuntu、Python 3.14 和 Node.js 24 上执行相同的必要检查。

## 只读文档内容

发布源、格式边界和最小示例见 `authoring/README.md`。从 `backend/` 验证或编译：

```text
uv run python -m buxianxian.infrastructure.content validate
uv run python -m buxianxian.infrastructure.content compile
```

默认输出为 `runtime-content/buxianxian-content.json`，它是可重复生成的本地构建产物，
不会提交到 Git。当前仓库不包含正式游戏文档。

## 项目导航

新贡献者应依次阅读：

1. `AGENTS.md`
2. `docs/project-status.md`
3. 当前 `docs/tasks/` 任务
4. `docs/architecture/overview.md`
5. 任务引用的 ADR 与质量要求

主要目录：

```text
backend/    Python 运行时工程
frontend/   原生 TypeScript 浏览器工程
authoring/  作者源边界与明确发布的只读文档目录（不参与运行）
docs/       产品、架构、ADR、路线图、任务与执行计划
```

## 名称规范

- 中文产品名：`不羡仙`
- 稳定代码标识：`buxianxian`
- 工程仓库名：`NoNeedforHeaven-Web`
- Python 包名：`buxianxian`
- 存档格式标识：`buxianxian-save`
- 运行时内容格式标识：`buxianxian-content`
- 环境变量前缀：`BUXIANXIAN_`

“文明online”不得作为产品名、代码名、存档名或界面文案进入仓库。
