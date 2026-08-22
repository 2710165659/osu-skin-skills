# 工具目录与调用契约

本文件定义自然语言需求到 `osu-skin` CLI 的固定接口。用户需求可以灵活理解；一旦选择工具，严格使用本文件的命令模板和参数约束，不自行拼接未记录的选项。

## 目录

- [统一协议](#统一协议)
- [选择流程](#选择流程)
- [selfcheck](#selfcheck)
- [db-query](#db-query)
- [image-inspect](#image-inspect)
- [image-transform](#image-transform)
- [audio-inspect](#audio-inspect)
- [mania-analyze](#mania-analyze)
- [mania-throw-length](#mania-throw-length)
- [mania-lazer-hold-body-fix](#mania-lazer-hold-body-fix)
- [mania-lazer-key-fix](#mania-lazer-key-fix)
- [工具边界](#工具边界)

## 统一协议

### 启动和路径

1. 所有命令以 `osu-skin <子命令>` 开头；命令不可用时在技能根目录运行 `python -m pip install -e .`，然后重试原命令。
2. 路径必须使用用户提供或检查得到的绝对路径；包含空格时用双引号。`<SKIN_DIR>` 必须是包含 `skin.ini` 的目录，`<PNG>` 必须是实际被引用的 PNG。
3. 只读检查先执行；任何写入命令先执行完全相同参数的 `--dry-run --json`，读取计划后才移除 `--dry-run`。写入输出默认使用新文件/新目录，不原地覆盖。
4. 除非命令明确要求，否则每次都追加 `--json`。JSON 顶层 `ok=false`、进程非零退出、`errors` 非空或关键文件不存在都视为失败，停止后续写入。
5. 写入工具的 `--output` 是输出文件或输出目录，不是 `skin.ini`；工具不会自动修改配置、复制资源、重命名资源或打包 `.osk`。

### 证据闭环

1. 记录输入路径、命令、完整参数和 JSON 输出。
2. 写入成功后，重新运行对应只读工具检查输出；至少确认输出存在、尺寸/格式正确、alpha 或透明行符合目标。
3. 不能用工具输出证明游戏内实测渲染；没有客户端实测时标记为静态验证。

## 选择流程

| 用户需求 | 固定工具链 | 禁止替代 |
|---|---|---|
| 查询元素、字段、标签、术语、客户端 | `db-query` | 不从文件名推断消费者 |
| 查询共享资源或消费者矩阵 | `db-query --sql` / `--sql-file` | 不只做普通关键词搜索 |
| 数据库异常 | `selfcheck` | selfcheck 失败后不写入 |
| 图片尺寸、alpha、透明边、SD/HD、动画 | `image-inspect` | 不用变换工具代替检查 |
| 普通图片放大、裁切、改色、HD/SD 变换 | `image-inspect` -> `image-transform` | 不直接覆盖源文件 |
| 音频格式、时长、hitsound 族、WAV 循环 | `audio-inspect` | 不凭扩展名断言可播放 |
| Mania path、重复小节、keycount 依赖 | `mania-analyze` | 不按 `mania-*` 文件名跨小节合并 |
| 投皮长度/顶部透明行数 | `mania-analyze` -> `mania-throw-length` | 不用普通 `scale` |
| lazer Hold Body 拉伸 | `mania-analyze` + `image-inspect` -> `mania-lazer-hold-body-fix` | 未确认 lazer 拉伸不执行 |
| lazer Key/KeyD 拉伸 | `mania-analyze` + `image-inspect` -> `mania-lazer-key-fix` | 不用 Hold Body 修复工具 |

## selfcheck

### 用途

只读检查 `osu_skin.db` 是否存在、SQLite `quick_check`、外键、必需表和 `term_definitions`。它不检查用户皮肤文件，不验证游戏渲染。

### 固定调用

使用内置数据库：

```text
osu-skin selfcheck --json
```

指定数据库：

```text
osu-skin selfcheck --db "<DB_PATH>" --json
```

### 判定

- 成功必须满足顶层 `ok=true`、`exists=true`、`integrity.ok=true`、`foreign_keys.ok=true`、`required_tables.ok=true`、`missing_tables=[]`、`errors=[]`。
- 任一条件失败，先修复数据库/安装问题，不执行依赖数据库的查询和写入。

## db-query

### 用途

只读查询 `elements`、图片/动画/音频/skin.ini 专属详情、标签定义、消费者范围、术语和 `lazer_json_entries`。普通搜索适合单个元素或 JSON 文件/字段/Type；跨元素、共享资源、JSON 完整目录和消费者矩阵必须使用只读 SQL。

### 普通搜索模板

```text
osu-skin db-query "<QUERY>" --client <stable|lazer|both> --type <image|audio|skin_ini|lazer_json> --json
```

可选参数规则：

- `--client`、`--type` 可省略；省略表示不按该条件过滤。
- `--tag "<TAG>"` 可重复多次，表示同时要求这些标签：

```text
osu-skin db-query "<QUERY>" --client <stable|lazer|both> --tag "<TAG1>" --tag "<TAG2>" --json
```

- `<QUERY>` 可以是元素 id、文件名/文件名去掉扩展名、skin.ini 命令、标签或描述词。查询动画帧时去掉 `@2x` 和帧号；候选不唯一时保留所有结果。
- `--type lazer_json` 只查询 `lazer_json_entries`；`--client lazer` 或省略客户端才会返回 JSON 事实，`stable`/`both` 不返回 lazer-only JSON 记录。
- 普通搜索不指定 `--type` 时，元素结果仍在 `results`，JSON 事实在 `lazer_json_results`；分别读取 `count`、`lazer_json_count` 和 `total_count`。

### SQL 模板

```text
osu-skin db-query --sql "<SELECT_OR_WITH_SQL>" --json
osu-skin db-query --sql-file "<UTF8_SQL_FILE>" --json
```

- `--sql` 与 `--sql-file` 互斥；不能同时传位置查询词。
- SQL 只能以 `SELECT`、只返回行的 `WITH`、`EXPLAIN` 或 `PRAGMA` 开始；禁止 `INSERT`、`UPDATE`、`DELETE`、`DROP`、DML CTE、多语句和写事务。
- 原始 SQL 不能同时使用 `--client`、`--type`、`--tag`；筛选条件写入 SQL。
- 混皮必须优先读取 `references/database.md` 的完整元素、共享资源、配置消费者和 Mania 查询，不要临时写不完整联表。

### 输出判定

- `mode="search"` 时读取 `results` 和 `term_matches`；`count=0` 是未知/无匹配，不是文件不存在。
- `mode="sql"` 时读取 `results` 的原始列；不要假设列名，按 SQL 中的列名处理。
- 成功要求顶层 `ok=true`；失败读取 `error`，不要使用失败时的部分输出。

## image-inspect

### 用途

只读检查图片格式、尺寸、alpha 统计、透明边、透明像素下的 RGB、SD/`@2x` 配对和数据库声明的动画帧。支持单文件或目录；目录默认只看一层，递归时显式加 `--recursive`。

### 固定调用

单张图片基础检查：

```text
osu-skin image-inspect "<PNG_OR_IMAGE>" --json
```

检查透明像素 RGB：

```text
osu-skin image-inspect "<PNG_OR_IMAGE>" --transparent-rgb --json
```

检查透明边/透明行和动画：

```text
osu-skin image-inspect "<PNG_OR_IMAGE_OR_DIR>" --transparent-rows --animation --json
```

递归检查整个皮肤：

```text
osu-skin image-inspect "<SKIN_DIR>" --recursive --animation --json
```

### 输出判定

- 顶层 `ok=false` 或 `errors` 非空表示至少一个文件无法读取；先处理错误。
- `images[]` 逐文件读取 `width`、`height`、`format`、`mode`、`has_alpha`、`alpha` 和 `hd_sd`。
- `alpha.status` 不存在于此工具输出；根据 `alpha.transparent`、`alpha.translucent`、`alpha.opaque` 判断全透明、混合或全不透明。
- 加 `--transparent-rows` 后读取 `transparent_edges.top/bottom/left/right`；它们是连续全透明边的行/列数，不是图片总透明像素数。
- 加 `--animation` 后读取 `animation_groups` 的 `frames`、`missing_frames`、`duplicate_frames`、`base_exists` 和 `consistent_size`。

## image-transform

### 用途

对 PNG 执行普通缩放、裁切、重着色和 SD/HD 互转。它只处理图片，不理解元素消费者、`skin.ini`、Mania 列宽或 lazer 渲染规则。

### 固定操作模板

所有写入操作先运行预览：

```text
osu-skin image-transform "<PNG_OR_DIR>" --operation <OPERATION> --output "<OUTPUT_OR_DIR>" [OPTIONS] --dry-run --json
```

确认 JSON 后，移除 `--dry-run`；只有明确允许覆盖时才追加 `--overwrite`。

| `--operation` | 必填参数 | 语义和固定约束 |
|---|---|---|
| `scale` | `--width <POSITIVE_INT>` 或 `--height <POSITIVE_INT>` 至少一个 | 指定一个边时按比例计算另一边；同时指定两边会改变纵横比。普通“放大 2 倍”先用 inspect 得到 `W,H`，再传 `--width 2W --height 2H`。 |
| `crop` | `--width <POSITIVE_INT> --height <POSITIVE_INT>` | `--left/--top` 可选，省略时居中；裁切矩形必须在源图内。 |
| `recolor` | `--color R,G,B` 或 `R,G,B,A` | 只替换颜色并保留 alpha；值必须为 0-255。 |
| `hd-to-sd` | 无 width/height | 只处理文件名带 `@2x` 的 PNG，尺寸缩小为 1/2；源宽高必须为偶数。 |
| `sd-to-hd` | 无 width/height | 只处理不带 `@2x` 的 PNG，尺寸放大为 2 倍，并输出带 `@2x` 的文件名。 |

单文件放大示例：

```text
osu-skin image-transform "<PNG>" --operation scale --width <2W> --height <2H> --output "<OUTPUT_PNG>" --dry-run --json
```

目录输入时 `<OUTPUT_OR_DIR>` 必须是目录；需要包含子目录的 PNG 时追加 `--recursive`。`--filter` 只能为 `nearest`、`lanczos`、`bicubic`，默认 `lanczos`。

### 输出判定

- 预览成功必须 `ok=true`、`dry_run=true`，并逐项读取 `files[].source_size`、`files[].output_size`、`files[].output`。
- 正式执行成功必须 `ok=true`、`dry_run=false`、每项 `written=true`，然后用 `image-inspect` 复查输出。
- 禁止把 `scale` 用于投皮顶部透明行、lazer Hold Body 或 Key/KeyD 适配。

## audio-inspect

### 用途

只读检查 `.wav`、`.mp3`、`.ogg` 的解码信息、扩展名与 codec 是否匹配、时长、采样率、声道和码率；可检查 hitsound 样本族和 WAV 首尾循环风险。

### 固定调用

单文件或一层目录：

```text
osu-skin audio-inspect "<AUDIO_OR_DIR>" --json
```

递归检查并分组 hitsound：

```text
osu-skin audio-inspect "<SKIN_DIR>" --recursive --family --json
```

检查 WAV 循环边界：

```text
osu-skin audio-inspect "<WAV_OR_DIR>" --loop --json
```

### 输出判定

- 顶层 `ok=false` 或 `errors` 非空表示存在无法解析的音频。
- `files[]` 读取 `codec`、`extension_matches_codec`、`duration_seconds`、`sample_rate`、`channels` 和 `bitrate`。
- WAV 读取 `sample_width_bits`、`compression`；加 `--loop` 读取 `loop_boundary.click_risk`、`boundary_delta`、`dc_offset`。非 PCM WAV 会标记 loop 不支持，不得当作无循环风险。
- 加 `--family` 读取 `families[].present`、`missing`、`complete`；缺失族成员再回到数据库确认 fallback。

## mania-analyze

### 用途

只读解析一个客户端下指定 `Keys:N` 的 `[Mania]` 小节。它解析重复小节、字段最终值、默认回退、实际 path、根目录/子目录、SD/`@2x`、动画帧、alpha、长条 H/L/T、几何和警告。

### 固定调用

```text
osu-skin mania-analyze "<SKIN_DIR_OR_INI>" --keys <N> --client <stable|lazer> --dependencies --json
```

- `--keys N` 必填，`N` 是正整数；每个要合并的 keycount 单独运行一次。
- `--client` 必须为 `stable` 或 `lazer`，不能省略或使用 `both`。
- `--dependencies` 是获取实际文件、HD、动画和 alpha 的必选项；没有皮肤文件时只能解析字段，不能断言资源存在性。

### 输出判定

- `matching_sections=0` 是失败/需确认 keycount；`matching_sections>1` 必须逐段确认，不能默认第一段。
- `sections[].paths` 是该小节的实际配置或默认 path；`path_sources` 区分 `configured` 与 `default`。`configured_paths` 列出只在该小节显式出现的字段。
- `sections[].resources[field]` 读取 `defined`、`relative_path`、`location`、`resolved_base`、`base_exists`、`hd_exists`、`base_alpha`、`hd_alpha`、`frames` 和 `hd_frames`。`defined=false` 表示皮肤目录没有提供该 path。
- `sections[].fallback_resources[path]`（需 `--dependencies`）会保留每个默认/候选 path，即使文件不存在；读取其中的 `defined`/`base_exists` 判断默认回退是否由当前皮肤定义。`fallback_defined[field]` 提供按字段排列的候选及其 `defined` 状态；未启用依赖检查时状态为 `null`。
- `base_alpha.status` 为 `fully_transparent` 时，资源存在但全透明，不能按缺失处理或自动替换。
- lazer 的有效偶数 `Keys > 10` 会强制等分为双舞台；显式配置的 `ColumnLineWidth[Keys/2+1..Keys]` 中如有非零值，`sections[].warnings` 会报告这些 0-based 索引不参与列分隔线渲染。未配置字段产生的默认值不触发此警告。
- 混皮时对源/目标的每个 `Keys:N` 建立 `来源 | Keys:N | 字段 | 实际 path | location | defined | alpha | 输出 path` 矩阵；只修改实际消费者小节。目标根目录已经定义的默认 `mania-stage-bottom` 等资源不能被来源默认文件直接覆盖。

## mania-throw-length

### 用途

修改一个 `NoteImage#L` Hold Body PNG 顶部连续全透明行数，保持画布宽高不变。这是“投皮长度”，不是图片整体缩放或谱面 hold duration。

### 固定调用

预览：

```text
osu-skin mania-throw-length "<NOTE_IMAGE_L_PNG>" --throw-length <TARGET_ROWS> --output "<OUTPUT_PNG>" --dry-run --json
```

确认后移除 `--dry-run` 执行。输入和输出必须为 PNG；`TARGET_ROWS` 必须满足 `0 <= TARGET_ROWS < 图片高度`；全透明源图不能处理。

该命令没有 `--overwrite` 选项，输出存在时会原子替换；除非用户明确允许覆盖，否则先选择不存在的新输出路径。

### 输出判定

- 预览/执行都应 `ok=true`；读取 `current_throw_length`、`target_throw_length`、`direction`、`shift_rows`。
- 正式执行后确认 `written=true`，再用 `image-inspect --transparent-rows --json` 复查顶部透明行。

## mania-lazer-hold-body-fix

### 用途

修复确认由 lazer 目标矩形造成的 `NoteImage#L` 非等比拉伸。它不能从已经依赖 stable 拉伸的成品外观还原原稿，也不修改 `skin.ini`。

### 固定调用

```text
osu-skin mania-lazer-hold-body-fix "<NOTE_IMAGE_L_PNG>" --column-width <COLUMN_WIDTH> --output "<OUTPUT_PNG>" --dry-run --json
```

- `<COLUMN_WIDTH>` 必须来自目标 `Keys:N` 小节的实际 `ColumnWidth`，不是图片宽度或 lazer 渲染宽度；必须为正数。
- 输出必须为 PNG；已有输出只有明确允许覆盖时追加 `--overwrite`。

### 输出判定

- 读取 `source_size`、`output_size`、`target_width`、`target_height`、`operation`、`limitation`。
- 目标高度固定为工具定义的 Hold Body 画布高度；若 `limitation` 与用户目标冲突，停止并报告。
- 正式执行后确认 `written=true`，再用 `image-inspect` 检查尺寸和 alpha。

## mania-lazer-key-fix

### 用途

修复确认由 lazer 目标矩形造成的 `KeyImage#` 或 `KeyImage#D` 非等比拉伸。全透明 Key 图会被识别为跳过，不生成替代图；不修改 `skin.ini`。

### 固定调用

```text
osu-skin mania-lazer-key-fix "<KEY_IMAGE_PNG>" --column-width <COLUMN_WIDTH> --output "<OUTPUT_PNG>" --dry-run --json
```

- `<COLUMN_WIDTH>` 必须来自实际 `Keys:N` 小节对应列；必须为正数。
- 工具根据输入文件名是否带 `@2x` 自动计算 HD 目标宽度；不要手动把 `ColumnWidth` 乘 2。
- 输出必须为 PNG；已有输出只有明确允许覆盖时追加 `--overwrite`。

### 输出判定

- 正常修复读取 `skipped=false`、`source_size`、`output_size`、`target_width`、`alpha_bbox` 和 `limitation`。
- `skipped=true` 且 `reason="source image is fully transparent"` 是成功的保留信号，不是错误，不要强行生成可见图。
- 正式执行后确认 `written=true`（跳过时为 false），再用 `image-inspect` 复查输出。

## 工具边界

- 没有自动混皮命令：按 `merge-recipes.md` 建立矩阵、复制资源、重命名并逐个回写 `skin.ini`。
- 没有自动 `skin.ini` 编辑命令：修改前后必须保留 section、重复键、path 和编码，并人工/脚本复查。
- 没有自动 `.osk` 打包命令：按 `merge-recipes.md` 检查压缩包根结构、名称和内部文件。
- 数据库工具只能提供数据库事实，不能证明某个用户皮肤实际引用；实际 path 必须由 `skin.ini` 和 `mania-analyze`/文件检查确认。
- 图片工具只能证明文件指标，不能证明 stable/lazer 游戏内最终渲染；客户端差异按对应 reference 解释。
