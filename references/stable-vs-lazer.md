# stable 与 lazer 规则

确认客户端后，运行 `osu-skin db-query "<元素或命令>" --client stable|lazer --json`，核对 `client`、notes 和关联 details。Mania 资源差异按 `mania.md` 的命令分析。

## 客户端识别

| 条件 | 处理 |
|---|---|
| 用户明确说 stable | 按 stable 规则，记录用户声明 |
| 用户明确说 lazer | 按 lazer 规则，记录用户声明 |
| 根目录有 `skininfo.json` | 判定 lazer，记录文件证据 |
| 无 `skininfo.json` 且用户未声明 | 必须询问，不得推断 |
| 用户声明与 `skininfo.json` 冲突 | 暂停客户端相关修改并询问 |

“根目录”是当前皮肤目录，不是整个工作区。不要因为工作区中其他位置存在 `skininfo.json` 就改变当前皮肤的判断。

## 数据库 `client` 的含义

- `both`：stable 和 lazer 都实际加载/消费。
- `stable`：stable 实际生效，lazer 不应承诺视觉/行为生效。
- `lazer`：lazer 实际加载，stable 不存在或不使用。
- 解码器能读取、导出或保留字段，不等于渲染器实际使用该字段。

## 资源差异

### lazer 独有

数据库当前标记的 lazer-only 元素包括：

- 图片：`osu-sliderendmiss`、`osu-slidertickmiss`、`score-pp`；
- 音频：`applause-S/A/B/C/D`、`fountain-shoot`、`fountain-loop`、`rank-up`、`rank-down`、`spinnerbonus-max`。

`score-pp.png` 不是默认 lazer HUD 的固定组成；`fountain-loop` 是循环音效。不要把这些文件报告为 stable 缺失。

### stable-only 的典型风险

- 程序化 UI 替代的按钮、界面和部分结算资源；
- `SliderBallFlip`：lazer 可解析/导出，但当前滑条球渲染不消费；
- Mania 的部分 stable 专属布局字段，如 `ColumnStart`、`ColumnRight`、`SplitStages`、`SpecialStyle` 等；
- 大号 `ranking-A/B/C/D/S/SH/X/XH.png` 在 lazer 当前使用点固定来自默认经典皮肤；不要承诺导入皮肤能覆盖它们。

## 已核验的配置差异

| 字段 | stable/lazer 行为 |
|---|---|
| `NoteBodyStyle` | lazer 有效值为 0、2、3、4；值 1 不可解析。版本 `<2.5` 默认 0，`>=2.5` 默认 3。 |
| `JudgementLine` | lazer 未配置时默认显示（1）。 |
| `LightFramePerSecond` | lazer 未配置时 60；配置值 `<=0` 时按 24 处理。 |
| `ScorePosition` | stable 未配置默认 325；lazer 未配置默认 300，lazer 判定图片实际读取此值。 |
| `ColourHold` | lazer 可解析并保留，但当前渲染不消费，按 stable-only 解释。 |
| `ColourLight#` | lazer 接受 RGB/RGBa；省略 alpha 按 255，非零 alpha 应用到列闪光；alpha 0 为兼容 stable 按不透明处理。 |
| `SpecialStyle` | lazer 为导入/导出稳定性保存，当前不实现对应 Mania 渲染。 |
| `SliderBallFlip` | stable 生效；lazer 解析但当前不消费。 |

## 动画差异

数据库的 `animation.rule` 主要有：

- `has_0_hides_base`：存在 `name-0.png` 时不加载 `name.png`；
- `always_load_base`：stable 的 hitXX 等元素即使有 `-0` 仍加载 base。

lazer 对 hitXX 也可能按 `has_0_hides_base` 处理。诊断 `hit0`、`hit50`、`hit100` 等动画时，不要只复述数据库 rule，要注明客户端。

## lazer 文件分类

`MainHUDComponents.json`、`SongSelect.json`、`Playfield.json`、`skininfo.json`、`rank-up.wav`、`rank-down.wav`、`fountain-shoot.wav`、`sliderendmiss.png`、`slidertickmiss.png` 等可能是 lazer 文件。客户端未确认时将未知文件标成“待确认”，不要删除。
