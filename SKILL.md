---
name: osu-skin-skills
description: >-
  处理 osu! stable 与 osu! lazer 皮肤：解释和修改 skin.ini，定位皮肤元素，
  诊断文件不生效、默认回退、透明 PNG 白边、@2x/SD、动画和音效问题，混合皮肤或
  Mania 键位，制作或修改投皮、调整 Mania 列布局，制作 lite 版和打包 .osk。用户提到 skin、
  skin.ini、.osk、hitcircle、cursor、hitsound、PNG 透明、@2x、instafade、Mania
  键位、投、投皮、投 50px、球皮、菱形皮、渐变皮或列位置时都触发。遇到客户端、
  模式、keycount 或修改目标不明确时先提问。
---

# 执行入口

触发后按顺序执行，不要先通读全部 references。

1. 读取 `references/start-here.md`，选择与用户请求对应的入口。
2. 确认输入类型：皮肤目录、`.osk`/zip、`skin.ini`、图片、音频、截图或纯问题。
3. 确认客户端、游戏模式、Mania keycount、源路径、目标路径和是否允许覆盖。
4. 读取入口指定的 reference；按该 reference 写明的 CLI 调用脚本，再读取 `assets/osu_skin.db` 中与当前问题相关的记录。
5. 读取真实文件建立事实；不要只凭文件名或记忆回答。
6. 输出简短计划；需要写入时先列将新增、修改、删除的文件和字段。
7. 执行修改后复查路径、字段、尺寸、alpha、动画、客户端差异和 fallback。
8. 报告结论、证据、实际变更、验证结果、警告和未确认信息。

## 必须提问的情况

### 客户端

按以下规则判断 stable/lazer：

1. 用户明确说 `stable` 或 `lazer` 时按用户说明处理。
2. 在候选皮肤根目录中存在 `skininfo.json` 时判定为 lazer，并说明检测依据。
3. 没有 `skininfo.json` 且用户没有明确说明时，先问：

   `这个皮肤按 osu! stable 还是 osu! lazer 处理？目录没有 skininfo.json，无法仅靠文件可靠判断。`

4. 未获得回答前，只做与客户端无关的只读检查；不要作客户端特有结论或写入客户端相关配置。
5. 用户说明与 `skininfo.json` 冲突时暂停并询问，不要自行选择。
6. 不得用 `MainHUDComponents.json`、`SongSelect.json`、文件名、目录位置或模型记忆替代上述确认。

### 其他需要确认的内容

- 用户说“投”“投皮”“投的长度”“投 50px”时不要做通用“长度”消歧；先读取 `references/mania-hold-body.md`，按投皮领域语义处理。
- 用户只说普通“长度/大小/位置”且没有投皮语境时，才询问具体对象。
- 用户说“Mania 皮肤”但未给 keycount 时，先询问 1K/2K/4K/7K 等具体键数。
- 用户要求混皮但未说明保留哪些模式或资源组时，先询问范围。
- 用户要求原地覆盖、删除第三方文件或安装到游戏目录时，先确认目标和备份方式。
- 用户给出的文件证据不足以确定元素时，先列候选并请求截图、路径或客户端信息。

## Reference 路由

只读取当前任务需要的文件：

| 请求 | 读取 |
|---|---|
| 文件/界面元素是什么 | `references/element-map.md`、`references/field-glossary.md` |
| 数据库 schema、client 口径、查询模板 | `references/database.md` |
| 为什么没生效/变默认/位置错 | `references/troubleshooting.md`、`references/stable-vs-lazer.md` |
| 修改 `skin.ini` 字段 | `references/field-glossary.md` |
| PNG 透明、白边、@2x、动画 | `references/image-animation.md` |
| lazer 图片压扁、拉长、非等比、列宽缩放、投皮重复 | `references/lazer-image-scaling.md`，再按元素读取图片或 Mania reference |
| 投、投皮、投的长度、投 50px、球皮/菱形皮/渐变皮 | `references/mania-hold-body.md`，已有皮肤再读 `references/mania.md` |
| Mania 键位、列位置、判定线、合并 | `references/mania.md` |
| hitsound、MP3、循环音效 | `references/audio.md` |
| 混皮、lite、资源组 | `references/merge-recipes.md` |
| 需要调研证据或解释来源 | `references/research-evidence.md` |

## 数据库使用

`assets/osu_skin.db` 是元素和字段事实源。使用 sqlite 查询时：

- 文件名问题查 `elements.filename`，去掉扩展名、`@2x` 和动画帧后缀再匹配；
- 配置问题查 `elements.command`、`section` 和 `skin_ini_details`；
- 画面描述查 `description`、`category`、`subcategory` 和 `element_tags`；
- 返回 `type`、`client`、适用模式、HD 支持、动画 rule、默认值和备注；
- 不把“解析/导出支持”当成“实际渲染支持”；
- 不一次输出整库，只查询当前任务所需的记录。

## 任务规则

### 元素解释

返回文件或命令、section、用途、适用模式、客户端、HD/谱面覆盖、动画/回退规则和常见误解。用户要求修改时继续执行对应修改流程，不停在定义解释。

### `skin.ini` 修改

1. 从 `field-glossary.md` 确认 section、类型、默认值、有效值、模式和客户端行为。
2. 保留注释、未知字段、原顺序、大小写和所有其他重复 `[Mania]` 段。
3. 修改前显示字段旧值和新值。
4. 修改后检查类型、枚举、RGB/RGBa、逐列值数量和 path 存在性。

### “不生效”诊断

按此顺序检查：客户端和当前选中的皮肤、游戏模式、谱面覆盖、元素是否被目标客户端消费、文件名/路径/扩展名、SD/`@2x`、动画 base/`-0`/帧序、图片格式/alpha、音频格式和 fallback。每个结论标记为“已确认”或“推断”。

### 图片和动画

1. 先检查格式、尺寸、颜色模式、alpha 通道、透明/半透明像素和帧连续性。
2. 区分“有 alpha 通道”“存在透明像素”“全透明”“透明 RGB 会造成 fringe”。
3. 根据数据库中的 `hd_supported`、`suggested_size`、origin、blend mode 和 animation rule 选择处理方式。
4. 生成 SD/HD 或动画后重新检查命名、尺寸、alpha、帧序和比例。
5. 白边问题先检查 alpha=0 像素 RGB 和缩放过滤，不要直接涂黑整张透明区域。

### Mania

1. 出现“投/投皮/投的长度/投 50px”时先读取 `references/mania-hold-body.md`；其他 Mania 任务读取 `references/mania.md`。按对应 reference 中的 `osu-skin` 子命令调用脚本。
2. 找到对应 `Keys: N` 的 `[Mania]` 段；多个段不能默认取第一个。
3. 检查共享字段、逐列字段、`NoteImage#`、`NoteImage#H/L/T`、key、receptor、lighting、stage、默认回退、`@2x` 和动画；数据库标准语义为 H=头、L=体/投皮、T=尾，仍需核对实际 path。
4. 调整列布局时检查 `ColumnStart`、`ColumnWidth`、`ColumnSpacing`、`ColumnLineWidth` 和中心位置。
5. 调整判定/舞台时检查 `HitPosition`、`ScorePosition`、`StageHint`、`StageLight` 和客户端默认值。
6. “投 50px”通常表示投皮图片顶部 50 行透明，不是某个 `skin.ini` 数值；生成器语境输出 `mania-noteNL.png` 一类图片（如 `mania-note1L.png`），对应 `NoteImage#L`，已有皮肤则先读取实际 path。
7. 用户反馈 lazer 投皮重复或非等比缩放时读取 `references/lazer-image-scaling.md`，不要在修改投长度时主动解释渲染推导。
8. 合并 keycount 时复制完整依赖并同步重写 path；保留目标其他 keycount、其他模式、作者和来源。

### 音频

读取 `references/audio.md`。按 Normal/Soft/Drum 和 hitnormal/hitclap/hitfinish/hitwhistle 成族检查；区分游戏格式支持与预览器解码；删除音效可能触发默认 fallback，静音需求优先生成合法静音文件。

### 混皮、lite、`.osk`

- 混皮前读取 `merge-recipes.md`，按 cursor、std gameplay、Mania keycount、hitsound、菜单等资源组处理，不逐文件随机混合。
- lite 版先列保留的客户端、模式和界面，生成删除计划，在新目录执行，再检查 fallback。
- `.osk` 打包时确保皮肤文件位于压缩包根；打包后重新解包检查 `skin.ini` 和资源。

## 脚本规则

首次使用或 `osu-skin` 不可用时，从 Skill 根目录运行 `python -m pip install -e .`。安装后只运行 reference 指定的 `osu-skin <子命令>`。脚本当前只保留 CLI 契约；返回 TODO 或退出码 3 时记录“入口未实现”，不得把 TODO 当成成功证据。

## 输出模板

解释：

```text
结论
涉及文件/字段
原因和客户端差异
修改方法
验证方法
```

诊断：

```text
环境与症状
已确认证据
可能原因（按置信度）
建议修复
未确认信息
```

修改：

```text
输出目录
新增/修改/删除文件
skin.ini 字段变更
验证结果
警告、来源和回退方式
```
