# osu!lazer 图片非等比缩放诊断

工具用途：`image-inspect` 只读取得实际尺寸、alpha 和透明行；`mania-analyze` 只读取得 Mania path、keycount 和列宽；`mania-lazer-hold-body-fix`/`mania-lazer-key-fix` 才执行对应的 lazer 拉伸修复。仅在用户明确使用 lazer，或明确说皮肤从 stable 移到 lazer 后发生变形，且图片出现压扁、拉长、比例错误、重复或尺寸异常时读取本文件。迁移问题先按 `stable-vs-lazer.md` 取得皮肤文件并确认实际加载元素，再运行 `osu-skin image-inspect "<图片或皮肤目录>" --transparent-rows --json`，把原图尺寸与下表的实际渲染约束比较。用户尚未提供皮肤时先索要文件和 Mania keycount，不要直接套表给尺寸。完整工具选择见 `tools.md`。

## 单位和前置检查

- 将 Mania 的实际渲染列宽按 `ColumnWidth * 1.6` 计算；`ColumnWidth: 30` 对应 48px。
- 将表中推荐尺寸视为 1x。处理 `@2x` 时通常把宽高都扩大一倍；`NoteImage{n}L` 不按普通图片规则盲目翻倍，先确认 `NoteBodyStyle` 和实际 `NoteImage#L` path。
- 先检查客户端、实际加载的 SD/`@2x`、图片原始宽高、目标 `skin.ini` path、`ColumnWidth`、`WidthForNoteHeightScale` 和 `NoteBodyStyle`。
- 不把 stable 的 `NoteBodyStyle` 顶部/底部语义直接套到 lazer。lazer 实际只区分 `0` 拉伸和非 `0` 的独立重复/填充效果；未设置时还受皮肤 `Version` 影响。只有确认实际值后才套用对应缩放规则。
- Mania 的“尾/面尾/收尾”先按 `stable-vs-lazer.md` 检查实际 `NoteImage#T` alpha。T 全透明时可见部分属于 `NoteImage#L` 投皮 cap，不适用普通 T 的正方形尺寸和 Y 翻转建议。

## 缩放速查

| 图片/字段 | lazer 缩放方式 | 常见症状 | 1x 建议 |
|---|---|---|---|
| `taiko-bar-right` | 拉伸至右侧区域宽度和 200 内部单位高，X/Y 独立缩放 | 宽屏下明显横向拉长 | 宽至少 1024，高 200 |
| `taiko-bar-right-glow` | 与 `taiko-bar-right` 相同，Kiai 时渐显 | glow 与底图比例不一致 | 与底图同尺寸 |
| `taiko-roll-middle` | 拉伸到 DrumRoll 首尾间的整个矩形，高约 128px | 窄竖条被横向拉糊 | 至少 512x128，横向纹理连续 |
| `mania-stage-left` / `StageLeft` | 宽保持原值，高拉到当前舞台高度 | 侧边框纵向变形 | 高 768；宽按设计取 50-200 |
| `mania-stage-right` / `StageRight` | 与 `StageLeft` 相同 | 侧边框纵向变形 | 同上 |
| `mania-stage-bottom` / `StageBottom` | 不拉伸到舞台宽；按纹理尺寸统一缩放 `1.6`。向下滚动底部居中，向上滚动顶部居中 | 宽度或遮挡高度与轨道不匹配 | 单舞台同宽时 SD 宽为 `sum(ColumnWidth)+sum(ColumnSpacing)`，`@2x` 宽为其两倍；高度按目标遮挡范围设计 |
| `mania-stage-hint` / `StageHint` | 先拉到舞台全宽，再把 Y 约放大 1.442 倍 | 判定提示比原图更高 | 宽至少覆盖舞台；原图高约为目标显示高 / 1.442 |
| `mania-stage-light` / `StageLight` | 横向压到列宽；松手时 Y 缩为 0 | 闪光过窄或横向压扁 | 宽等于实际列宽，默认 48；高至少 200 |
| `KeyImage{n}` / `KeyImage{n}D` | 宽强制等于列宽，高保持图片原高 | 128x128 按键显示成 48x128 | 宽等于实际列宽；高等于期望显示高 |
| `NoteImage{n}` | 宽适配列宽；高由 `WidthForNoteHeightScale` 决定 | note 横纵比例不一致 | 使用正方形素材；让高度缩放基准与列宽一致 |
| `NoteImage{n}H` | 与普通 note 相同；缺失时可能回退普通 note | Hold 头与 note 尺寸不一致 | 与普通 note 同尺寸并检查回退 |
| 可见的 `NoteImage{n}T` | 与普通 note 相同，并额外进行 Y 翻转 | 普通 Hold Tail 方向或比例异常 | 仅在 T 已确认存在可见像素后，按普通 note 尺寸检查；不要预先重复翻转 |
| `NoteImage{n}L` Stretch 样式 | 宽拉到列宽，高拉到当前 Hold body 高度 | 随 LN 长度纵向变形 | 宽等于实际列宽；纵向纹理设计为可拉伸 |
| `NoteImage{n}L` lazer 非 0 样式 | 宽拉到列宽；源图不足目标纵向范围时按 lazer 独立逻辑重复采样，效果类似从顶部叠加 | 投皮图案重复、宽度被拉伸 | 宽等于实际列宽；需要单次完整映射时使用 32800px 高 |
| 按键计数器 | X 固定约放大 1.05，Y 不变 | 字体略宽 | 按正常字体设计，通常无需补偿 |

## 诊断顺序

1. 用 `image-inspect` 记录实际加载图片的宽高和 SD/`@2x` 配对。
2. 读取数据库的 `suggested_size`、`hd_supported`、origin 和目标客户端。
3. 对 Mania 运行 `osu-skin mania-analyze "<皮肤目录>" --keys <N> --client lazer --dependencies --json`，确认实际 path 与列宽字段。
4. 把 `ColumnWidth * 1.6` 与图片宽度比较；不相等时先判断横向拉伸是否就是症状来源。
5. 对普通 note 比较 `WidthForNoteHeightScale` 与列宽；不相等时预期出现非等比缩放。
6. 对投皮确认 `NoteBodyStyle` 的实际值和皮肤版本；需要修改顶部透明区时返回 `mania-hold-body.md`，不要把缩放问题当成“投的长度”。
7. `NoteImage#L` 和 `KeyImage#`/`KeyImage#D` 不使用通用 `image-transform` 猜尺寸；按下面的专用命令执行。其他元素只在确认目标尺寸后使用通用变换。

### StageBottom 的位置和尺寸

`StageBottom` 不使用 `HitPosition`。lazer 先按普通纹理规则加载 SD/`@2x`，再把最终图像统一缩放 `1.6`。因此在高为 `768` 的桌面舞台中：

```text
SD 显示高度 = Hraw * 1.6
@2x 显示高度 = Hraw / 2 * 1.6
向下滚动画布顶部比例：SD = 1 - Hraw / 480；@2x = 1 - Hraw / 960
```

这些公式只定位图片画布；PNG 顶部或底部有透明行时，以 alpha 包围框计算实际可见遮挡范围。图片超出舞台、移动端放大或最终 playfield 缩放时，还要结合容器裁切和实际窗口尺寸检查。

## 适配任务的强制扫描

用户要求 lazer 适配、从 stable 迁移到 lazer，或把来源皮肤混入 lazer 输出时，不以“当前没有反馈变形”为跳过理由。对输出实际会加载的资源执行以下扫描：

1. 对每个目标 Mania keycount 运行 `mania-analyze --dependencies`，按实际 path 去重收集普通 note、H/L/T、Key/KeyD、StageBottom/Hint/Left/Right/Light、LightingN/L；
2. 对每个实际图片运行 `image-inspect`，记录 SD/`@2x` 选择、宽高、alpha 和透明行；
3. 用该 keycount 的 `ColumnWidth * 1.6`、`WidthForNoteHeightScale`、`NoteBodyStyle` 与本文件缩放表计算目标尺寸；同一路径被不同列宽使用时分别计算；
4. 同时查询并检查输出中存在的 `taiko-bar-right`、`taiko-bar-right-glow`、`taiko-roll-middle` 和其他数据库/本表标记为 X/Y 独立缩放的元素；
5. 确认会造成非预期拉伸时，在新输出中修复。L 使用 `mania-lazer-hold-body-fix`，Key/KeyD 使用 `mania-lazer-key-fix`；其他元素在数据库尺寸和目标画布均已确定后处理；
6. 修复后重新运行依赖与图片检查。未检查、无法由现有素材恢复或仍依赖客户端拉伸的项目必须逐项报告，不能写“lazer 适配完成”。

当症状位于 Mania 长按的面尾时，在第 3 步后先检查实际 T 的 alpha：T 全透明则保持透明，并检查 L 的 cap、宽高和 lazer 非 0 样式的重复效果；T 可见才继续普通 T 的 Y 翻转和高度缩放。不要按内部枚举名在多个非 0 值之间试错，因为当前 lazer 不实现彼此独立的顶部/底部渲染行为。

## 投皮 L 拉伸修复

确认 T 全透明、实际 L path、有效 `NoteBodyStyle` 和对应列的 `ColumnWidth` 后，先运行：

```powershell
osu-skin mania-lazer-hold-body-fix "<NoteImage#L PNG>" --column-width <值> --output "<输出 PNG>" --dry-run --json
```

命令计算 `target_width = round(ColumnWidth * 1.6)`、`target_height = 32800`，再执行：

1. 按目标宽度用 Lanczos3 等比缩放原图；
2. 缩放后高度大于 32800 时保留顶部并裁剪底部；
3. 缩放后高度小于 32800 时，取输入原图底部最多 1000 行，按同一倍率缩放后循环平铺到 32800；
4. 输出固定为目标宽度 x 32800。

## Key / KeyD 拉伸修复

从 `mania-analyze` 获取实际 `KeyImageN`/`KeyImageND` 和该列 `ColumnWidth`，逐个文件先运行：

```powershell
osu-skin mania-lazer-key-fix "<Key PNG>" --column-width <值> --output "<输出 PNG>" --dry-run --json
```

命令扫描 alpha>0 的主体包围框；目标总宽为 `round(ColumnWidth * 1.6)`，输入文件名以 `@2x` 结尾时再乘 2。它裁出主体，以“目标总宽减原左侧留白”为主体目标宽进行 Lanczos3 等比缩放，删除顶部留白，保留左侧和底部留白的原像素数量。输出高度为缩放后主体高度加原底部留白高度；全透明图片返回 skipped，不写输出。

如果同一实际 path 被不同列宽的多列共享，一个输出不能同时匹配多个目标宽度。为每种列宽生成独立文件并更新对应 path，或者先向用户确认统一采用哪个列宽；不要对同一路径连续覆盖。

## 适用边界

两个命令会修复“未变形原始素材因为 lazer 目标尺寸而被拉伸”的情况。它们不能修复“目标外观已经由 stable 客户端拉伸形成，再要求从现有 PNG 自动适配 lazer”的情况，因为 PNG 不包含 stable 拉伸后的原始设计信息。遇到该情况不要执行脚本并声称已适配。

报告原图尺寸、实际列宽、预计显示尺寸、X/Y 缩放方向、触发字段、SD/`@2x` 选择和建议目标尺寸。没有客户端实测时，将显示结果标记为静态推断。
