# osu-skin-skills

`osu-skin-skills` 是一个面向 Codex 等 AI Agent 的 osu! 皮肤领域 Skill。它把 osu! stable、osu! lazer、`skin.ini`、图片、动画、音频和 Mania 皮肤规则整理成可查询的知识库、按需加载的参考文档以及一组可验证的 CLI 工具。

它的目标不是只回答“这个文件叫什么”，而是帮助 AI 根据实际皮肤文件、数据库和客户端规则判断：资源是谁在使用、路径是否真的生效、修改会不会影响其他模式，以及输出是否经过复查。

## 能做什么

安装后，你可以让 AI 协助完成以下工作：

- **识别皮肤元素**：解释 `hitcircle`、`button`、`play-skip`、Mania note、Lighting、Stage 等图片或字段的用途、客户端和回退关系。
- **查询术语和数据库**：查询文件名、`skin.ini` 字段、标签、客户端差异、术语定义和共享资源消费者；需要时直接执行只读 SQL。
- **检查实际皮肤**：读取 `skin.ini` 的实际 path，检查图片尺寸、alpha、透明区域、SD/`@2x`、动画帧、音频格式和 hitsound 族。
- **诊断 stable/lazer 差异**：分析默认回退、非等比缩放、Mania 列宽、Hold Body、Key/KeyD、`NoteBodyStyle` 等问题。
- **编辑 lazer JSON**：查询并修改 `skininfo.json`、HUD、SongSelect 和 Playfield 布局，精确解释分组、字段、完整 `Type`、`Settings`、锚点和默认回退。
- **处理 Mania 皮肤**：按 4K、5K、7K 等具体 keycount 解析重复 `[Mania]` 小节、资源依赖、长按头/体/尾、Lighting 和 Stage。
- **混合皮肤**：把不同来源的 std、taiko、catch 或 Mania keycount 合入目标皮肤，同时区分共享资源、根目录/子目录 path、透明占位图和其他消费者。
- **修改图片**：进行普通缩放、裁切、重着色、HD/SD 变换，或处理 Mania 投皮长度和 lazer 专用图片适配。
- **制作输出**：在确认资源闭包、配置引用和回退关系后，协助生成新的皮肤目录或 `.osk` 文件，并列出变更和未确认项。

## 安装到 Skill 目录

不需要手动创建目录或执行多条命令。把下面这段粘贴到你的 AI 智能体对话框，它会自动读取技能文件、放入标准 Skill 目录、安装依赖并验证：

```text
请安装 osu-skin-skills Skill：从 https://github.com/2710165659/osu-skin-skills.git 克隆到当前 AI 智能体使用的标准 skills 目录；如果已经存在则拉取最新版本。按照该平台的 Skill 安装流程注册它，在技能目录中执行必要的依赖安装（python -m pip install -e .），最后运行 selfcheck 或等价检查确认安装成功，并报告安装路径和验证结果。
```

安装完成后重新打开 Agent 或新建任务即可使用。只需要知识和参考文档时不一定要运行 CLI；涉及实际文件、像素、路径或音频时，CLI 能提供可复查证据。

## 示例对话

下面这些说法都可以直接作为任务发给 AI。AI 会根据请求先确认客户端、皮肤目录、模式或 Mania keycount，再决定读取哪些资料和工具。

### 解释元素

> `hitcircle` 是什么？

> std 模式有哪些图片可以换？

> `button` 和 `play-skip` 分别是什么？

> `LightingN` 是干什么的？会影响哪些模式？

> std 模式滑条颜色相关配置项有哪些？

### 检查和修改图片

> 帮我把 `cursor.png` 放大两倍。

> `mania-note1T` 为什么是透明的？

### stable 到 lazer

> 我的皮肤从 stable 换到 lazer 后面尾变形了，帮我看看。

### 混皮

> 我想把两个皮肤的 4K 和 7K 合到一起，帮我处理一下。

> 我想把这个皮肤的 std 皮肤移到我的皮肤上，应该替换哪些元素？

### 投皮

> 帮我把4k的投皮长度改成 50。

## CLI 工具概览

详细参数和调用契约见 [`references/tools.md`](references/tools.md)。可用工具包括：

- `selfcheck`：检查数据库完整性和必需表；
- `db-query`：查询元素、字段、标签、术语、lazer JSON 事实和只读 SQL；
- `image-inspect`：检查尺寸、alpha、透明区域、SD/`@2x` 和动画；
- `image-transform`：缩放、裁切、重着色、HD/SD 变换；
- `audio-inspect`：检查音频格式、时长、hitsound 族和 WAV 循环；
- `mania-analyze`：解析指定 Mania keycount 的字段、path 和资源依赖；
- `mania-throw-length`：修改投皮顶部透明行数；
- `mania-lazer-hold-body-fix`：修复 lazer Hold Body 拉伸；
- `mania-lazer-key-fix`：修复 lazer Key/KeyD 拉伸。

CLI 工具不会自动替 AI 决定共享资源归属，也不会无提示地修改 `skin.ini`、删除源文件或覆盖原皮肤。写入操作应使用新输出路径并进行复查。

## 项目内容

```text
SKILL.md               AI Agent 的入口、路由和安全边界
assets/osu_skin.db     皮肤元素、字段和术语数据库
references/            按任务加载的领域说明和工具契约
scripts/               CLI 工具实现
tests/                 自动化测试
evals/                 Skill 行为评测样例
```

## 能力边界

- 数据库和静态检查可以证明记录、文件、像素和配置状态，但不能代替在游戏中实际运行验证。
- 没有实际皮肤文件时，AI 不能可靠断言某个 path、SD/`@2x`、动画帧、alpha 或回退结果。
- 混皮时，未确认的跨模式、全局或共享资源默认保留目标版本，并会列为需要确认的项目。
- 生成或分发第三方皮肤前，请自行确认原作者许可和资源授权。

## 许可证

- Python、打包配置和 CI 等代码：[MIT](LICENSE-CODE)
- `SKILL.md`、references、evals 和项目知识库：[CC BY 4.0](LICENSE-KNOWLEDGE)
- 双轨适用范围和第三方材料说明：[LICENSE](LICENSE)
