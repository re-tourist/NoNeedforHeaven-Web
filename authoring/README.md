# 作者内容工作区

Obsidian 可以作为作者的编辑工具，但不是“不羡仙”的运行时。游戏程序不会扫描完整的
Obsidian Vault，也不会直接读取私人笔记、草稿或插件状态。

## 目录边界

```text
authoring/
├─ published/documents/  明确发布、允许编译的只读文档 Markdown
├─ private/              私人材料；Git 忽略且编译器不扫描
└─ drafts/               未发布草稿；Git 忽略且编译器不扫描

runtime-content/         生成的运行时内容包；不属于作者源且 Git 忽略
backend/tests/content/   中性编译器测试夹具；不属于发布内容
```

只有显式传给编译器的 `authoring/published/documents/` 是正式输入。不要把私人笔记或未发布
草稿放入该目录。

## 最小只读文档

在 `authoring/published/documents/` 下创建 UTF-8 Markdown 文件：

```markdown
---
schema_version: 1
id: document.example
type: read_only_document
title: "示例文档"
---
# 示例

Markdown 正文。
```

- `id` 是长期引用标识，不从标题或文件名推导；必须以小写 ASCII 字母开头，由小写字母、
  数字以及分隔符 `.`, `_`, `-` 组成，最长 128 个字符。
- `title` 是玩家可见文本，可以使用中文，改变标题不应改变 `id`。
- 当前仅支持 `schema_version: 1` 和 `type: read_only_document`。
- Frontmatter 只支持这四个唯一标量字段、简单未加引号值或 JSON 风格双引号字符串。不支持
  数组、映射、注释、锚点、多行 YAML、单引号或任意可执行表达式。

## 验证和编译

以下命令从 `backend/` 目录执行：

```text
uv run python -m buxianxian.infrastructure.content validate
uv run python -m buxianxian.infrastructure.content compile
```

验证只检查源文件，不写输出。编译在所有源文件都通过后，以稳定 ID 顺序生成
`runtime-content/buxianxian-content.json`。可用 `--source` 和 `--output` 指定其他路径，例如
测试临时目录。编译结果不包含源路径、作者信息或 Obsidian 元数据。

当前管线不处理正式剧情、场景、人物、地点、任务、规则、图片、Wikilink、HTML、搜索、
本地化或内容与游戏状态的绑定。
