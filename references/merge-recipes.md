# 混皮、资源组和 lite 配方

合并 Mania 前，运行 `osu-skin mania-analyze "<源皮肤>" --keys <N> --client stable|lazer --dependencies --json`，并对目标皮肤运行同一命令。核对图片组时运行 `osu-skin image-inspect "<资源路径>" --animation --json`。

## 统一混皮原则

1. 先确认客户端、模式、输入皮肤和输出目录。
2. 先定义资源组，再决定复制文件；不要按目录全量覆盖。
3. 对每个资源组收集：配置字段、path、默认回退、SD、`@2x`、动画、关联音频和谱面覆盖。
4. 冲突时先生成映射；重命名后同步修改所有引用。
5. 默认生成新目录，保留源皮肤和作者信息。
6. 写后重新检查资源闭包，不以“文件复制成功”作为完成标准。

## 常用资源组

### cursor

包含 `cursor.png`、`cursormiddle.png`、`cursortrail.png` 和动画/HD 变体；同时检查 `CursorCentre`、`CursorExpand`、`CursorRotate`、`CursorTrailRotate`。只换 cursor 而保留旧 trail 可能产生尺寸或旋转不一致。

### std gameplay

按以下子组处理：

- hitcircle：`hitcircle`、overlay、approachcircle、数字前缀和 overlap；
- slider：slider body、followcircle、endcircle、scorepoint、reversearrow、ball；
- spinner：background、circle、approachcircle、metre、rpm、warning；
- followpoint：base、`-0..n`、blend mode 和帧率。

不要把菜单、结算和 gameplay 混为一个组，除非用户明确要求整套替换。

### Mania keycount

只复制源的 `Keys: N` 段及其完整依赖；保留目标其他 keycount、std/taiko/catch、菜单和音效。依赖见 `mania.md`。

### hitsound

按 Normal/Soft/Drum 和用途族处理；替换一个文件前说明其他文件可能仍来自目标皮肤。

### 菜单/选歌/结算

按数据库标签选择 `菜单界面`、`选歌界面`、`结算界面`；检查 supporter 和 stable/lazer。大号 ranking 图在 lazer 的实际覆盖要单独确认。

## lite 配方

1. 询问保留的客户端、模式和界面。
2. 列出会删除的资源组、被删除的配置和预计保留的 fallback。
3. 复制到新目录后执行删除，不原地删除第三方皮肤。
4. 动画可以保留 base、首帧或静态代表帧；必须说明选择。
5. 删除后重新检查 `skin.ini` path、数据库必需资源和客户端 fallback。

## 来源和授权

记录源皮肤名、作者、资源组、复制日期和修改内容。不要把混合结果描述成全部原创；分发前提醒用户自行确认作者许可。
