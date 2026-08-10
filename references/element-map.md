# 元素、文件名和资源组映射

工具用途：`db-query` 返回元素、标签、客户端和专属详情；`image-inspect` 只读核对图片实际指标；`audio-inspect` 只读核对音频格式和族。定位元素时，运行 `osu-skin db-query "<文件名、命令或描述>" --json`。核对图片时运行 `osu-skin image-inspect "<路径>" --json`；核对音频时运行 `osu-skin audio-inspect "<路径>" --json`。处理 Mania 逐列 path 时，改读 `mania.md` 并运行其中的命令。完整工具选择见 `tools.md`。

## 数据库查询协议

`db-query` 普通搜索已经返回主表、专属详情、标签定义和 `term_matches`。需要跨元素或消费者矩阵时，运行 `database.md` 中对应的 SQL 配方。

用户给文件名时先标准化：

1. 去掉目录和扩展名；
2. 去掉末尾 `@2x`；
3. 去掉动画帧的 `-0`、`-1`、`1` 等后缀，但保留可能属于元素名的数字；
4. 分别尝试 `filename`、`id` 和 `command`；
5. 候选不唯一时返回候选和区分方法，不强行选择。

## 返回元素时必须说明

- 实际文件名或文件名模式；
- 图片/音频/skin.ini 类型；
- category、subcategory 和适用模式；
- `client` 和用户目标客户端是否匹配；
- 图片尺寸、origin、blend mode、HD 支持和谱面覆盖；
- 动画帧模式、FPS、循环和 base rule；
- 音频格式、循环、supporter 和谱面覆盖；
- path 字段的 section、类型、默认值和回退；
- 与该元素一起出现的资源组和常见故障。

## 常用元素

### std 游玩资源

| 用户说法 | 重点元素 | 一起检查 |
|---|---|---|
| 打击圈/圆圈 | `hitcircle`, `hitcircleoverlay`, `approachcircle` | `[Fonts] HitCirclePrefix/Overlap`、数字图、HD |
| 滑条 | `sliderb`, `sliderfollowcircle`, `sliderendcircle`, `sliderscorepoint`, `reversearrow` | `SliderBorder`、`SliderBall`、球动画、谱面覆盖 |
| 光标和尾迹 | `cursor`, `cursormiddle`, `cursortrail` | CursorCentre/Expand/Rotate、帧组、HD；lazer 中皮肤光标只在 std 游玩时渲染，其他模式和界面使用原生光标 |
| 跟随点 | `followpoint`, `followpoint-0..n` | `has_0_hides_base`、帧序、blend mode |
| 转盘 | `spinner-background`, `spinner-circle`, `spinner-approachcircle`, `spinner-metre`, `spinner-rpm` | 新旧转盘样式、Spinner 配置、stable/lazer |
| 打击结果 | `hit0`, `hit50`, `hit100`, `hit300`, `hit100k`, `hit300k` | 动画 base rule、数字前缀、谱面覆盖 |

### taiko、catch 和菜单

- Taiko：按 `太鼓模式` 标签筛选，不要从 std 同名文件推断鼓面资源。
- Catch：水果及 overlay、catcher idle/fail/kiai、hyperdash 颜色和动画必须作为组检查。
- 菜单/选歌：检查 `菜单界面`、`选歌界面`、`全局界面` 标签以及 supporter/client 限制。
- 结算：区分大号 ranking 图和 `ranking-*-small.png`；lazer 的实际覆盖范围不同。

### Mania 资源

不要只查 `mania` 目录。先从 `[Mania]` 的 `Keys: N` 和 path 字段确定：

- `NoteImage#`、`NoteImage#H/L/T`：数据库用于列音符及长按部件的字段；读取实际 path 和图片确定本皮肤映射；
- `KeyImage#`、`KeyImage#D`：未按下/按下按键；
- `LightingN`、`LightingL`、`StageLight`：闪光和舞台；
- `StageHint`、`StageLeft/Right/Bottom`：舞台边界和判定线；
- `Hit0/50/100/200/300/300g`：判定图；
- `WarningArrow`：警告箭头；
- 逐列路径、默认命名、`@2x` 和动画帧。

“投/投皮/投的长度”是特殊领域词，先读取 `mania-hold-body.md`。标准投皮输出为 `mania-noteNL.png` 一类图片（如 `mania-note1L.png`），对应 `NoteImage#L`；编辑已有皮肤仍要以实际 path 和图片为准。

## 资源组原则

资源组是混皮和诊断的基本单位：

1. 组内元素共享视觉语义、路径、尺寸或动画规则。
2. 复制组时收集 base、HD、帧、配置字段、默认回退和依赖音效。
3. 用户只点名一个文件时，先说明它可能依赖哪些同组文件；不要扩大修改范围而不告知用户。
4. 数据库标签 `谱面可自定义` 表示谱面可能覆盖皮肤文件；诊断时必须检查 beatmap skin。
5. 任意混皮或单模式替换时，先为每个候选文件族运行数据库查询；提示词里的模式名称只定义目标范围，不能定义文件归属。检查 `client`、`std模式`、`太鼓模式`、`接水果模式`、`mania模式`、`全模式`、`全局界面`、description/notes，再检查 `skin.ini` path/prefix 和其他 Mania keycount 的实际引用。目标范围外存在任何消费者、多个来源候选或数据库未知项时，说明其使用位置并单独确认覆盖。

## 找不到元素时

按顺序处理：

1. 检查当前客户端和模式是否已经确认；
2. 查询中文描述、分类、标签和官方 wiki 的同义词；
3. 检查是否是程序化 UI 或客户端自带资源；
4. 检查是否是谱面内置 skin 或 beatmap 文件；
5. 把结果标为“未确认”，请求实际文件名、路径或皮肤目录。
