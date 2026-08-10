# `skin.ini` 字段语义和修改约束

工具用途：`db-query --type skin_ini` 只读查询字段 section、值类型、默认值、有效值和客户端；它不修改 `skin.ini`。解释或修改字段前，运行 `osu-skin db-query "<命令名>" --type skin_ini --json`。处理 `NoteImage#L` 或 `NoteBodyStyle` 时再读取 `mania-hold-body.md`。完整工具选择见 `tools.md`。

## 目录

- [解析规则](#解析规则)
- [General](#general)
- [Colours](#colours)
- [Fonts](#fonts)
- [CatchTheBeat](#catchthebeat)
- [Mania 总览](#mania-总览)

## 解析规则

- 命令大小写敏感；section 名称按 osu! 规则书写。
- 保留注释、空行、未知字段、原顺序和原编码。
- `[Mania]` 可以出现多个实例；用其中的 `Keys` 选择目标段，不能把同名段合并。
- 带 `#` 的命令中 `#` 从 1 开始；逐列值的数量必须与 `Keys` 和字段语义一致。
- RGB 是 `R,G,B`；RGBa 是 `R,G,B,A`。检查范围 0-255 和是否需要 alpha。
- path 字段按实际皮肤规则解析；编辑前检查目标文件、扩展名、省略扩展名和动画后缀。
- 未配置值与显式默认值不同；报告中同时给出“未配置时默认”和“当前文件值”。

## `[General]`

| 命令 | 类型 | 语义/默认 | 修改时检查 |
|---|---|---|---|
| `Name` | text | 皮肤名，默认 `Unknown` | 导出名称；不要把作者写入 Name |
| `Author` | text | 作者，默认空 | 混皮时合并来源，不冒充原创 |
| `Version` | enum text | `1.0..2.7/latest`，无文件时 latest，有文件未指定时 1.0 | 影响客户端行为；不要随意升级 |
| `AnimationFramerate` | positive integer | 依赖此设置的动画 FPS，默认 -1 | 不覆盖固定 FPS 和 Mania `LightFramePerSecond` |
| `AllowSliderBallTint` | boolean | 滑条球是否使用 combo 色，默认 0 | 只适用于 osu；和 `SliderBall` 区分 |
| `CursorCentre` | boolean | 光标原点在中心，默认 1 | 改动会造成光标视觉偏移 |
| `CursorExpand` | boolean | 点击时光标放大，默认 1 | 只改行为，不改 cursor 图片 |
| `CursorRotate` | boolean | 光标持续旋转，默认 1 | 动画/旋转与图片方向分开 |
| `CursorTrailRotate` | boolean | 尾迹持续旋转，默认 1 | 影响 cursortrail 组 |
| `ComboBurstRandom` | boolean | combo burst 随机顺序，默认 0 | 不适用于 taiko；stable 行为优先 |
| `CustomComboBurstSounds` | boolean | 使用编号 combo burst 音效，默认 0 | 检查对应音频组 |
| `HitCircleOverlayAboveNumber` | boolean | overlay 在数字上方，默认 1 | 影响 std 的图层关系 |
| `LayeredHitSounds` | boolean | 总是播放 hitnormal，默认 1 | 不适用于 taiko；检查 hitsound fallback |
| `SliderBallFlip` | boolean | 滑条球反转时水平翻转，默认 1 | stable 生效；lazer 当前解析但不消费 |
| `SpinnerFadePlayfield` | boolean | 转盘时暗化 playfield，默认 0 | stable-only 风险 |
| `SpinnerFrequencyModulate` | boolean | 提高 spinnerspin 音调，默认 1 | 检查音频与客户端 |
| `SpinnerNoBlink` | boolean | spinner 量计顶部持续显示，默认 0 | 不要把图像问题当成字段问题 |

## `[Colours]`

| 命令 | 类型 | 语义/默认 |
|---|---|---|
| `Combo1..Combo8` | RGB | 连击色；默认前四个为 255,192,0 / 0,202,0 / 18,124,255 / 242,24,57 |
| `SliderBall` | RGB | 禁用滑条球着色时的颜色，默认 2,170,255 |
| `SliderBorder` | RGB | 滑条外缘，默认白色 |
| `SliderTrackOverride` | RGB | 统一滑条体颜色；未配置时使用 combo 色 |
| `SpinnerBackground` | RGB | spinner-background 着色，默认 100,100,100 |
| `InputOverlayText` | RGB | 输入覆盖层数字，默认黑色；适用 osu/catch |
| `MenuGlow` | RGB | 主菜单频谱条，supporter，stable 风险 |
| `SongSelectActiveText` | RGB | 选中面板文字，stable |
| `SongSelectInactiveText` | RGB | 未选面板文字，stable |
| `StarBreakAdditive` | RGB | 休息时 star2 颜色，默认 255,182,193 |

修改颜色时说明是 combo、滑条、spinner、菜单还是 Mania 列颜色；不要把 `[Colours] Combo#` 和 `[Mania] Colour#` 混为一组。

## `[Fonts]`

| 命令 | 类型 | 语义/默认 | 诊断用途 |
|---|---|---|---|
| `ComboPrefix` | path | osu!/catch 连击数字前缀，默认 `score` | 检查 combo-0..9 图片；taiko/mania 不使用此组 |
| `ComboOverlap` | integer | osu!/catch 连击数字重叠像素，默认 0 | 影响 combo 数字宽度；taiko/mania 不使用此组 |
| `ScorePrefix` | path | 分数数字前缀，默认 `score` | 检查 score-0..9 |
| `ScoreOverlap` | integer | 分数数字重叠像素，默认 0 | 影响 HUD 数字 |
| `HitCirclePrefix` | path | hitcircle 数字前缀，默认 `default` | instafade/自定义数字入口 |
| `HitCircleOverlap` | integer | hitcircle 数字重叠像素，默认 -2；负数增加空隙 | 双位数重叠的第一检查项 |

instafade 后 10 以上数字重叠时，同时检查 `HitCirclePrefix` 指向的图片尺寸、`HitCircleOverlap`、HD/SD 和运行分辨率。

## `[CatchTheBeat]`

| 命令 | 类型 | 语义/默认 |
|---|---|---|
| `HyperDash` | RGB | 红果跳颜色，默认 255,0,0 |
| `HyperDashAfterImage` | RGB | 红果跳残像；未配置时继承 HyperDash |
| `HyperDashFruit` | RGB | 大果颜色；未配置时继承 HyperDash |

## `[Mania]` 总览

`Keys` 识别一个 keycount 段；以下字段分为几何、颜色、路径、行为、判定和舞台。完整命令仍以数据库为准。

### 几何与位置

以下纵向位置字段使用高为 `480` 的 legacy Mania 坐标系。向下滚动时 `0` 是舞台顶部、`480` 是舞台底部，位置约占舞台高度的 `值 / 480`；因此 `240` 位于正中央。lazer 在桌面布局中把这些值乘以 `1.6` 映射到高为 `768` 的内部舞台。向上滚动时，`HitPosition`、`LightPosition` 和 `ScorePosition` 随滚动方向垂直镜像；`ComboPosition` 是固定 HUD 坐标，不随滚动方向镜像。窗口像素坐标还会受最终 playfield 缩放影响。

| 命令 | 类型/默认 | 语义 |
|---|---|---|
| `ColumnStart` | number / 136 | 最左列起点；stable-only 约束，不能当 HitPosition |
| `ColumnRight` | number / 19 | 列最多绘制到哪里；stable-only |
| `ColumnWidth` | comma numbers / 30 | 每列宽度；键数大或按键宽时减小 |
| `ColumnSpacing` | comma numbers / 0 | 相邻列间透明间隔；完整数组为 `Keys-1` 个值 |
| `ColumnLineWidth` | comma numbers / 2 | 列边界宽度；完整数组为 `Keys+1` 个值 |
| `StageSeparation` | number / 40 | 分割舞台间距；仅 stable 渲染消费 |
| `ComboPosition` | integer / 111 | Mania combo 计数器的纵向坐标；`240` 为中央 |
| `HitPosition` | integer / 402 | 判定线的纵向坐标；影响 StageHint/LightingN/LightingL。lazer 将配置值钳制到 `240..480` |
| `LightPosition` | integer / 413 | StageLight 的纵向坐标；`240` 为中央，只影响 StageLight |
| `WidthForNoteHeightScale` | number / 最小列宽比例 | 列宽不同时统一 note 高度 |

在 lazer 的单舞台桌面布局中，轨道宽度只由列宽和列间距决定：

```text
legacy 单位轨道宽 = sum(ColumnWidth[i]) + sum(ColumnSpacing[i])
lazer 内部轨道宽 = legacy 单位轨道宽 * 1.6
```

`ColumnLineWidth` 绘制在各列内部，不增加轨道布局宽度；`StageLeft`/`StageRight` 位于轨道外侧，也不加入上述宽度。多舞台时按每个实际舞台分别计算。不要只改 `ColumnStart` 而忽略逐列宽度、间距、StageLeft/Right 和目标分辨率。

### 舞台资源布局

- `StageBottom` 未配置时回退到根目录 `mania-stage-bottom`；lazer 不把它拉伸到轨道宽，而是在纹理自身尺寸上统一缩放 `1.6`。向下滚动使用底部居中锚点，向上滚动使用顶部居中锚点，且不受 `HitPosition` 控制。
- 要让 `StageBottom` 宽度恰好等于单个轨道，SD 原图宽度应等于 `sum(ColumnWidth) + sum(ColumnSpacing)`；`@2x` 原图宽度应为该值的两倍。
- 向下滚动时，若可见内容从 PNG 第一行开始，SD 图的画布顶部比例为 `1 - H / 480`，`@2x` 图为 `1 - H / 960`。透明边存在时必须再检查 alpha 包围框。
- `StageLeft`/`StageRight` 在 lazer 中保持图片宽度并单独把高度缩放到舞台高度；它们位于轨道两侧，不遮挡轨道外的整屏背景。
- 未显式配置的路径依次回退到 `mania-stage-hint`、`mania-stage-left`、`mania-stage-right` 和 `mania-stage-light`。

### 颜色

| 命令 | 类型 | 语义 |
|---|---|---|
| `Colour#` | RGBa | 第 # 列背景颜色，# 从 1 开始 |
| `ColourLight#` | RGBa | 第 # 列闪光；lazer alpha 行为见 `stable-vs-lazer.md` |
| `ColourBarline` | RGBa | 小节线颜色 |
| `ColourColumnLine` | RGBa | 分隔线颜色 |
| `ColourJudgementLine` | RGB | 判定线颜色 |
| `ColourBreak` | RGB | 断连 combo 颜色 |
| `ColourHold` | RGBa | 长按 combo 颜色；lazer 当前不消费 |
| `ColourKeyWarning` | RGB | 按键绑定提示颜色；stable |
| `BarlineHeight` | number / 1.2 | 小节线宽度 |

### 资源路径

遇到“投/投皮”先读 `mania-hold-body.md`。数据库标准映射为 `H=长按头`、`L=长按体/投皮`、`T=长按尾`；投皮生成器输出 `mania-noteNL.png` 一类图片（如 `mania-note1L.png`），编辑已有皮肤仍检查实际 path 和图片。

| 命令 | 作用 |
|---|---|
| `KeyImage#`, `KeyImage#D` | 第 # 列未按下/按下按键 |
| `NoteImage#` | 第 # 列普通音符 |
| `NoteImage#H/L/T` | 数据库描述为第 # 列长按头/体/尾；实际任务必须核对 path，不能据字母后缀直接覆盖 |
| `LightingN`, `LightingL` | 单音符/长按闪光 |
| `StageBottom`, `StageHint`, `StageLeft`, `StageRight`, `StageLight` | 舞台资源 |
| `WarningArrow` | 警告箭头，stable |
| `Hit0`, `Hit50`, `Hit100`, `Hit200`, `Hit300`, `Hit300g` | 判定图片 |

路径修改后必须检查普通图、H/L/T、`@2x`、动画帧和默认 fallback。

### 行为与翻转

| 命令 | 语义 |
|---|---|
| `NoteBodyStyle` | 通用长按体样式；stable 为 0 拉伸、1 从顶部叠加、2 从底部叠加；lazer 为 0 拉伸，非 0 统一呈现类似从顶部叠加的独立效果 |
| `NoteBodyStyle#` | 逐列样式；stable 的 per-column 规则，不能套用通用值 |
| `NoteFlipWhenUpsideDown` 及 `#/#H/#L/#T` | upside-down 时音符和 H/L/T 翻转，stable 重点 |
| `KeyFlipWhenUpsideDown` 及 `#/#D` | upside-down 时按键翻转，stable 重点 |
| `UpsideDown` | 舞台上下颠倒，stable |
| `KeysUnderNotes` | 按键是否被音符覆盖 |
| `JudgementLine` | StageHint 上方是否再绘制一线 |
| `SplitStages` | stable 的舞台分割字段；lazer 只解析/导出，不用于创建多舞台 |
| `SeparateScore` | 判定结果是否只显示在得分舞台；stable |
| `SpecialStyle` | stable 旧特殊键样；lazer 当前只保留导入/导出 |

### 帧率与得分

| 命令 | 语义 |
|---|---|
| `LightFramePerSecond` | StageLight 帧率；lazer 未配置 60，值 <=0 时 24 |
| `ScorePosition` | 判定图在 480 高 legacy 坐标系中的纵向坐标；向下滚动时 `0` 顶部、`480` 底部、`240` 中央，向上滚动时垂直镜像；stable 默认 325，lazer 默认 300 |
| `ComboBurstStyle` | 0 左、1 右、2 两侧随机；右侧图像会翻转，stable |
