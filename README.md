# osu! Skin Skill

面向 AI Agent 的 osu! 皮肤领域 Skill，提供 stable/lazer 判断规则、皮肤元素数据库、按需 reference，以及统一的 `osu-skin` CLI 入口。

## 当前状态

Skill 的领域说明和 CLI 参数已经建立，CLI 业务逻辑尚未实现。当前子命令会输出 `TODO` 并返回退出码 `3`；这表示入口可用，不表示任务已经执行成功。

## 环境要求

- Python 3.10 或更高版本
- pip

## 安装

在项目根目录运行：

```powershell
python -m pip install -e .
```

验证命令是否注册：

```powershell
osu-skin --help
```

使用可编辑安装后，修改 `scripts/` 中的模块不需要重新安装。修改 `pyproject.toml` 中的命令注册或包元数据后，应重新执行安装命令。

## CLI

```text
osu-skin db-query
osu-skin image-inspect
osu-skin image-transform
osu-skin audio-inspect
osu-skin mania-analyze
osu-skin mania-throw-length
```

查看具体参数：

```powershell
osu-skin <子命令> --help
```

示例：

```powershell
# 查询数据库字段
osu-skin db-query NoteBodyStyle --type skin_ini --json

# 检查 PNG 的 alpha、透明行和透明像素 RGB
osu-skin image-inspect "D:\Skins\Example\mania-note1L.png" --transparent-rows --transparent-rgb --json

# 分析 lazer 7K Mania 段及其资源依赖
osu-skin mania-analyze "D:\Skins\Example" --keys 7 --client lazer --dependencies --json

# 将投皮顶部透明区域设为 50px
osu-skin mania-throw-length "D:\Skins\Example\mania-note1L.png" --throw-length 50 --output "D:\Skins\Output\mania-note1L.png" --dry-run
```

“投的长度”指投皮图片顶部连续全透明行数，不是谱面长按时间、判定线高度或某个 `skin.ini` 长度字段。

## 目录

```text
SKILL.md               AI Agent 的入口和路由规则
assets/osu_skin.db     皮肤元素与 skin.ini 字段数据库
references/            按任务加载的领域说明
scripts/               可导入的 Python CLI 模块
evals/evals.json       Skill 行为评测样例
pyproject.toml         Python 包与 osu-skin 命令注册
```
