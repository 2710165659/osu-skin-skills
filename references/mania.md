# osu!mania 处理手册

工具用途：`mania-analyze` 只读解析指定 `Keys:N` 小节的字段、实际 path、默认回退、几何和资源依赖；`image-inspect` 只读检查被引用图片的尺寸、alpha、SD/`@2x` 和动画。确认客户端和 keycount 后，运行 `osu-skin mania-analyze "<皮肤目录或 skin.ini>" --keys <N> --client stable|lazer --dependencies --json`。读取分析结果中的实际 path 后，再对目标图片运行 `osu-skin image-inspect "<路径>" --json`。遇到“投/投皮”时改读 `mania-hold-body.md`。完整工具选择见 `tools.md`。

## 任务前置

客户端、输入类型、keycount 和写入范围由 `start-here.md` 统一闸门负责；本文件只定义 Mania 领域的对象和依赖。进入本文件后：

1. 用 `skin.ini` 中的 `Keys: N` 选择目标段，不默认第一个段或 4K。
2. 区分皮肤视觉与谱面数据；皮肤不能改变 note 时间、hold duration 或 BPM。
3. 读取该段实际 path、默认回退、`@2x` 和动画帧。
4. 遇到投皮、lazer 缩放或面尾分支时，读取 `mania-hold-body.md`、`lazer-image-scaling.md` 或 `stable-vs-lazer.md`，并执行对应文件中的修复流程。

## 非投皮语境的几何消歧

| 症状/说法 | 真实对象 | 检查 | 可修改内容 |
|---|---|---|---|
| “长条持续时间太长/太短” | 谱面 hold duration | `.osu` 谱面数据 | 不在 skin 中修改；告知需要编辑谱面 |
| “LN 看起来太粗” | LN 体纹理和列几何 | 实际 H/L/T path、`NoteBodyStyle`、`ColumnWidth`、`WidthForNoteHeightScale` | 先确认投皮映射，再修改图片、体样式或列宽 |
| “判定线太高/太低” | 判定线坐标 | `HitPosition`、`StageHint`、`LightingN/L`、相关资源和用户描述 | 修改 `HitPosition` 或舞台资源 |
| “轨道太长/可视区域不对” | 舞台和游戏布局 | `StageBottom/Left/Right`、`StageSeparation`、`UpsideDown`、客户端 | 修改舞台字段/图片，不能只拉伸一张图 |
| “note/receptor 太大/太小” | 图片像素尺寸 | `NoteImage#`、`KeyImage#`、SD/HD、列宽 | 修改资源组，保持 `@2x` 比例 |

本表只处理用户没有使用“投/投皮”等明确领域词的情况。如果一句话同时可能对应两项，先提问，不要盲改。

## 列几何

### 480 高纵向坐标

`HitPosition`、`LightPosition`、`ScorePosition` 和 `ComboPosition` 的配置值以高为 `480` 的 legacy 坐标系表示。向下滚动时 `0` 在顶部、`480` 在底部，`240` 正好在中央；lazer 桌面舞台内部按 `值 * 1.6` 映射到 `768` 高度。向上滚动时前三项随滚动方向垂直镜像，`ComboPosition` 作为 HUD 位置不镜像。lazer 对 `HitPosition` 额外按 `240..480` 范围处理，其他三项没有同样的范围限制。

### 参数

- `ColumnStart`：最左列起点，stable 重点；不是判定线高度。
- `ColumnWidth`：每列宽度，可以是单值或逗号分隔的逐列值。
- `ColumnSpacing`：相邻列之间的透明间距；完整数组为 `Keys-1` 个值。
- `ColumnLineWidth`：列边界线宽度；完整数组为 `Keys+1` 个值（每列读取左边界 `i` 和右边界 `i+1`）。
- `ColumnRight`：列最多绘制位置，stable 重点。
- `StageSeparation`：分割舞台间距，仅 stable 渲染消费。
- `SplitStages`：stable 的舞台拆分字段；lazer 只为导入/导出稳定性解析，不据此拆分舞台。
- `WidthForNoteHeightScale`：列宽不同时统一 note 高度的比例。

### 居中计算

1. 读取所有列宽和列间距，不把一个 `ColumnWidth` 值当成总宽。
2. 按 `sum(ColumnWidth) + sum(ColumnSpacing)` 计算单个舞台的轨道总宽；lazer 内部尺寸再乘 `1.6`。
3. 以目标 playfield 中心计算新的 `ColumnStart`。
4. 保持列宽、间距、分隔线和舞台边界的关系；`ColumnLineWidth` 在列内绘制，`StageLeft/Right` 位于轨道外侧，二者都不加入轨道布局宽度。
5. 输出改前/改后列边界；如果只改 `ColumnStart` 仍会溢出，必须说明。

## 资源依赖

对一个 keycount 做复制或混合时收集：

1. `Keys: N` 段的共享字段；
2. `NoteImage#`、`NoteImage#H/L/T`；
3. `KeyImage#`、`KeyImage#D`；
4. `LightingN`、`LightingL` 及逐列宽度；
5. `StageBottom`、`StageHint`、`StageLeft`、`StageRight`、`StageLight`；
6. `Hit0/50/100/200/300/300g` 和 `WarningArrow`；
7. 路径未显式指定时的默认文件名；
8. 每个 path 的 SD、`@2x`、`-0..n` 动画帧；
9. 客户端需要的 `skin.ini` 版本、flip、score 和 lighting 字段。

只复制 `[Mania]` 文本会遗漏默认 receptor、LN tail、动画或 HD 文件，这是合并失败的主要来源。

### 多 keycount 的 path 与占位图

同一皮肤可以包含多个重复的 `[Mania]` 段；每个 `Keys:N` 都是独立的资源消费者。必须对每个 keycount 单独读取实际 `skin.ini` path，再解析根目录或子目录中的 SD、`@2x` 和动画帧。`mania-hit300`、`mania-lightingN` 等同名文件只在 path 相同且被同一小节引用时才属于同一资源组；不能因为文件名相同就跨 keycount 合并。

运行 `mania-analyze --dependencies --json` 时，记录每个资源的 `relative_path`、`location`、`resolved_base`、`base_exists`、`hd_exists` 和 `base_alpha.status`。`fully_transparent` 是“存在且全透明”的证据，可能是关闭灯光或保留布局的占位图；不要把它当成缺失，也不要自动用其他目录的可见同名图替换。需要改变该 keycount 的视觉时，复制可见资源并只修改该 `Keys:N` 小节的对应字段。

## 长按视觉与路径映射

- 数据库标准映射为 `H=长按头`、`L=长按体/投皮`、`T=长按尾`。投皮生成器输出 `mania-noteNL.png` 一类图片（如 `mania-note1L.png`）；编辑已有皮肤时仍读取实际 path 和图片。
- 用户使用“投/投皮”时按 `mania-hold-body.md` 处理，并明确本次使用的 `NoteImage#L` path。
- 头、体、尾缺失时可能按客户端/皮肤规则回退；复制后必须报告实际回退。
- `NoteBodyStyle`：通用体样式。stable 为 0 拉伸、1 从顶部叠加、2 从底部叠加；lazer 为 0 拉伸，所有可解析的非 0 整数统一呈现类似从顶部叠加的独立效果。lazer 未配置时版本 `<2.5` 使用拉伸，`>=2.5` 使用非 0 分支。
- `NoteBodyStyle#`：逐列体样式，不能把通用字段的值表直接套用到它。
- `WidthForNoteHeightScale` 会改变 note 高度统一策略；改列宽后要复检 LN 体和 head/tail 对齐。
- `NoteFlipWhenUpsideDown#H/L/T` 只处理对应部件，不等于把所有 PNG 旋转。
- 面尾归属必须看实际 T 的 alpha：`NoteImage#T` 全透明时按投皮处理，可见收尾来自 `NoteImage#L` cap；T 存在可见像素时才按普通 Hold Tail 处理。lazer 的非 0 `NoteBodyStyle` 统一呈现类似从顶部叠加的效果，不能按内部枚举名推断独立的顶部或底部行为。

## 判定线、灯光和得分

- `HitPosition` 控制判定线及部分 StageHint/Lighting 的垂直位置；lazer 将配置值钳制到 `240..480`，且不用于定位 `StageBottom`。
- `LightPosition` 只用于 StageLight；不要用它替代 HitPosition。
- `LightFramePerSecond` 控制 StageLight；lazer 未配置时 60，值 <=0 时按 24。
- `ScorePosition` 控制判定结果位置；stable 默认 325，lazer 默认 300。
- `ComboPosition` 控制 Mania combo 计数器位置，默认 111；lazer 将其作为固定的顶部 HUD 坐标，不随滚动方向镜像。
- `JudgementLine` 控制 StageHint 上方是否再画一条线；lazer 未配置默认显示。

## 舞台前景和边框

- `StageBottom` 未配置时回退 `mania-stage-bottom`。lazer 按纹理自身尺寸统一缩放 `1.6`，不拉伸到轨道宽；向下滚动底部居中、向上滚动顶部居中。
- 单舞台精确同宽时，StageBottom 的 SD 宽度取 `sum(ColumnWidth) + sum(ColumnSpacing)`，`@2x` 宽度取其两倍。它的位置和遮挡高度由实际 PNG 高度及 alpha 决定，不由 `HitPosition` 决定。
- `StageLeft`/`StageRight` 分别以轨道左/右边缘为锚点，图片朝轨道外侧展开；宽度保持原值，高度独立拉伸到舞台高度。
- 未配置的 `StageHint`、`StageLeft`、`StageRight`、`StageLight` 分别回退 `mania-stage-hint`、`mania-stage-left`、`mania-stage-right`、`mania-stage-light`。

## 合并提示

执行 Mania 混皮时，读取 `merge-recipes.md` 获取混皮顺序、共享资源矩阵和输出策略；本文件提供该流程所需的 Mania 依赖字段。
