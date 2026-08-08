# osu!lazer 图片非等比缩放诊断

仅在用户明确使用 lazer，且图片出现压扁、拉长、比例错误、重复或尺寸异常时读取本文件。先运行 `osu-skin image-inspect "<图片或皮肤目录>" --transparent-rows --json`，再把原图尺寸与下表的实际渲染约束比较。

## 单位和前置检查

- 将 Mania 的实际渲染列宽按 `ColumnWidth * 1.6` 计算；`ColumnWidth: 30` 对应 48px。
- 将表中推荐尺寸视为 1x。处理 `@2x` 时通常把宽高都扩大一倍；`NoteImage{n}L` 不按普通图片规则盲目翻倍，先确认 `NoteBodyStyle` 和实际 `NoteImage#L` path。
- 先检查客户端、实际加载的 SD/`@2x`、图片原始宽高、目标 `skin.ini` path、`ColumnWidth`、`WidthForNoteHeightScale` 和 `NoteBodyStyle`。
- 不从社区表述复制 `NoteBodyStyle` 数值。数据库当前记录 lazer 有效值为 `0,2,3,4`，值 `1` 无法解析；未设置时还受皮肤 `Version` 影响。只有确认实际样式后才套用对应缩放规则。

## 缩放速查

| 图片/字段 | lazer 缩放方式 | 常见症状 | 1x 建议 |
|---|---|---|---|
| `taiko-bar-right` | 拉伸至右侧区域宽度和 200 内部单位高，X/Y 独立缩放 | 宽屏下明显横向拉长 | 宽至少 1024，高 200 |
| `taiko-bar-right-glow` | 与 `taiko-bar-right` 相同，Kiai 时渐显 | glow 与底图比例不一致 | 与底图同尺寸 |
| `taiko-roll-middle` | 拉伸到 DrumRoll 首尾间的整个矩形，高约 128px | 窄竖条被横向拉糊 | 至少 512x128，横向纹理连续 |
| `mania-stage-left` / `StageLeft` | 宽保持原值，高拉到当前舞台高度 | 侧边框纵向变形 | 高 768；宽按设计取 50-200 |
| `mania-stage-right` / `StageRight` | 与 `StageLeft` 相同 | 侧边框纵向变形 | 同上 |
| `mania-stage-hint` / `StageHint` | 先拉到舞台全宽，再把 Y 约放大 1.442 倍 | 判定提示比原图更高 | 宽至少覆盖舞台；原图高约为目标显示高 / 1.442 |
| `mania-stage-light` / `StageLight` | 横向压到列宽；松手时 Y 缩为 0 | 闪光过窄或横向压扁 | 宽等于实际列宽，默认 48；高至少 200 |
| `KeyImage{n}` / `KeyImage{n}D` | 宽强制等于列宽，高保持图片原高 | 128x128 按键显示成 48x128 | 宽等于实际列宽；高等于期望显示高 |
| `NoteImage{n}` | 宽适配列宽；高由 `WidthForNoteHeightScale` 决定 | note 横纵比例不一致 | 使用正方形素材；让高度缩放基准与列宽一致 |
| `NoteImage{n}H` | 与普通 note 相同；缺失时可能回退普通 note | Hold 头与 note 尺寸不一致 | 与普通 note 同尺寸并检查回退 |
| `NoteImage{n}T` | 与普通 note 相同，并额外进行 Y 翻转 | 尾部方向与预期相反 | 与普通 note 同尺寸；不要预先重复翻转 |
| `NoteImage{n}L` Stretch 样式 | 宽拉到列宽，高拉到当前 Hold body 高度 | 随 LN 长度纵向变形 | 宽等于实际列宽；纵向纹理设计为可拉伸 |
| `NoteImage{n}L` RepeatTop 样式 | 宽拉到列宽；源图不足目标纵向范围时重复采样 | 投皮图案重复、宽度被拉伸 | 宽等于实际列宽；需要单次完整映射时使用 32800px 高 |
| 按键计数器 | X 固定约放大 1.05，Y 不变 | 字体略宽 | 按正常字体设计，通常无需补偿 |

## 诊断顺序

1. 用 `image-inspect` 记录实际加载图片的宽高和 SD/`@2x` 配对。
2. 读取数据库的 `suggested_size`、`hd_supported`、origin 和目标客户端。
3. 对 Mania 运行 `osu-skin mania-analyze "<皮肤目录>" --keys <N> --client lazer --dependencies --json`，确认实际 path 与列宽字段。
4. 把 `ColumnWidth * 1.6` 与图片宽度比较；不相等时先判断横向拉伸是否就是症状来源。
5. 对普通 note 比较 `WidthForNoteHeightScale` 与列宽；不相等时预期出现非等比缩放。
6. 对投皮确认 `NoteBodyStyle` 的实际值和皮肤版本；需要修改顶部透明区时返回 `mania-hold-body.md`，不要把缩放问题当成“投的长度”。
7. 只在确认目标尺寸后运行 `osu-skin image-transform "<图片>" --operation scale --output "<输出>" --width <px> --height <px> --dry-run`。

报告原图尺寸、实际列宽、预计显示尺寸、X/Y 缩放方向、触发字段、SD/`@2x` 选择和建议目标尺寸。没有客户端截图时，将显示结果标记为静态推断。
