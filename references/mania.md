# osu!mania 处理手册

确认客户端和 keycount 后，运行 `osu-skin mania-analyze "<皮肤目录或 skin.ini>" --keys <N> --client stable|lazer --dependencies --json`。读取分析结果中的实际 path 后，再对目标图片运行 `osu-skin image-inspect "<路径>" --json`。遇到“投/投皮”时改读 `mania-hold-body.md`。

## 任务前置

1. 确认客户端；目录没有 `skininfo.json` 且用户未声明时先提问。
2. 确认 keycount。用 `skin.ini` 中的 `Keys: N` 选择段；不要默认第一个 `[Mania]` 或默认 4K。
3. 确认用户修改的是皮肤视觉还是谱面数据。皮肤不能改变谱面 note 的出现时间、hold duration 或 BPM。
4. 读取目标 `[Mania]` 段、同 keycount 的路径、默认文件、`@2x` 和动画帧。
5. 用户提到“投/投皮/投的长度/投 50px/球皮/菱形皮/渐变皮”时停止本文件的通用判断，先读取 `mania-hold-body.md`。
6. 用户描述 lazer 中的列宽换算、图片压扁、拉长或投皮重复时读取 `lazer-image-scaling.md`。

## 非投皮语境的几何消歧

| 症状/说法 | 真实对象 | 检查 | 可修改内容 |
|---|---|---|---|
| “长条持续时间太长/太短” | 谱面 hold duration | `.osu` 谱面数据 | 不在 skin 中修改；告知需要编辑谱面 |
| “LN 看起来太粗” | LN 体纹理和列几何 | 实际 H/L/T path、`NoteBodyStyle`、`ColumnWidth`、`WidthForNoteHeightScale` | 先确认投皮映射，再修改图片、体样式或列宽 |
| “判定线太高/太低” | 判定线坐标 | `HitPosition`、`StageHint`、`LightingN/L`、截图 | 修改 `HitPosition` 或舞台资源 |
| “轨道太长/可视区域不对” | 舞台和游戏布局 | `StageBottom/Left/Right`、`StageSeparation`、`UpsideDown`、客户端 | 修改舞台字段/图片，不能只拉伸一张图 |
| “note/receptor 太大/太小” | 图片像素尺寸 | `NoteImage#`、`KeyImage#`、SD/HD、列宽 | 修改资源组，保持 `@2x` 比例 |

本表只处理用户没有使用“投/投皮”等明确领域词的情况。如果一句话同时可能对应两项，先提问，不要盲改。

## 列几何

### 参数

- `ColumnStart`：最左列起点，stable 重点；不是判定线高度。
- `ColumnWidth`：每列宽度，可以是单值或逗号分隔的逐列值。
- `ColumnSpacing`：列间透明间距；逐列数量必须与布局语义一致。
- `ColumnLineWidth`：列分隔线宽度。
- `ColumnRight`：列最多绘制位置，stable 重点。
- `StageSeparation`：分割舞台间距，stable 重点。
- `SplitStages`：多键舞台是否拆分；键数大于 1 时可能被客户端强制。
- `WidthForNoteHeightScale`：列宽不同时统一 note 高度的比例。

### 居中计算

1. 读取所有列宽和列间距，不把一个 `ColumnWidth` 值当成总宽。
2. 计算可绘制总宽和当前中心。
3. 以目标 playfield 中心计算新的 `ColumnStart`。
4. 保持列宽、间距、分隔线和舞台边界的关系。
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

## 长按视觉与路径映射

- 数据库标准映射为 `H=长按头`、`L=长按体/投皮`、`T=长按尾`。投皮生成器输出 `mania-noteNL.png` 一类图片（如 `mania-note1L.png`）；编辑已有皮肤时仍读取实际 path 和图片。
- 用户使用“投/投皮”时按 `mania-hold-body.md` 处理，并明确本次使用的 `NoteImage#L` path。
- 头、体、尾缺失时可能按客户端/皮肤规则回退；复制后必须报告实际回退。
- `NoteBodyStyle`：通用体样式。lazer 有效值 0、2、3、4；值 1 不可解析；版本 `<2.5` 默认 0，`>=2.5` 默认 3。
- `NoteBodyStyle#`：逐列体样式，不能把通用字段的值表直接套用到它。
- `WidthForNoteHeightScale` 会改变 note 高度统一策略；改列宽后要复检 LN 体和 head/tail 对齐。
- `NoteFlipWhenUpsideDown#H/L/T` 只处理对应部件，不等于把所有 PNG 旋转。

## 判定线、灯光和得分

- `HitPosition` 控制判定线及部分 StageHint/Lighting 的垂直位置。
- `LightPosition` 只用于 StageLight；不要用它替代 HitPosition。
- `LightFramePerSecond` 控制 StageLight；lazer 未配置时 60，值 <=0 时按 24。
- `ScorePosition` 控制判定结果高度；stable 默认 325，lazer 默认 300。
- `JudgementLine` 控制 StageHint 上方是否再画一条线；lazer 未配置默认显示。

## 合并流程

1. 列出源和目标皮肤，分别确认客户端。
2. 让用户指定 keycount；没有指定就先询问。
3. 生成依赖清单和冲突清单。
4. 在新目录复制目标皮肤。
5. 复制源 keycount 资源；冲突文件使用前缀或目录，并同步改 path。
6. 在目标 `skin.ini` 插入/更新对应 `Keys: N` 段，保留其他段。
7. 合并 `Name`/`Author` 时保留所有来源。
8. 检查 path、SD/HD、动画、H/L/T、列数量、几何和客户端差异。
9. 生成变更清单；没有运行客户端时不要宣称游戏内一定正确。
