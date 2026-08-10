# osu! 皮肤元素数据库说明

工具用途：`selfcheck` 只读检查数据库完整性、外键和必需表；`db-query` 查询元素、字段、标签、术语、客户端、消费者和 lazer 生成的 JSON 事实，并支持只读 SQL。首次使用、安装后或怀疑资源路径异常时，先运行 `osu-skin selfcheck --json`。需要查询字段、文件名、标签、默认值或客户端时，再运行 `osu-skin db-query "<查询词>" [--client stable|lazer|both] [--type image|audio|skin_ini|lazer_json] [--tag <标签>] --json`。需要自定义只读查询时，使用 `osu-skin db-query --sql "<SQL>" --json` 或 `--sql-file <UTF-8 SQL 文件> --json`；命令拒绝写 SQL。完整工具选择见 `tools.md`。

## 目录

- [概述](#概述)
- [表结构](#表结构)
- [各表字段说明](#各表字段说明)
- [client 字段说明](#client-字段说明)
- [混皮的数据库优先消费者矩阵](#混皮的数据库优先消费者矩阵)
- [lazer skin.ini 核验说明](#lazer-skinini-核验说明)
- [动画规则](#动画规则-animationrule)
- [完整标签列表](#完整标签列表)
- [常用查询](#常用查询)
- [数据来源与验证](#数据来源与验证)
- [注意事项](#注意事项)

## 概述

`osu_skin.db` 是一个 SQLite 数据库，存储 osu! stable 与 osu! lazer 用户皮肤实际加载的**图片文件、音频文件、skin.ini 配置项**，以及经版本核验的 **lazer 布局 JSON 文件、分组、字段、完整 Type 和 Settings**。每条记录都带有**中文说明**、**适用范围**和**验证版本**。

不要在文档中维护记录数快照。需要统计时直接运行本文件“统计查询”中的 SQL，以数据库当前内容为准。

## 表结构

数据库包含以下表：

| 表名 | 用途 |
|---|---|
| `tag_definitions` | 标签定义及说明 |
| `elements` | 元素主表（图片/音频/skin.ini 共有字段） |
| `element_tags` | 元素 ↔ 标签多对多关联 |
| `image_details` | 图片专属字段（混合模式、锚点、尺寸等） |
| `animation` | 动画信息（帧序列模式、加载规则等） |
| `audio_details` | 音频专属字段（循环、格式、支持者要求等） |
| `skin_ini_details` | skin.ini 配置项专属字段（值类型、默认值等） |
| `term_definitions` | 术语及其定义；普通搜索会在 `term_matches` 返回匹配项 |
| `lazer_json_entries` | lazer 生成 JSON 的文件、分组、字段、组件 Type 和 Settings 事实 |

### `lazer_json_entries` — lazer JSON 事实

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | TEXT PK | 事实记录唯一 ID |
| `entry_kind` | TEXT | `file` / `top_level_field` / `group` / `component_field` / `component_type` / `setting` |
| `file_name` | TEXT | JSON 文件名；组件目录记录使用 `*.json layout`，不表示该组件能放入每一个布局目标 |
| `json_path` | TEXT | JSON 路径模式 |
| `ruleset_scope` | TEXT | 文件/分组记录表示读取的 JSON 分组；组件/设置记录表示组件目录来源：`global`、`osu` 或 `mania` |
| `component_type` | TEXT | 不含程序集限定信息的类型名 |
| `assembly_qualified_type` | TEXT | lazer 生成的完整 Type 字符串 |
| `field_name` | TEXT | 字段或 Settings 键名 |
| `value_type` | TEXT | JSON 值类型 |
| `default_value` | TEXT | 默认/生成值 |
| `valid_values` | TEXT | 合法值和枚举映射 |
| `description` | TEXT | 确定用途 |
| `notes` | TEXT | fallback、覆盖和版本注意事项 |
| `verified_lazer_version` | TEXT | 事实核验的 lazer 版本 |
| `search_terms` | TEXT | 普通搜索的别名词 |

`component_type` 记录覆盖 `verified_lazer_version` 所标构建中组件目录返回的全部公开具体类型；`setting` 记录覆盖这些类型继承后的全部可序列化设置。组件目录来源不等于目标兼容性：编辑器是否允许把一个类型加入某个 HUD、选歌或 Playfield 目标，还取决于该目标提供的运行上下文和组件自身的可编辑状态。

## 各表字段说明

### `tag_definitions` — 标签定义

| 列 | 类型 | 说明 |
|---|---|---|
| `tag` | TEXT PK | 标签名 |
| `description` | TEXT | 中文说明 |

### `elements` — 元素主表

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | TEXT PK | 唯一标识，如 `hitcircle`、`followpoint`、`HitCirclePrefix` |
| `filename` | TEXT | 文件名或文件名模式；skin_ini 类型为 NULL |
| `command` | TEXT | skin.ini 命令名；图片/音频为 NULL |
| `section` | TEXT | skin.ini 所属节，如 `[General]`；图片/音频为 NULL |
| `type` | TEXT | `image` / `audio` / `skin_ini` |
| `category` | TEXT | 分类中文名，如"打击圈"、"光标"、"倒计时" |
| `subcategory` | TEXT | 子分类中文名，如"滑条"、"长按音符" |
| `description` | TEXT | 中文说明 |
| `notes` | TEXT | 额外备注 |
| `client` | TEXT | `stable`=仅 stable 实际生效，`lazer`=仅 lazer 实际加载，`both`=两边都实际加载 |

### `element_tags` — 元素标签关联

| 列 | 类型 | 说明 |
|---|---|---|
| `element_id` | TEXT FK | 关联 `elements.id` |
| `tag` | TEXT FK | 关联 `tag_definitions.tag` |

### `image_details` — 图片专属字段

| 列 | 类型 | 说明 |
|---|---|---|
| `element_id` | TEXT PK FK | 关联 `elements.id` |
| `blend_mode` | TEXT | 混合模式：`Normal` / `Additive` / `Multiplicative` |
| `origin` | TEXT | 锚点：`Centre` / `TopLeft` / `TopRight` / `BottomLeft` / `BottomRight` / `Top` / `Bottom` / `Left` / `Right` |
| `suggested_size` | TEXT | 建议 SD 尺寸，如 `128x128` |
| `hd_supported` | INTEGER | 是否支持 @2x 高清变体（1=支持，0=不支持） |
| `beatmap_skinnable` | INTEGER | 是否可被谱面皮肤覆盖（1=是，0=否） |

### `animation` — 动画信息

| 列 | 类型 | 说明 |
|---|---|---|
| `element_id` | TEXT PK FK | 关联 `elements.id` |
| `pattern` | TEXT | 帧文件名模式，如 `followpoint-{n}.png` 或 `sliderb{n}.png` |
| `frame_range` | TEXT | 帧数范围，如 `0-∞` 或 `0-9` |
| `fps` | REAL | 固定帧率；NULL 表示依赖 `AnimationFramerate` 全局设置或 BPM |
| `loops` | INTEGER | 是否循环播放（1=循环，0=不循环） |
| `rule` | TEXT | 动画加载规则（见下文） |

### `audio_details` — 音频专属字段

| 列 | 类型 | 说明 |
|---|---|---|
| `element_id` | TEXT PK FK | 关联 `elements.id` |
| `looped` | INTEGER | 是否循环播放（1=循环，0=单次） |
| `formats` | TEXT | 支持格式，逗号分隔，如 `wav,mp3,ogg` |
| `beatmap_skinnable` | INTEGER | 是否可被谱面皮肤覆盖 |
| `requires_supporter` | INTEGER | 是否需要 osu!supporter |

### `skin_ini_details` — 配置项专属字段

| 列 | 类型 | 说明 |
|---|---|---|
| `element_id` | TEXT PK FK | 关联 `elements.id` |
| `value_type` | TEXT | 值类型，如 `boolean` / `integer` / `number` / `text` / `path` / `RGB` / `RGBa` / `comma_split_numbers` |
| `default_value` | TEXT | 默认值 |
| `valid_values` | TEXT | 有效值列表（枚举型时），逗号分隔 |
| `game_mode` | TEXT | 适用游戏模式，逗号分隔，如 `osu` / `all` / `osu,catch,mania` |

### `term_definitions` — 术语定义

| 列 | 类型 | 说明 |
|---|---|---|
| `term` | TEXT PK | 术语名 |
| `description` | TEXT | 术语定义及必要的客户端/代码口径 |

## client 字段说明

`elements.client` 用于区分皮肤元素在哪个客户端实际生效。仅被 lazer 解析并在导出时保留、但当前不参与渲染或行为的 `skin.ini` 键，不算 lazer 实际支持。

| 值 | 含义 |
|---|---|
| `both` | stable 与 lazer 都实际加载 |
| `stable` | 仅 stable 实际生效；lazer 未实现、未消费或被程序化替代 |
| `lazer` | 仅 lazer 加载，stable 不存在或不使用 |

查询 lazer 独有元素，不在文档中维护静态清单：

```sql
SELECT id, filename, command, type, description
FROM elements
WHERE client = 'lazer'
ORDER BY type, id;
```

补充限制：

- `score-pp.png` 仅由 lazer 的性能点数计数器使用。该组件通常需要通过皮肤布局编辑器添加。
- `fountain-loop` 是循环音效。lazer 请求 `Gameplay/fountain-loop` 时会回退查找皮肤根目录中的 `fountain-loop.wav/.mp3/.ogg`。
- `scoreentry-0.png` 到 `scoreentry-9.png` 属于 `both`，不是 lazer 独有；lazer 在 osu!/catch 的按键计数器中读取它们。
- cursor 图片和 Cursor 配置虽然为 `both`，但 lazer 只在 osu! 标准模式游玩中消费皮肤版本。lazer 的菜单/选歌界面及 taiko/catch/mania 使用原生光标；查询时必须读取 notes，不能只凭 `全局界面` 标签推断消费者。

## 混皮的数据库优先消费者矩阵

混皮时，用户口头指定“std 用 A、taiko 用 B、Mania 4K 用 C”只定义目标范围和来源候选，不定义文件归属，也不指定全局基础皮肤。写文件前按以下顺序建立矩阵：

1. 枚举各来源和目标中的普通图、`@2x`、动画、音频与 `skin.ini` path/prefix，按文件族去重；
2. 对每个文件族按目标客户端运行 `db-query`，读取 `client`、标签、description/notes；
3. 对每个字段查询 `skin_ini_details.game_mode`，并反向检查目标所有 section、Mania keycount 和自定义路径；
4. 记录目标消费者与目标外消费者。数据库未知、候选不唯一、跨模式、`all`、全局界面和跨 keycount 引用均进入确认项；
5. 未确认时保留目标资源。不要把 std 来源自动用于 cursor、score、combo、菜单、音频、`[Fonts]`、共享字段或元数据。

可用以下 SQL 一次取得字段或文件的数据库消费者证据：

```sql
SELECT e.id, e.filename, e.command, e.client, e.description, e.notes,
       sd.game_mode, GROUP_CONCAT(DISTINCT et.tag) AS tags
FROM elements e
LEFT JOIN skin_ini_details sd ON sd.element_id = e.id
LEFT JOIN element_tags et ON et.element_id = e.id
WHERE e.id IN ('cursor', 'cursortrail', 'ComboPrefix', 'ComboOverlap')
GROUP BY e.id
ORDER BY e.id;
```

`ComboPrefix`、`ComboOverlap` 和 `[Colours]` 的 `Combo1..8` 的消费者是 `osu,catch`。taiko 与 mania 不使用这组连击数字/颜色；但从 std 来源覆盖该组仍会改变 catch，因此必须单独确认。

### 混皮时直接运行的查询

以下查询用于建立“来源候选 → 数据库元素 → 模式/界面消费者 → 客户端”的矩阵。可保存为 UTF-8 文件后运行 `osu-skin db-query --sql-file .\consumer-matrix.sql --json`，或直接作为 `--sql` 参数传入。

**1. 文件族的完整元素详情、标签定义和专属字段**

```sql
SELECT e.id, e.filename, e.command, e.section, e.type,
       e.category, e.subcategory, e.description, e.notes, e.client,
       GROUP_CONCAT(DISTINCT et.tag) AS tags,
       GROUP_CONCAT(DISTINCT td.description) AS tag_descriptions,
       idt.blend_mode, idt.origin, idt.suggested_size, idt.hd_supported,
       idt.beatmap_skinnable AS image_beatmap_skinnable,
       a.pattern, a.frame_range, a.fps, a.loops, a.rule AS animation_rule,
       ad.looped, ad.formats,
       ad.beatmap_skinnable AS audio_beatmap_skinnable,
       ad.requires_supporter,
       sd.value_type, sd.default_value, sd.valid_values, sd.game_mode
FROM elements e
LEFT JOIN element_tags et ON et.element_id = e.id
LEFT JOIN tag_definitions td ON td.tag = et.tag
LEFT JOIN image_details idt ON idt.element_id = e.id
LEFT JOIN animation a ON a.element_id = e.id
LEFT JOIN audio_details ad ON ad.element_id = e.id
LEFT JOIN skin_ini_details sd ON sd.element_id = e.id
WHERE lower(COALESCE(e.filename, e.id, e.command, '')) LIKE lower('%cursor%')
GROUP BY e.id
ORDER BY e.type, e.id;
```

把 `'%cursor%'` 换成去掉 `@2x`、扩展名和动画帧号后的文件族关键词；候选不唯一时全部保留并逐项确认。

**2. 找出可能跨模式、全模式或全局共享的资源**

```sql
WITH mode_usage AS (
    SELECT e.id,
           MAX(et.tag = 'std模式') AS std_mode,
           MAX(et.tag = '太鼓模式') AS taiko_mode,
           MAX(et.tag = '接水果模式') AS catch_mode,
           MAX(et.tag = 'mania模式') AS mania_mode,
           MAX(et.tag = '全模式') AS all_modes,
           MAX(et.tag = '全局界面') AS global_ui
    FROM elements e
    LEFT JOIN element_tags et ON et.element_id = e.id
    GROUP BY e.id
)
SELECT e.id, e.filename, e.command, e.type, e.client,
       e.description, e.notes,
       m.std_mode, m.taiko_mode, m.catch_mode, m.mania_mode,
       m.all_modes, m.global_ui,
       GROUP_CONCAT(DISTINCT et.tag) AS tags
FROM elements e
JOIN mode_usage m ON m.id = e.id
LEFT JOIN element_tags et ON et.element_id = e.id
WHERE (m.std_mode + m.taiko_mode + m.catch_mode + m.mania_mode > 1)
   OR m.all_modes = 1 OR m.global_ui = 1
GROUP BY e.id
ORDER BY e.type, e.id;
```

结果中的任意一项都不能直接从 A 覆盖到 B；必须按目标范围说明会影响哪些模式/界面，并逐资源组确认。

**3. 查找配置字段的模式消费者和共享范围**

```sql
SELECT e.id, e.command, e.section, e.client,
       e.description, e.notes,
       sd.value_type, sd.default_value, sd.valid_values, sd.game_mode,
       GROUP_CONCAT(DISTINCT et.tag) AS tags
FROM elements e
JOIN skin_ini_details sd ON sd.element_id = e.id
LEFT JOIN element_tags et ON et.element_id = e.id
WHERE sd.game_mode = 'all'
   OR instr(',' || sd.game_mode || ',', ',osu,') > 0
   OR instr(',' || sd.game_mode || ',', ',catch,') > 0
   OR instr(',' || sd.game_mode || ',', ',taiko,') > 0
   OR instr(',' || sd.game_mode || ',', ',mania,') > 0
GROUP BY e.id
ORDER BY e.section, e.id;
```

`game_mode` 说明字段适用范围，不证明某个皮肤实际填写了该字段；仍须读取目标和来源 `skin.ini` 的实际值、路径和重复 `[Mania]` 段。

**4. 查找 Mania 字段和跨 keycount 风险**

```sql
SELECT e.id, e.command, e.description, e.notes,
       sd.value_type, sd.default_value, sd.valid_values, sd.game_mode,
       GROUP_CONCAT(DISTINCT et.tag) AS tags
FROM elements e
JOIN skin_ini_details sd ON sd.element_id = e.id
LEFT JOIN element_tags et ON et.element_id = e.id
WHERE e.section = '[Mania]'
GROUP BY e.id
ORDER BY e.id;
```

数据库能说明字段的通用语义和模式范围，但没有目标皮肤每个 `Keys: N` 段的实际 path；跨 4K/5K/7K 的共享必须结合 `skin.ini` 和 `mania-analyze --dependencies` 结果确认。

## lazer skin.ini 核验说明

以下值以当前 lazer 实现为准：

| 配置项 | lazer 实际行为 |
|---|---|
| `NoteBodyStyle` | stable 使用 `0`=拉伸、`1`=从顶部叠加、`2`=从底部叠加，默认 `1`。lazer 使用 `0`=拉伸；所有可解析的非 `0` 整数统一进入 lazer 独立实现的重复/填充分支，效果类似从顶部叠加，不区分 stable 的顶部与底部叠加。lazer 未配置时，皮肤版本 `<2.5` 使用拉伸，版本 `>=2.5` 使用非 `0` 分支 |
| `JudgementLine` | 未配置时默认 `1`（显示） |
| `LightFramePerSecond` | 未配置时默认 `60`；配置值小于等于 `0` 时使用 `24` |
| `SliderBallFlip` | lazer 会解析并可重新导出，但当前滑条球渲染不消费该值，因此按实际生效口径标为 `stable` |
| `SpecialStyle` | lazer 仅为导入/导出稳定性保存该值，当前未实现对应 mania 渲染，因此标为 `stable` |
| `ScorePosition` | lazer 的 Mania 判定组件实际读取该值，因此为 `both`；未配置时 stable 默认 `325`，lazer 默认 `300` |
| `HitPosition` / `LightPosition` / `ScorePosition` / `ComboPosition` | 使用高为 `480` 的 legacy 纵向坐标；向下滚动时 `0` 顶部、`480` 底部、`240` 中央。lazer 映射到高 `768` 的内部舞台；前三项在向上滚动时镜像，ComboPosition 不镜像。HitPosition 额外钳制到 `240..480` |
| `ColourHold` | 支持 `R,G,B` 或 `R,G,B,A`，但 lazer 当前只有解析/导出，没有渲染消费点，因此仍标为 `stable` |
| `ColourLight#` | 支持 `R,G,B` 或 `R,G,B,A`；省略 alpha 时按 `255`，非零 alpha 会实际应用到对应列的闪光图片。为兼容 stable，alpha `0` 在 lazer 渲染时按完全不透明处理 |

> **stable/lazer 差异**：公开的 [`skin.ini` 页面](https://osu.ppy.sh/wiki/en/Skinning/skin.ini) 所列 `0/1/2` 和默认 `1` 是 stable 口径。当前 lazer 可以解析整数值，但渲染只区分 `0` 与非 `0`；不要把 stable 的顶部/底部叠加语义直接套到 lazer。

大号结算等级图片 `ranking-A/B/C/D/S/SH/X/XH.png` 在 lazer 当前使用点中固定读取默认资源，用户皮肤不能覆盖，因此标为 `stable`。游玩中可覆盖的是对应的 `ranking-*-small.png`，后者仍为 `both`。

### Mania 舞台记录的表达边界

- `image_details.origin` 只记录图片自身 origin，不能同时表达父容器 anchor、向上/向下滚动时切换的 origin 或额外缩放。查询 `StageBottom/Left/Right` 时必须同时读取 `elements.notes` 和 `lazer-image-scaling.md`。
- `skin_ini_details.default_value` 对 Mania 舞台 path 应写出实际默认 basename；实际皮肤未显式配置字段时仍需由 `mania-analyze` 确认 `path_sources=default` 和根目录文件是否存在。
- `StageBottom` 的画布顶部和可见顶部不是数据库静态坐标；它们取决于实际 SD/`@2x` 图片高度、alpha 边界、滚动方向和客户端缩放。

## 动画规则 (animation.rule)

| 值 | 含义 | 典型元素 |
|---|---|---|
| `has_0_hides_base` | 若 `{name}-0.png` 存在，则不加载 `{name}.png`，仅加载帧序列 | `followpoint`、`sliderfollowcircle`、`pippidon`、hitXX 等 |

> **注意**：hitXX 没有动画例外。stable 结算界面的判定数量统计会另行读取无后缀 hitXX 图片，但这不表示动画同时加载基图；lazer 也按 `has_0_hides_base` 选择动画帧。

## 完整标签列表

| 标签 | 说明 |
|---|---|
| `可选动画` | 该元素支持 `-{n}` 帧动画序列 |
| `有-0隐藏基图` | 若 `-0` 帧文件存在，则不加载无后缀基图 |
| `结算统计基图` | stable 结算界面的判定数量统计会独立读取无后缀 hitXX 图片；这不是动画基图 |
| `std模式` | 用于 osu! 标准模式 |
| `太鼓模式` | 用于 osu!taiko 模式 |
| `接水果模式` | 用于 osu!catch 模式 |
| `mania模式` | 用于 osu!mania 模式 |
| `全模式` | 所有游戏模式通用 |
| `菜单界面` | 主菜单界面元素 |
| `选歌界面` | 歌曲选择界面元素 |
| `游玩界面` | 游戏进行中的界面元素 |
| `结算界面` | 结算/排名界面元素 |
| `暂停界面` | 暂停、失败等覆盖层界面元素 |
| `全局界面` | 跨界面通用元素（如光标、按钮组件等） |
| `可配置路径` | skin.ini 中可用命令重新指定此元素的文件路径或文件名前缀 |
| `谱面可自定义` | 可被谱面皮肤覆盖 (beatmap skinnable) |
| `需要支持者` | 需要 osu!supporter 标签才能生效 |
| `旧转盘样式` | v1.0 旧版转盘元素 |
| `新转盘样式` | v2.0+ 新版转盘元素 |
| `lazer独有` | 仅 lazer 客户端加载 |
| `稳定独有` | 仅 stable 客户端加载 |
| `倒计时` | 倒计时相关元素 |
| `打击结果` | Miss/50/100/300 等打击判定结果动画 |
| `分数数字` | 分数/连击数字显示 |
| `连击提示` | 连击爆发 (combo burst) 图片/音效 |
| `模组选择` | 模组图标相关元素 |
| `游戏模式` | osu!/taiko/catch/mania 模式图标 |

## 常用查询

### 按客户端过滤

```sql
-- stable 加载的全部元素
SELECT * FROM elements WHERE client IN ('both', 'stable');

-- lazer 加载的全部元素
SELECT * FROM elements WHERE client IN ('both', 'lazer');

-- lazer 独有的元素（极少数）
SELECT * FROM elements WHERE client = 'lazer';

-- stable 有但 lazer 没有的元素
SELECT * FROM elements WHERE client = 'stable';
```

### 按类型查询

```sql
-- 所有图片
SELECT id, filename, category, subcategory, description FROM elements WHERE type = 'image';

-- 所有音频
SELECT id, filename, category, description FROM elements WHERE type = 'audio';

-- 所有 skin.ini 配置项
SELECT id, command, section, description, value_type, default_value
FROM elements e JOIN skin_ini_details d ON e.id = d.element_id
WHERE e.type = 'skin_ini' ORDER BY e.section, e.id;
```

### lazer 布局 JSON

```sql
-- 四个 JSON 文件及其确定事实
SELECT entry_kind, file_name, json_path, ruleset_scope,
       component_type, assembly_qualified_type, field_name,
       value_type, default_value, valid_values, description,
       notes, verified_lazer_version
FROM lazer_json_entries
ORDER BY file_name, json_path, entry_kind, id;

-- 当前核验构建的完整组件 Type 目录
SELECT ruleset_scope, component_type, assembly_qualified_type,
       description, notes, verified_lazer_version
FROM lazer_json_entries
WHERE entry_kind = 'component_type'
ORDER BY ruleset_scope, component_type;

-- Mania 连击 Type 和位置字段
SELECT entry_kind, file_name, json_path, component_type,
       assembly_qualified_type, field_name, description, notes
FROM lazer_json_entries
WHERE LOWER(COALESCE(component_type, '')) LIKE '%mania%'
   OR LOWER(COALESCE(field_name, '')) IN ('position', 'anchor', 'origin', 'usesfixedanchor')
ORDER BY entry_kind, id;

-- 某个组件的全部设置
SELECT component_type, field_name, value_type,
       default_value, valid_values, description, notes
FROM lazer_json_entries
WHERE entry_kind = 'setting'
  AND component_type = 'osu.Game.Screens.Play.HUD.ArgonPerformancePointsCounter'
ORDER BY field_name;
```

### 按标签过滤

```sql
-- 查找所有可动画元素
SELECT e.id, e.filename, e.description
FROM elements e JOIN element_tags et ON e.id = et.element_id
WHERE et.tag = '可选动画' AND e.type = 'image';

-- 查找带有"有-0隐藏基图"规则的动画元素（带帧模式）
SELECT e.id, e.filename, a.pattern, a.rule
FROM elements e
JOIN element_tags et ON e.id = et.element_id
JOIN animation a ON e.id = a.element_id
WHERE et.tag = '有-0隐藏基图';

-- 查找 stable 结算统计独立读取无后缀图片的 hitXX 元素
SELECT e.id, e.filename, e.notes
FROM elements e
JOIN element_tags et ON e.id = et.element_id
WHERE et.tag = '结算统计基图';

-- 查找 skin.ini 中可配置路径的命令
SELECT e.id, e.command, e.section, e.description
FROM elements e
JOIN element_tags et ON e.id = et.element_id
WHERE e.type = 'skin_ini' AND et.tag = '可配置路径'
ORDER BY e.section;

-- lazer 加载的所有 osu!taiko 图片
SELECT e.id, e.filename, e.description
FROM elements e
JOIN element_tags et ON e.id = et.element_id
WHERE e.type = 'image' AND e.client IN ('both', 'lazer')
  AND et.tag = '太鼓模式'
ORDER BY e.id;
```

### 按界面位置过滤

```sql
-- 菜单界面元素
SELECT id, filename, type, description FROM elements e
JOIN element_tags et ON e.id = et.element_id
WHERE et.tag = '菜单界面' AND e.client IN ('both', 'stable');

-- 游玩界面元素（游戏 HUD）
SELECT id, filename, type, description FROM elements e
JOIN element_tags et ON e.id = et.element_id
WHERE et.tag = '游玩界面' AND e.client IN ('both', 'stable');

-- 选歌界面元素
SELECT id, filename, type, description FROM elements e
JOIN element_tags et ON e.id = et.element_id
WHERE et.tag = '选歌界面' AND e.client IN ('both', 'stable');
```

### 完整信息查询（联表）

```sql
-- 图片 + 动画 + 标签（stable 加载）
SELECT e.id, e.filename, e.category, e.subcategory, e.description,
       d.blend_mode, d.origin, d.suggested_size, d.hd_supported, d.beatmap_skinnable,
       a.pattern, a.frame_range, a.fps, a.loops, a.rule,
       GROUP_CONCAT(et.tag, ', ') AS tags
FROM elements e
LEFT JOIN image_details d ON e.id = d.element_id
LEFT JOIN animation a ON e.id = a.element_id
LEFT JOIN element_tags et ON e.id = et.element_id
WHERE e.type = 'image' AND e.client IN ('both', 'stable')
GROUP BY e.id
ORDER BY e.category, e.subcategory, e.id;

-- 音频 + 标签（lazer 加载）
SELECT e.id, e.filename, e.category, e.description,
       d.looped, d.formats, d.beatmap_skinnable, d.requires_supporter,
       GROUP_CONCAT(et.tag, ', ') AS tags
FROM elements e
LEFT JOIN audio_details d ON e.id = d.element_id
LEFT JOIN element_tags et ON e.id = et.element_id
WHERE e.type = 'audio' AND e.client IN ('both', 'lazer')
GROUP BY e.id
ORDER BY e.category, e.id;

-- skin.ini 完整信息（stable 加载）
SELECT e.id, e.command, e.section, e.description, e.notes,
       d.value_type, d.default_value, d.valid_values, d.game_mode,
       GROUP_CONCAT(et.tag, ', ') AS tags
FROM elements e
LEFT JOIN skin_ini_details d ON e.id = d.element_id
LEFT JOIN element_tags et ON e.id = et.element_id
WHERE e.type = 'skin_ini' AND e.client IN ('both', 'stable')
GROUP BY e.id
ORDER BY e.section, e.id;
```

### 统计查询

```sql
-- 各客户端元素分布
SELECT type, client, COUNT(*) FROM elements
GROUP BY type, client ORDER BY type, client;

-- 标签使用排行
SELECT tag, COUNT(*) AS cnt FROM element_tags
GROUP BY tag ORDER BY cnt DESC;

-- 各分类元素数量
SELECT category, type, COUNT(*) FROM elements
GROUP BY category, type ORDER BY COUNT(*) DESC;

-- 动画规则使用统计
SELECT rule, COUNT(*) FROM animation GROUP BY rule;

-- lazer JSON 事实按记录类型统计
SELECT entry_kind, COUNT(*) AS cnt
FROM lazer_json_entries
GROUP BY entry_kind ORDER BY entry_kind;
```

## 数据来源与验证

数据基于 osu! 官方 skinning 文档逐一核对整理。每个元素的 `client` 字段按 stable/lazer 的实际加载和生效行为标注；lazer 元素数据最近一次核验日期为 2026-08-03，JSON 事实按 `lazer_json_entries.verified_lazer_version` 标注版本。

## 注意事项

- **lazer 的加载范围近似 stable 的子集**：实际范围约为 stable 元素减去被程序化 UI、动态音效替代或尚未实现的部分，再加少数 lazer 独有元素。
- **解析/导出不等于实际支持**：lazer 会保存部分当前尚未参与渲染的 `skin.ini` 键，以减少重新导出时的数据丢失。`client` 按视觉或行为是否实际生效标注。
- **新增资源**：lazer 支持用户皮肤的 `scoreentry-0..9` 和 `fountain-loop`。
- **hitXX 的两个消费者**：`hit0`/`hit50`/`hit100` 等元素的动画遵循 `has_0_hides_base`；stable 结算界面的判定数量统计会另外读取无后缀图片。后者不属于动画加载规则，带 `结算统计基图` 标签的记录可用于查询该用途。
- **lazer 判定图片范围**：通用 legacy 判定只读取 `hit0`、`hit50`、`hit100`、`hit300`；通用 `hit100k`、`hit300g`、`hit300k` 为 stable-only。模式专用的六种 `mania-hitXX` 和五种 `taiko-hitXX` 均有 lazer 消费点，不能按通用文件名范围推断。
- **转盘样式**：旧样式（v1.0）和新样式（v2.0+）的元素都收录在数据库中，通过 `旧转盘样式` / `新转盘样式` 标签区分。当 `spinner-background.png` 存在于皮肤目录时，即使 skin.ini 版本设为 latest 也会强制使用旧样式。
- **模式共享元素**：部分图片被多个模式共用（如 `lighting.png` 用于 osu! + taiko + catch，`sliderscorepoint.png` 用于 osu! + taiko），在数据库中只有一条记录，通过标签标注了所有适用模式。
