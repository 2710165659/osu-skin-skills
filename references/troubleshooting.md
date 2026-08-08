# osu! skin 故障诊断树

按症状选择命令：元素不生效时运行 `osu-skin db-query "<元素>" --client <客户端> --json`；图片异常时运行 `osu-skin image-inspect "<路径>" --transparent-rgb --json`；Mania 异常时读取 `mania.md`；投皮长度或重复时读取 `mania-hold-body.md`。

用户明确使用 lazer 且症状是图片非等比缩放或重复时，读取 `lazer-image-scaling.md`；“投的长度”修改仍读取 `mania-hold-body.md`。

## 目录

- [诊断格式](#诊断格式)
- [元素完全没有变化](#元素完全没有变化)
- [元素变成默认皮肤](#元素变成默认皮肤)
- [透明 PNG 白边或黑边](#透明-png-白边黑边)
- [动画不播放或叠加错误](#动画不播放或叠加错误)
- [std 数字重叠或 instafade](#std-数字重叠instafade)
- [Mania 按键或音符缺失](#mania-按键音符缺失)
- [Mania 位置或长条异常](#mania-位置长条异常)
- [音频没声音](#音频没声音)
- [.osk 导入失败](#osk-导入失败)

## 诊断格式

先记录：客户端、皮肤根目录、当前选中皮肤、游戏模式、keycount、运行分辨率、谱面/谱面皮肤、问题截图和复现步骤。每个原因标记 `已确认`、`客户端规则`、`高概率` 或 `待确认`。

## 元素完全没有变化

按顺序检查：

1. 当前 osu! 选择的是否是修改后的皮肤；
2. stable/lazer 是否已确认；
3. 当前模式是否匹配元素标签；
4. 文件名、扩展名、路径和大小写是否正确；
5. 元素是否由该客户端实际消费；
6. 是否存在 `@2x`/SD 另一版本导致看到旧图；
7. 是否被谱面 skin、程序化 UI 或默认资源覆盖；
8. 是否需要刷新/重载；
9. 图片是否损坏或格式不支持。

不要先建议“重启游戏”；先给出文件和客户端证据。

## 元素变成默认皮肤

可能原因：

- 引用 path 不存在；
- 文件名模式、动画帧或 `-0` 不符合加载规则；
- 文件只有 SD/HD 的另一版本；
- 客户端不支持该元素；
- 图片/音频解码失败；
- 用户修改的是大号 ranking 图，但 lazer 实际使用默认资源；
- 删除资源触发 fallback。

先检查真实路径和数据库 `client`，再给修复。

## 透明 PNG 白边/黑边

检查：

1. 是否存在 alpha 通道；
2. alpha=0 和半透明像素数量；
3. alpha=0 的 RGB 是否主要为白色/黑色；
4. 是否使用 Additive blend；
5. 是否从 HD 缩到 SD 时发生颜色扩散；
6. 是否裁切改变了 origin/视觉中心。

白边通常优先修透明边缘颜色或 edge bleed；黑边要检查抠图和预乘 alpha。处理前备份并输出像素变更统计。

## 动画不播放或叠加错误

检查 base、`-0`、帧起始、连续性、帧尺寸、FPS、循环和客户端 rule。stable hitXX 的 `always_load_base` 与 lazer 的行为可能不同；不要只按文件存在性下结论。

## std 数字重叠/instafade

同时检查：

- `HitCirclePrefix` 是否指向预期数字；
- 数字图片是否有宽度变化；
- `HitCircleOverlap` 是否适合当前数字宽度；
- 是否在 HD/SD 之间切换；
- `HitCircleOverlayAboveNumber` 是否改变图层；
- 运行分辨率和生成器的 overlap 假设。

## Mania 按键/音符缺失

检查：

1. `Keys: N` 是否选择了正确段；
2. `KeyImage#`/`NoteImage#` 的 `#` 是否从 1 开始；
3. path 指向的普通图、`@2x` 和动画是否存在；
4. H/L/T 是否只复制了头和体而遗漏尾；
5. 默认命名回退是否被错误路径覆盖；
6. `KeysUnderNotes`、flip、stage 和客户端是否造成“看起来缺失”。

## Mania 位置/长条异常

用户说“投/投皮/投的长度/投 50px”时先读 `mania-hold-body.md`，不要把它归入模糊的“长条长度”。“投 50px”通常要求把投皮图片顶部连续透明区改为 50 行，而不是修改 `HitPosition` 或谱面 hold duration。

- 列偏移：检查 `ColumnStart`、逐列 `ColumnWidth`、`ColumnSpacing`、`ColumnLineWidth`、StageLeft/Right。
- 判定线偏移：检查 `HitPosition`、`StageHint`、`JudgementLine`。
- 得分判定偏移：检查 `ScorePosition` 及 stable/lazer 默认差异。
- 投皮重复/不连续：检查 `NoteBodyStyle`、实际 `NoteImage#L` path、源图高度、顶部透明行、`WidthForNoteHeightScale` 和 H/L/T 尺寸。
- 长条方向错误：检查 `UpsideDown` 和 Note/Key flip 字段，不要直接旋转全部资源。

## 音频没声音

分开检查：

- 游戏是否支持该元素和格式；
- 预览工具是否能解码该格式；
- 文件是否真的为扩展名所称的 codec；
- sample set 是否完整；
- 谱面是否覆盖 hitsound；
- 删除文件是否触发默认 fallback；
- 循环音效首尾是否有 click/DC offset。

## `.osk` 导入失败

检查压缩包根是否直接包含 `skin.ini`/资源、是否多嵌套一层目录、文件名编码、损坏文件、重复路径和目标客户端。打包后先解包回读，再告诉用户导入结果。
