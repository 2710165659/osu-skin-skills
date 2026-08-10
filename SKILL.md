---
name: osu-skin-skills
description: >-
  此技能用于处理 osu! stable 和 osu! lazer 皮肤，包括查询和解释皮肤元素与配置、诊断资源不生效
  和默认回退、编辑 skin.ini 与 lazer 布局 JSON、处理 PNG 动画和音效、迁移或混合不同模式与
  Mania 键数，以及制作投皮、轻量化皮肤和打包 .osk。凡用户需要分析、修改、排查或组合 osu!
  皮肤，尤其涉及 stable/lazer 差异、HUD/Playfield 布局、hitsound、长按素材或 keycount 时，
  都应使用此技能。
---

# 执行入口

把本文件作为任务路由和安全边界；领域细节按下表读取。每次触发按以下顺序执行：

1. 读取 `references/start-here.md`，按意图选择最少的 reference。
2. 确认输入类型、皮肤根目录、客户端、模式/keycount、源/目标路径和覆盖策略。
3. 运行入口 reference 指定的只读检查；首次使用或数据库异常时先运行 `osu-skin selfcheck --json`。
4. 读取数据库和真实文件建立证据，再给计划；不要用文件名、目录名或模型记忆推断未确认的消费者。
5. 写入前列出文件、字段、路径和回退影响；写后复查并报告未确认项。

## 硬性闸门

- 没有 `skininfo.json` 且用户没有说明 stable/lazer：先询问客户端；在回答前只做与客户端无关的检查。
- Mania 没有 `Keys: N`：先询问 keycount；不能默认 4K 或第一个 `[Mania]` 段。
- 混皮没有模式/资源组/输出范围：先询问范围；不能整目录覆盖或把某来源自动当全局基础皮肤。
- 用户说“投/投皮/投的长度”：读取 `references/mania-hold-body.md`，不要按普通长度字段解释。
- 要删除、原地覆盖或安装到游戏目录：先确认精确目标和备份/新目录策略。
- 没有实际皮肤文件时，不能断言实际 path、SD/`@2x`、动画帧、alpha、fallback、NoteBodyStyle 或显示尺寸。

## Reference 路由

| 意图 | 权威 reference |
|---|---|
| 请求入口、客户端/输入/最小提问 | `references/start-here.md` |
| 元素、文件名、资源组 | `references/element-map.md` |
| 数据库 schema、客户端口径、混皮 SQL | `references/database.md` |
| 混皮、资源组、lite、`.osk` | `references/merge-recipes.md` |
| skin.ini 字段 | `references/field-glossary.md` |
| stable/lazer 差异和迁移 | `references/stable-vs-lazer.md` |
| lazer 生成的布局 JSON 编辑 | `references/lazer-layout-json.md` |
| Mania 键位、路径、几何、合并 | `references/mania.md` |
| 投皮和投的长度 | `references/mania-hold-body.md` |
| lazer 非等比缩放 | `references/lazer-image-scaling.md` |
| 图片、alpha、@2x、动画 | `references/image-animation.md` |
| 音频和 hitsound | `references/audio.md` |
| 工具用途、参数和选择 | `references/tools.md` |
| 故障诊断 | `references/troubleshooting.md` |
| 证据和来源记录 | `references/research-evidence.md` |

生成或导出 `.osk` 时，读取 `references/merge-recipes.md` 的“lazer 皮肤名称与 `.osk` 输出名”规则。输出基名默认由 `[General] Name` 和 `Author` 组成的 `Name (Author)` 经过 lazer 文件名清理后得到；不要只使用目录名、源压缩包名或 `skininfo.json` 推导名称。

同一规则只以对应 reference 为准；其他 reference 只引用它，不重新复制完整流程。跨域任务按“入口 → 领域 reference → 数据库/真实文件”顺序读取。

## 数据库查询协议

`assets/osu_skin.db` 是事实源，包含元素表和 lazer 生成 JSON 事实表。普通查询：

```powershell
osu-skin db-query "<元素、文件名、命令或描述>" --client <stable|lazer|both> --json
```

查询 lazer 布局 JSON 的文件、字段、完整 `Type` 或 `Settings`：

```powershell
osu-skin db-query "<文件、字段、Type 或设置>" --client lazer --type lazer_json --json
```

`references/lazer-layout-json.md` 只描述编辑流程和运行时行为；具体 JSON 事实必须以 `lazer_json_entries` 查询结果为准。

普通搜索 JSON 结果中，元素记录在 `results`，lazer JSON 事实记录在 `lazer_json_results`；元素专属详情、标签及标签定义仍在元素记录中，术语匹配在 `term_matches`。查询文件族前去掉目录、扩展名、`@2x` 和动画帧后缀，但候选不唯一时保留全部结果。

复杂联表直接执行只读 SQL：

```powershell
osu-skin db-query --sql "SELECT ..." --json
osu-skin db-query --sql-file .\consumer-matrix.sql --json
```

`--sql`/`--sql-file` 只接受 `SELECT`、`WITH`、`EXPLAIN`、`PRAGMA`，结果列原样返回。混皮必须使用 `references/database.md` 中的完整元素、共享资源、配置消费者和 Mania keycount 查询，不得只依据 `client` 或单个标签。

## 证据和写入

- 区分“数据库/文件直接证明”“客户端规则”“静态推断”“待确认”；不要把解析/导出支持写成渲染支持。
- 实际皮肤的 `skin.ini` path、重复 `[Mania]` 段、默认回退和文件存在性优先于数据库默认文件名。
- 合并多个 Mania keycount 时，先按每个 `Keys:N` 建立实际 path 矩阵；根目录/子目录冲突或透明占位按 `references/merge-recipes.md` 处理，只回写实际消费者小节。
- 修改后复查路径、字段类型、资源闭包、SD/`@2x`、动画、alpha、音频格式和 fallback；没有客户端实测时只报告静态验证。
- 命令失败时读取结构化 `error`/`errors`；非零退出码不是部分成功。

## CLI 入口

需要调用工具时先读取 `references/tools.md` 的工具总表和按需求选择表，再读取领域 reference 中的具体流程。工具不可用时，在技能根目录运行 `python -m pip install -e .`；所有命令优先使用 `--json`，写入工具先用 `--dry-run`。
