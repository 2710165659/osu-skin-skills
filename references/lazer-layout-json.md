# lazer 布局 JSON 编辑

工具用途：`db-query` 只读查询 `lazer_json_entries` 中经版本核验的 JSON 文件、分组、字段、完整 `Type`、`Settings` 和运行时行为；PowerShell 的 `ConvertFrom-Json` 只验证实际文件语法和读取对象，不验证组件能否被 lazer 实例化。开始任务时先运行 `osu-skin selfcheck --json`，再运行 `osu-skin db-query "<文件、字段、Type 或设置>" --client lazer --type lazer_json --json`。需要列出全部记录时使用 `db-query --sql` 查询 `lazer_json_entries`。写入前退出皮肤编辑器并备份目标 JSON，写入后重新解析文件并在 lazer 中实测。完整工具选择见 `tools.md`。

文件、分组、字段、完整 `Type` 字符串及 `Settings` 的确定事实只存放在数据库；查询结果带有 JSON 路径、用途、合法值和验证版本，不在本文件复制一份会过期的目录。

## 四个 JSON 的职责

| 文件 | lazer 读取目标 | 分组选择 | 缺失/空数组 |
|---|---|---|---|
| `skininfo.json` | 皮肤实例元数据 | 无分组 | 缺失或解析失败时按兼容皮肤实例处理 |
| `MainHUDComponents.json` | 游玩 HUD | `global` + 当前规则集（`osu`/`taiko`/`fruits`/`mania`） | 文件或目标分组缺失时可走默认；存在空数组时该 HUD 目标明确为空 |
| `SongSelect.json` | 选歌界面可编辑组件 | 只读 `global` | 缺失可走默认；存在空数组时选歌自定义目标为空 |
| `Playfield.json` | 游玩 Playfield 组件 | 只读当前规则集 | 缺失可走默认；存在空数组时该规则集 Playfield 自定义目标为空 |

`MainHUDComponents.json` 的 `global` 和规则集分组是两个同时挂载的容器，不是覆盖关系。`Playfield.json` 不使用 `global` 作为当前规则集的替代分组。

## 先查数据库

普通搜索会同时查询元素表和 lazer JSON 表。`results/count` 保持原有元素结果含义；JSON 事实在 `lazer_json_results/lazer_json_count`，总数在 `total_count`。

查询某个文件的所有记录：

```powershell
osu-skin db-query "MainHUDComponents.json" --type lazer_json --client lazer --json
```

查询完整 `Type` 和用途：

```powershell
osu-skin db-query "LegacyManiaComboCounter" --type lazer_json --client lazer --json
```

查询所有通用字段：

```powershell
osu-skin db-query "Position" --type lazer_json --client lazer --json
```

查询某组件的设置：

```powershell
osu-skin db-query "ArgonPerformancePointsCounter" --type lazer_json --client lazer --json
```

需要完整目录时使用只读 SQL：

```powershell
osu-skin db-query --sql "SELECT entry_kind, file_name, json_path, component_type, field_name, value_type, default_value, valid_values, description, notes, verified_lazer_version FROM lazer_json_entries ORDER BY file_name, json_path, entry_kind, id" --json
```

## `skininfo.json`

该文件不是 HUD 布局。它的顶层字段及导入语义直接查询：

```powershell
osu-skin db-query "InstantiationInfo" --type lazer_json --client lazer --json
```

编辑规则：

- `InstantiationInfo` 必须保留 lazer 生成的完整实例类型信息。它决定使用哪种皮肤实现；不要替换为显示名称或任意类型。
- `Name`、`Creator` 是元数据，不是组件位置、资源路径或 HUD 开关。
- `ID` 是内部皮肤对象标识，导出文件可以没有；不要手工新建 ID 来“修复”布局。
- 修改 `skin.ini` 的 `[General] Name/Author` 后，重新导入时以实际 skin.ini 元数据为准；不要只改 `skininfo.json` 就断言游戏内名称已变。

## 布局 JSON 顶层字段

```json
{
  "Version": 1,
  "DrawableInfo": {
    "global": [],
    "mania": []
  }
}
```

- `Version`：布局 schema 版本。保留 lazer 生成值；缺失或旧版本由客户端迁移，不能用来指定客户端程序版本。
- `DrawableInfo`：分组到组件数组的字典。数组内对象按顺序实例化并加入目标容器。
- 分组不存在与空数组不同：不存在允许默认 fallback，空数组表示用户明确配置了空目标。
- 同一组件重复出现会实例化多个实例；这不是“覆盖旧对象”，会造成重叠或重复显示。

## 组件对象字段

组件字段的完整类型、路径、值类型和默认值以数据库 `entry_kind='component_field'` 为准：

```powershell
osu-skin db-query "component_field" --type lazer_json --client lazer --json
```

核心行为如下：

- `Type`：完整程序集限定类型。必须保留完整命名空间、程序集、版本、Culture 和 PublicKeyToken；无法解析时该组件变为空对象，不会自动补成默认组件。
- `Position`：相对 `Anchor` 的逻辑坐标偏移；x 正向右，y 正向下。它不是 PNG 像素坐标。
- `Rotation`：角度，通常为 `0.0`。
- `Scale`：x/y 缩放；`0` 不可见，负值翻转对应轴。
- `Width`、`Height`：非自动尺寸组件的显式尺寸。客户端只在值非 null、非 0 且组件对应轴不是自动尺寸时应用它们。
- `Anchor`：父区域参考点。常用数值及名称查询数据库 `field_name='Anchor'`，不要凭数字猜锚点。
- `Origin`：组件自身落在坐标上的参考点。`Anchor` 正确而 `Origin` 错误时，组件会偏移自身宽高的一部分。
- `UsesFixedAnchor`：`true` 保持 JSON 指定锚点；`false` 时皮肤编辑器移动组件会自动选择最近锚点/原点，并可能重写位置。
- `Settings`：组件专属设置。只写该 `Type` 在数据库中列出的键；键名是 snake_case，枚举使用序列化整数。未知键不参与应用；省略已知键时保留组件构造默认值；已知键类型无法转换时该组件变为空对象。
- `Children`：嵌套组件数组。只有容器组件会加入子组件；子对象同样需要有效 `Type` 和完整字段。

## Mania 位置规则

自定义 `MainHUDComponents.json` 的 `mania` 分组是所有 Mania keycount 共用的一套组件列表。`skin.ini` 每个 `[Mania]` 小节仍可有不同的 `ComboPosition`/`ScorePosition`，但自定义 HUD 中的连击对象位置由 JSON 控制，不会逐 keycount 重定位。

legacy 坐标迁移到 lazer 布局时：

```text
JSON y = skin.ini legacy position * 1.6
```

例如 `ComboPosition: 160` 对应 `y: 256`；`ScorePosition: 200` 对应判定坐标 `320`，两者相差 `64` 个 lazer 单位，也就是 legacy 的 `40`。要保持多个 keycount 的距离一致，统一各小节的 `ScorePosition`，并保留一个共用连击对象。

若要让各 keycount 使用不同连击位置，必须删除整个自定义 Mania HUD 分组让默认布局接管，或接受 JSON 共用位置；单个 JSON `mania` 数组不能表达逐 keycount 的连击坐标。

## 手动编辑流程

1. 确认当前 lazer 皮肤目录和目标 JSON；不要编辑 stable 目录或旧导出副本。
2. 退出皮肤编辑器，先备份目标文件。
3. 先用 `db-query --type lazer_json` 查出目标分组、完整 `Type` 和字段合法值。
4. 移动已有组件时只改 `Position`、`Anchor`、`Origin`、`UsesFixedAnchor`；不要凭记忆重建 `Type`、`Settings`、`Children`。
5. 保存为 UTF-8，无注释、无尾逗号、字符串用双引号。
6. 用 JSON 解析器检查语法，再比较修改前后的分组和组件数量。
7. 重新加载皮肤后进入对应界面/规则集；Mania 至少检查 4K 和一个高 keycount。
8. 若重新打开编辑器并保存，保存后再次检查，因为编辑器会规范化布局数据。

静态 JSON 检查：

```powershell
Get-Content -LiteralPath '.\MainHUDComponents.json' -Raw | ConvertFrom-Json | Out-Null
```

## 故障定位

| 现象 | 确定的优先检查 |
|---|---|
| 连击消失 | `MainHUDComponents.json` 的 `DrawableInfo.mania` 是否存在连击 `Type`；数组存在时不会自动补回 |
| 修改 `ComboPosition` 无效 | 自定义 Mania 分组是否存在；存在时 JSON 的 `Position` 优先 |
| 整个 HUD 回默认 | JSON 文件未被读取、语法解析失败、目标分组缺失或编辑了错误皮肤副本 |
| HUD 为空 | 目标分组是 `[]`，这是明确的空自定义布局 |
| 组件重叠/重复 | 同一个 `Type` 被列出多次，或 global 与规则集组件本来就同时显示 |
| 位置随屏幕比例漂移 | `Anchor`/`Origin` 不匹配，或 `UsesFixedAnchor=false` 导致编辑器采用最近锚点 |
| 单个组件不可见 | `Type` 无效、`Scale` 为 0、尺寸被错误设为 0，或位置在屏外 |
| 设置不生效 | `Settings` 键名、snake_case、枚举整数或值类型不符合数据库记录 |

## 验证边界

数据库和 JSON 解析只能证明结构、类型记录和静态字段；不能证明当前 lazer 版本、显示设置、窗口比例和实际谱面中的最终渲染。完成手工修改后必须报告静态验证，并把未启动客户端实测标为未验证。
