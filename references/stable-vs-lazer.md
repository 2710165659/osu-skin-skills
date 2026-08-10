# stable 与 lazer 规则

工具用途：`db-query` 只读核对客户端和元素事实；`mania-analyze` 只读核对 Mania 的实际 path 和依赖；`image-inspect` 只读核对图片尺寸、alpha 和透明行。确认客户端后，运行 `osu-skin db-query "<元素或命令>" --client stable|lazer --json`，核对 `client`、notes 和关联 details。Mania 资源差异按 `mania.md` 的命令分析。完整工具选择见 `tools.md`。

## 客户端识别

| 条件 | 处理 |
|---|---|
| 用户明确说 stable | 按 stable 规则，记录用户声明 |
| 用户明确说 lazer | 按 lazer 规则，记录用户声明 |
| 根目录有 `skininfo.json` | 判定 lazer，记录文件证据 |
| 无 `skininfo.json` 且用户未声明 | 必须询问，不得推断 |
| 用户声明与 `skininfo.json` 冲突 | 暂停客户端相关修改并询问 |

“根目录”是当前皮肤目录，不是整个工作区。不要因为工作区中其他位置存在 `skininfo.json` 就改变当前皮肤的判断。

## stable 迁移到 lazer 后变形

用户已经说明“从 stable 移到 lazer”时，把目标客户端记为 lazer，不再重复询问。没有皮肤文件时只索要皮肤目录/`.osk`/zip、相关 `skin.ini`/图片和 Mania keycount，不猜实际 path、尺寸或 NoteBodyStyle。

取得文件后按固定顺序取证：

1. `db-query --client lazer` 确认元素是否实际消费；未消费时检查程序化 UI、默认资源或 fallback。
2. `mania-analyze --dependencies` 或实际 `skin.ini` 确认 path、keycount、SD/`@2x`、动画和字段。
3. `image-inspect --transparent-rows` 确认真实图片尺寸、alpha 和透明行。
4. 只有确认是 lazer 目标矩形导致的非等比缩放，才读取 `lazer-image-scaling.md` 并执行其中的专用修复；投皮语义和 T 全透明分支读取 `mania-hold-body.md`。

执行缩放或投皮修复时，读取 `lazer-image-scaling.md` 和 `mania-hold-body.md` 的对应流程；本文件中的结论负责 stable/lazer 取证和消费者差异。没有游戏实测时标记为静态验证。

## 数据库 `client` 的含义

- `both`：stable 和 lazer 都实际加载/消费。
- `stable`：stable 实际生效，lazer 不应承诺视觉/行为生效。
- `lazer`：lazer 实际加载，stable 不存在或不使用。
- 解码器能读取、导出或保留字段，不等于渲染器实际使用该字段。

## 资源差异

### lazer 光标消费者

皮肤目录中的 `cursor`、`cursormiddle`、`cursortrail`、`cursor-ripple`、`cursor-smoke` 及其 Cursor 配置字段在 lazer 中仅用于 osu! 标准模式的游玩光标。lazer 的菜单/选歌界面以及 taiko、catch、mania 使用客户端原生光标；混皮时不得只凭数据库跨客户端的 `全局界面` 标签把 std 来源光标自动归为全局基础资源，必须结合 notes。stable 的实际使用范围不同，报告时必须注明客户端。

### lazer 独有

数据库当前标记的 lazer-only 元素包括：

- 图片：`osu-sliderendmiss`、`osu-slidertickmiss`、`score-pp`；
- 音频：`applause-S/A/B/C/D`、`fountain-shoot`、`fountain-loop`、`rank-up`、`rank-down`、`spinnerbonus-max`。

`score-pp.png` 不是默认 lazer HUD 的固定组成；`fountain-loop` 是循环音效。不要把这些文件报告为 stable 缺失。

### stable-only 的典型风险

- 程序化 UI 替代的按钮、界面和部分结算资源；
- 音效也需按实际 `SkinnableSound` 消费点核对：lazer 的 `heartbeat`、`key-*`、`check-*`、`select-*`、`shutter`、`metronomelow`、`sectionpass/sectionfail` 不读取 legacy 皮肤文件，导入成功或存在同名内置资源不等于生效；
- `SliderBallFlip`：lazer 可解析/导出，但当前滑条球渲染不消费；
- Mania 的部分 stable 专属布局字段，如 `ColumnStart`、`ColumnRight`、`SplitStages`、`SpecialStyle` 等；
- 大号 `ranking-A/B/C/D/S/SH/X/XH.png` 在 lazer 当前使用点固定来自默认经典皮肤；不要承诺导入皮肤能覆盖它们。

## 已核验的配置差异

| 字段 | stable/lazer 行为 |
|---|---|
| `NoteBodyStyle` | stable：0 拉伸、1 从顶部叠加、2 从底部叠加，默认 1。lazer：0 拉伸；所有可解析的非 0 整数统一呈现类似从顶部叠加的独立效果。lazer 未配置时版本 `<2.5` 使用拉伸，`>=2.5` 使用非 0 分支。 |
| `JudgementLine` | lazer 未配置时默认显示（1）。 |
| `LightFramePerSecond` | lazer 未配置时 60；配置值 `<=0` 时按 24 处理。 |
| `ScorePosition` | stable 未配置默认 325；lazer 未配置默认 300，lazer 判定图片实际读取此值。 |
| `ColourHold` | lazer 可解析并保留，但当前渲染不消费，按 stable-only 解释。 |
| `ColourLight#` | lazer 接受 RGB/RGBa；省略 alpha 按 255，非零 alpha 应用到列闪光；alpha 0 为兼容 stable 按不透明处理。 |
| `SpecialStyle` | lazer 为导入/导出稳定性保存，当前不实现对应 Mania 渲染。 |
| `SplitStages` / `StageSeparation` | lazer 为导入/导出稳定性保存，当前不据此分割或间隔舞台。 |
| `SliderBallFlip` | stable 生效；lazer 解析但当前不消费。 |

## lazer 自定义 Mania HUD

lazer 的自定义 Mania HUD 布局是完整替代，不是在默认 HUD 上追加。启用自定义布局后，只显示布局中明确保留的组件；误删连击组件会导致连击完全消失，客户端不会自动补回。

`skin.ini` 的 `ComboPosition` 只控制默认生成的 Mania HUD。自定义 HUD 启用时，连击的位置、锚点和缩放以自定义布局为准，`ComboPosition` 不会覆盖它。删除整套自定义 Mania HUD 可以恢复 `skin.ini` 的位置控制，但 PP、按键、CPS、排行榜等一并保存的自定义布局也会失效。

将 legacy 位置手动迁移到 lazer 自定义布局时，纵坐标按 `ComboPosition * 1.6` 换算，并使用顶部居中锚点、组件中心原点和固定锚点。只修改 `skin.ini` 后看不到位置变化时，先检查是否存在自定义 Mania HUD；连击完全不显示时，先检查自定义布局是否仍包含连击组件。

需要直接编辑 lazer 导出的布局数据时，读取 `lazer-layout-json.md`。

## 动画差异

数据库的 `animation.rule` 使用 `has_0_hides_base`：存在 `name-0.png` 时，动画只加载编号帧，不加载 `name.png`。hitXX 也遵循此规则，stable 并不会把无后缀图片作为动画基图同时加载。

stable 的特殊之处是结算界面的判定数量统计会独立读取无后缀 hitXX 图片。这是动画以外的另一处消费；lazer 不因该 stable 结算用途而加载无后缀图片。诊断 `hit0`、`hit50`、`hit100` 等文件时，应分别检查游玩判定动画和 stable 结算统计。

lazer 的通用 legacy 判定只读取 `hit0`、`hit50`、`hit100`、`hit300`，不读取通用 `hit100k`、`hit300g`、`hit300k`。模式专用资源不能据此类推：lazer 会读取全部六种 `mania-hit0/50/100/200/300/300g`，也会读取 `taiko-hit0/100/100k/300/300k`。

## lazer 文件分类

`MainHUDComponents.json`、`SongSelect.json`、`Playfield.json`、`skininfo.json`、`rank-up.wav`、`rank-down.wav`、`fountain-shoot.wav`、`sliderendmiss.png`、`slidertickmiss.png` 等可能是 lazer 文件。客户端未确认时将未知文件标成“待确认”，不要删除。
