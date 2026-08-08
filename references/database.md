# osu! 皮肤元素数据库说明

需要查询字段、文件名、标签、默认值或客户端时，运行 `osu-skin db-query "<查询词>" [--client stable|lazer|both] [--type image|audio|skin_ini] [--tag <标签>] --json`。脚本返回 TODO 时，直接按本文件 SQL 模板查询 `assets/osu_skin.db`。

## 目录

- [概述](#概述)
- [表结构](#表结构)
- [各表字段说明](#各表字段说明)
- [client 字段说明](#client-字段说明)
- [lazer skin.ini 核验说明](#lazer-skinini-核验说明)
- [动画规则](#动画规则-animationrule)
- [完整标签列表](#完整标签列表)
- [常用查询](#常用查询)
- [数据来源与验证](#数据来源与验证)
- [注意事项](#注意事项)

## 概述

`osu_skin.db` 是一个 SQLite 数据库，存储 osu! stable 与 osu! lazer 用户皮肤实际加载的**图片文件、音频文件、skin.ini 配置项**。每条记录都带有**中文说明**、**分类标签**和**客户端归属**（stable 加载 / lazer 加载 / 两者都加载）。

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

## lazer skin.ini 核验说明

以下值以当前 lazer 实现为准：

| 配置项 | lazer 实际行为 |
|---|---|
| `NoteBodyStyle` | 有效值为 `0,2,3,4`：`0`=拉伸，`2`=从顶部重复，`3`=从底部重复，`4`=同时重复顶部和底部；值 `1` 无法解析。未配置时，皮肤版本 `<2.5` 使用 `0`，版本 `>=2.5` 使用 `3` |
| `JudgementLine` | 未配置时默认 `1`（显示） |
| `LightFramePerSecond` | 未配置时默认 `60`；配置值小于等于 `0` 时使用 `24` |
| `SliderBallFlip` | lazer 会解析并可重新导出，但当前滑条球渲染不消费该值，因此按实际生效口径标为 `stable` |
| `SpecialStyle` | lazer 仅为导入/导出稳定性保存该值，当前未实现对应 mania 渲染，因此标为 `stable` |
| `ScorePosition` | lazer 的 Mania 判定组件实际读取该值，因此为 `both`；未配置时 stable 默认 `325`，lazer 默认 `300` |
| `ColourHold` | 支持 `R,G,B` 或 `R,G,B,A`，但 lazer 当前只有解析/导出，没有渲染消费点，因此仍标为 `stable` |
| `ColourLight#` | 支持 `R,G,B` 或 `R,G,B,A`；省略 alpha 时按 `255`，非零 alpha 会实际应用到对应列的闪光图片。为兼容 stable，alpha `0` 在 lazer 渲染时按完全不透明处理 |

大号结算等级图片 `ranking-A/B/C/D/S/SH/X/XH.png` 在 lazer 当前使用点中固定读取默认资源，用户皮肤不能覆盖，因此标为 `stable`。游玩中可覆盖的是对应的 `ranking-*-small.png`，后者仍为 `both`。

## 动画规则 (animation.rule)

| 值 | 含义 | 典型元素 |
|---|---|---|
| `has_0_hides_base` | 若 `{name}-0.png` 存在，则不加载 `{name}.png`，仅加载帧序列 | `followpoint`、`sliderfollowcircle`、`pippidon` 等 |
| `always_load_base` | 即使 `{name}-0.png` 存在，仍同时加载 `{name}.png` 基图 | `hit0`、`hit50`、`hit100` 等 hitXX 系列（仅 stable 端此规则生效；lazer 端 hitXX 也遵循 `has_0_hides_base`） |

> **注意**：`always_load_base` 标记的元素在 stable 下有特殊行为——基图和动画帧共存。lazer 不适用此规则，所有元素统一遵循 `has_0_hides_base`。

## 完整标签列表

| 标签 | 说明 |
|---|---|
| `可选动画` | 该元素支持 `-{n}` 帧动画序列 |
| `有-0隐藏基图` | 若 `-0` 帧文件存在，则不加载无后缀基图 |
| `始终加载基图` | 即使 `-0` 帧存在，仍同时加载无后缀基图（仅 stable hitXX 系列） |
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

-- 查找始终加载基图的动画元素（hitXX 系列）
SELECT e.id, e.filename, a.rule
FROM elements e
JOIN element_tags et ON e.id = et.element_id
JOIN animation a ON e.id = a.element_id
WHERE et.tag = '始终加载基图';

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
```

## 数据来源与验证

数据基于 osu! wiki 英文文档（`Interface/en.md`、`osu!/en.md`、`osu!taiko/en.md`、`osu!catch/en.md`、`osu!mania/en.md`、`Sounds/en.md`、`skin.ini/en.md`）逐一核对整理。每个元素的 `client` 字段参照 osu! lazer 源码分析标注。lazer 数据最近一次按源码提交 `44f96657a557980befc7bdcf29cf7c7a9ef3ab88`（2026-08-03）核验。

## 注意事项

- **lazer 的加载范围近似 stable 的子集**：实际范围约为 stable 元素减去被程序化 UI、动态音效替代或尚未实现的部分，再加少数 lazer 独有元素。
- **解析/导出不等于实际支持**：lazer 会保存部分当前尚未参与渲染的 `skin.ini` 键，以减少重新导出时的数据丢失。`client` 按视觉或行为是否实际生效标注。
- **新增资源**：lazer 支持用户皮肤的 `scoreentry-0..9` 和 `fountain-loop`。
- **hitXX 动画规则差异**：`hit0`/`hit50`/`hit100` 等元素的 `animation.rule` 标注为 `always_load_base`，这是 stable 的规则。lazer 中这些元素实际遵循 `has_0_hides_base`（通用规则），但未拆分两条记录——使用时需注意如果针对 lazer 读取，应忽略 `always_load_base` 规则。
- **转盘样式**：旧样式（v1.0）和新样式（v2.0+）的元素都收录在数据库中，通过 `旧转盘样式` / `新转盘样式` 标签区分。当 `spinner-background.png` 存在于皮肤目录时，即使 skin.ini 版本设为 latest 也会强制使用旧样式。
- **模式共享元素**：部分图片被多个模式共用（如 `lighting.png` 用于 osu! + taiko + catch，`sliderscorepoint.png` 用于 osu! + taiko），在数据库中只有一条记录，通过标签标注了所有适用模式。
