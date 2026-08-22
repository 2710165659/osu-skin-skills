# 混皮、资源组和 lite 配方

工具用途：`db-query` 只读建立元素和消费者矩阵；`mania-analyze` 只读解析每个 Mania keycount 的实际 path；`image-inspect` 只读核对图片族；本工具集没有自动混皮命令，复制、重命名和 `skin.ini` 回写必须按本文件执行。合并前先按目标客户端查询数据库并建立资源消费者矩阵。合并 Mania 前，运行 `osu-skin mania-analyze "<源皮肤>" --keys <N> --client stable|lazer --dependencies --json`，并对目标皮肤运行同一命令。核对图片组时运行 `osu-skin image-inspect "<资源路径>" --animation --json`。完整工具选择见 `tools.md`。

## 统一混皮原则

1. 先确认客户端、目标模式/keycount、输入皮肤和输出目录。用户给某来源分配 std/taiko/catch/Mania，只表示该来源是这个范围的候选，不表示它是全局基础皮肤。
2. 清点全部来源和目标中的文件族。普通图、`@2x`、动画帧、透明占位图和同族音频按族归并，不把文件名或目录当作模式归属证据。
3. 对每个去重文件族运行 `osu-skin db-query "<文件名>" --client <目标客户端> --json`，再运行 `database.md` 中的完整元素和共享资源 SQL；不要手写一套不完整的联表查询。
4. 先定义资源组，再决定复制文件；不要按目录全量覆盖。数据库无匹配或候选不唯一时标为未知并询问，不用提示词中的口头分组自行判断。
5. 对每个资源组收集配置字段、path、默认回退、SD、`@2x`、动画、关联音频、谱面覆盖和目标范围外消费者。
6. 冲突时先生成映射；重命名后同步修改所有引用。用户未确认共享来源时保留目标版本。
7. 默认生成新目录，保留目标 Name/Author 和来源记录；没有得到明确要求时不改皮肤名、不把混合结果作者改成模型或单一来源作者。
8. 写后重新检查资源闭包、引用、加载回退和输出像素，不以“文件复制成功”作为完成标准。

资源矩阵至少包含以下列：文件族/字段组、来源候选、数据库 id/client/标签/`game_mode`、实际 `skin.ini` 消费者、目标消费者、目标外消费者、来源决定、复制/重命名/保留动作、lazer 缩放检查。矩阵完成并处理未知项之前不能写输出。

以下资源组必须分别确认来源或明确保留目标版本，不能由 std 来源自动决定：

- cursor；
- score 数字、符号和 scorebar；
- combo 数字、overlap 和 Combo1..8 颜色；
- 菜单、选歌、暂停、失败和结算界面；
- Normal/Soft/Drum hitsound 和通用 UI 音频；
- `[Fonts]` 的 HitCircle/Score/Combo prefix 与 overlap；
- `[General]`、`[Colours]` 中的共享字段；
- Name、Author、credits 和其他元数据。

## 常用资源组

### cursor

包含 `cursor.png`、`cursormiddle.png`、`cursortrail.png`、`cursor-ripple.png`、`cursor-smoke.png` 和动画/HD 变体；同时检查 `CursorCentre`、`CursorExpand`、`CursorRotate`、`CursorTrailRotate`。只换 cursor 而保留旧 trail 可能产生尺寸或旋转不一致。

目标为 lazer 时，皮肤光标只在 std 游玩中渲染；菜单/选歌界面以及 taiko、catch、mania 使用 lazer 原生光标。因此 cursor 不是这些模式的共享皮肤资源，也不能只凭跨客户端的 `全局界面` 标签自动跟随 std 来源。stable 的消费范围不同，必须按目标客户端读取数据库 notes。

### std gameplay

按以下子组处理：

- hitcircle：`hitcircle`、overlay、approachcircle、数字前缀和 overlap；
- slider：slider body、followcircle、endcircle、scorepoint、reversearrow、ball；
- spinner：background、circle、approachcircle、metre、rpm、warning；
- followpoint：base、`-0..n`、blend mode 和帧率。

不要把菜单、结算和 gameplay 混为一个组，除非用户明确要求整套替换。

### 只替换一个模式或 Mania keycount 时的共享资源闸门

用户说“把目标皮肤的某个模式改成源皮肤的”时，不要复制源皮肤全部文件或整个 `skin.ini`。使用 `database.md` 的“完整元素详情”“共享资源”和“配置字段消费者” SQL 建立消费者集合，再把目标 `skin.ini` 的实际 path、prefix 和所有 `Keys: N` 段补入矩阵。

按查询结果分三组：目标范围内的专属资源可计划复制；包含其他模式的资源必须逐组确认；带 `全模式`/`全局界面` 或被目标外段引用的资源默认保留目标版本。

典型共享资源及其消费者：

| 资源 | 数据库/配置消费者 |
|---|---|
| `lighting.png` | std、taiko、catch |
| `sliderscorepoint.png`、`spinner-approachcircle.png`、`spinner-circle.png` | std、taiko |
| `inputoverlay-background.png`、`inputoverlay-key.png`、`scoreentry-0..9` | std、catch |
| `hit0/50/100/300` 等打击结果 | 全模式；还可能被谱面覆盖 |
| `score-0..9`、score 符号、`scorebar-*` | 全模式的分数或血量显示 |
| Normal/Soft/Drum hitsound 族 | 全模式音频，不属于任一单模式专属资源 |
| `cursor.png`、`cursormiddle.png`、`cursortrail.png` | stable 需按全局光标检查；lazer 只由 std 游玩消费，其他模式和界面使用原生光标 |
| `combo-0..9`、`ComboPrefix/ComboOverlap`、`Combo1..8` | std、catch；taiko、mania 不使用该组 |
| Mania path 指向的 note/key/stage 图片 | 所有引用同一路径的 `[Mania] Keys:N` 段；必须按目标皮肤实际引用判断 |

该表用于提示风险，不替代数据库查询；只向用户列出本次源皮肤中实际存在且计划复制的共享资源。提问时按资源组汇总，并明确效果，例如：

```text
源皮肤的目标模式资源中检测到以下共享项：
- lighting.png：目标皮肤中还由 std 和 catch 使用，会同时改变这两个模式的击打闪光；
- scorebar 组：标记为全模式，会改变其他模式的血量条；
- custom/note.png：还被 Keys:4 段引用，覆盖会同时改变 4K 音符。
这些共享组要跟随源皮肤覆盖，还是保留目标皮肤版本？可以逐组指定。
```

配置字段按 `database.md` 的消费者 SQL 查询；`[General]`、`[Colours]`、`[Fonts]` 和 `game_mode=all` 默认视为共享，不整段复制。用户未确认共享项时，保留目标值和目标文件。

### Mania keycount

只合并来源的 `Keys:N` 小节及其实际依赖，目标其他 keycount 保持不变。依赖清单、lazer 缩放和修复顺序分别看 `mania.md`、`lazer-image-scaling.md`；同一路径若被不同 keycount 或列宽使用，先拆分路径再改配置。

对来源和目标的每个 `Keys:N` 分别运行：

```text
osu-skin mania-analyze "<皮肤目录或 skin.ini>" --keys <N> --client <stable|lazer> --dependencies --json
```

把输出整理为 `来源 | Keys:N | 字段 | path | location | defined | base_alpha.status | 输出 path`。`path` 是该小节的唯一配置证据，`defined` 表示皮肤目录是否真的提供该资源：

- `location=root` 和 `location=subdirectory` 必须分开；不要把同名 `mania-*` 文件复制到根目录后让它覆盖目标的默认资源。
- `configured` path 优先于默认 path。默认回退也要单独记录 `defined=true/false`；例如目标根目录已有 `mania-stage-bottom.png` 时，它会继续作为未配置 `StageBottom` 的回退，不能被来源 6K 的默认文件静默叠加。
- 来源字段没有显式 path 时，先将来源默认资源复制到独立子目录并在导入的 `[Mania] Keys:N` 中写成显式 path；若要保留目标回退，则不要复制该来源默认文件。
- `Hit*`、`Lighting*`、`WarningArrow`、`Stage*`、`KeyImage#`、`NoteImage#` 及 `H/L/T` 均按 keycount 独立处理；不要因 7K 的 path 改写 4K。
- `base_alpha.status=fully_transparent` 是“存在但全透明”，不是缺失；除非用户确认替换，否则保留它。

只有每个目标 keycount 的 path、位置、`defined` 和透明状态都确认后，才复制、重命名或回写 `skin.ini`。

### hitsound

按 Normal/Soft/Drum 和用途族处理；替换一个文件前说明其他文件可能仍来自目标皮肤。

### 菜单/选歌/结算

按数据库标签选择 `菜单界面`、`选歌界面`、`结算界面`；检查 supporter 和 stable/lazer。大号 ranking 图在 lazer 的实际覆盖要单独确认。

## `@2x` 与 skin.ini 清理

- “图片只保留 `@2x`”必须按加载族验证。只有确认目标客户端会加载对应 HD 文件时才能删除 SD；若 SD 是必需入口或透明占位，先生成有效的 HD 等价物或保留 SD，并明确说明原因。删除后检查默认皮肤 fallback，不能以文件数量判断完成。
- 每个图片族都检查无后缀 base、`-0..n` 帧、SD/`@2x` 和自定义 path。不得遗漏子目录、自定义前缀或只处理根目录。
- 格式化 `skin.ini` 时只删除真正的整行注释和解析器确认的行尾注释。不要用简单的 `//` 分割，因为 URL（如 `https://...`）和路径可能包含该字符。
- 格式化后逐项验证 section、重复键、拼写、path/prefix、文件存在性和大小写；发现疑似错拼字段时查询数据库并报告，不能静默保留或自创修正。

## lite 配方

1. 询问保留的客户端、模式和界面。
2. 列出会删除的资源组、被删除的配置和预计保留的 fallback。
3. 复制到新目录后执行删除，不原地删除第三方皮肤。
4. 动画可以保留 base、首帧或静态代表帧；必须说明选择。
5. 删除后重新检查 `skin.ini` path、数据库必需资源和客户端 fallback。

## 来源和授权

记录源皮肤名、作者、资源组、复制日期和修改内容。不要把混合结果描述成全部原创；分发前提醒用户自行确认作者许可。

## lazer 皮肤名称与 `.osk` 输出名

生成或导出 lazer 皮肤时，按以下行为规则处理名称，不要只用工作目录名或源压缩包名猜输出文件名：

1. `[General]` 中的 `Name` 和 `Author` 是皮肤显示名称与作者信息；导出或保存时，这两个值会写回 `skin.ini`。
2. 导入目录或 `.osk` 时，非空的 `skin.ini Name` 优先于压缩包/目录基名；Name 为空时才使用 archive/folder basename。若两者不同，lazer 可能把原始 archive 名追加为 `[archiveName]`，以保留用户可识别的来源名。
3. `skininfo.json` 在导入时主要用于保留 `InstantiationInfo`，不能作为皮肤显示名或 `.osk` 文件名的权威来源。
4. 导出 `.osk` 时，默认基名是 `Name`，有作者时追加 ` (Author)`。因此默认输出应为：

   ```text
   <Name> (<Author>).osk
   ```

   作者为空时省略括号部分。
5. 导出前删除跨平台非法字符（包括 `" < > |`、控制字符、`: * ? \\ /`），不要擅自用下划线替换；基名过长时先截断，再添加 `.osk`。基名最大保留长度为 208 个字符，实际重名时生成不冲突名称。
6. lazer 导出使用 UTF-8 archive filename；保留非 ASCII 名称时不要为了兼容 stable 擅自转成拼音或删除 Unicode 字符。
7. `.osk` 内部资源文件名仍必须保持 `skin.ini`、图片、音频和 JSON 的实际文件名/path；外部 `.osk` 文件名与内部资源文件名是两套命名，不要把 Name 改写成某个图片文件名。

执行输出前检查并报告：`skin.ini [General] Name`、`Author`、计算出的显示字符串、清理后的 `.osk` 文件名、是否发生截断/重名，以及输出后 `skin.ini` 是否仍与显示名称一致。用户明确指定输出文件名时可以遵循用户指定，但要标明它与 lazer 默认的 `Name (Author).osk` 规则不同；除非用户要求，不要静默修改 Name 或 Author 来迎合文件名。
