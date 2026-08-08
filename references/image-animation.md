# 图片、alpha、@2x 和动画处理手册

检查图片时，运行 `osu-skin image-inspect "<路径>" --transparent-rgb --json`；检查动画时追加 `--animation`。执行通用图片变换前，运行 `osu-skin image-transform "<路径>" --operation <操作> --output "<输出>" --dry-run`。遇到“投 50px”时停止通用变换，改读 `mania-hold-body.md`。

用户明确使用 lazer 且症状是压扁、拉长、比例错误或重复时，再读取 `lazer-image-scaling.md`；不要只按原图纵横比推断显示尺寸。

## 图片检查顺序

对每张图片先记录：格式、文件大小、像素尺寸、颜色模式、位深、是否有 alpha、alpha 的最小/最大值、alpha=0/半透明/不透明像素数量。

### “透明”四种不同结论

1. 格式支持 alpha：PNG/RGBA 等，但可能所有像素都不透明。
2. 存在 alpha 通道：有 A 通道，不等于有透明像素。
3. 存在透明像素：至少一个 alpha<255；还要区分半透明和 alpha=0。
4. 透明区域有 fringe 风险：alpha=0 像素的 RGB 与可见边缘颜色不一致，缩放/抗锯齿可能出现白边或黑边。

回答“是否透明”时至少给出前 3 项的像素统计；用户描述白边时追加第 4 项。

## 元素尺寸和 origin

从数据库读取 `suggested_size`、`origin`、`blend_mode`、`hd_supported`：

- `suggested_size` 是建议的 SD 尺寸，不是所有屏幕都必须使用的硬限制；偏离时报告风险。
- `origin` 决定图片定位锚点；裁切透明边可能改变视觉位置，即使元素像素内容未变。
- `blend_mode=Additive` 的黑色/透明处理与 Normal 元素不同；改色前检查混合方式。
- `hd_supported=0` 时不要自动创建 `@2x` 并承诺会生效。

## @2x/SD

1. `name@2x.png` 通常对应 `name.png`，目标尺寸应严格 2:1。
2. 先检查两者是否同一资源的缩放版本；同名不代表内容一致。
3. 像素风默认 nearest；平滑 UI 素材使用高质量缩放并记录过滤器。
4. 已有 SD/HD 时默认不覆盖，先报告冲突。
5. 修改一个版本后检查另一个版本，否则可能出现“高分辨率正常、低分辨率异常”。
6. 配置中的路径、元素 HD 支持、运行分辨率和客户端共同决定实际选择。

## 透明边缘和白边

白边常见原因是透明像素仍保存白色 RGB，游戏在缩放时混入边缘。排查顺序：

1. 统计 alpha=0 像素 RGB 的主要颜色；
2. 查看可见边缘与透明边缘是否颜色不连续；
3. 检查是否经过预乘 alpha/非预乘 alpha 转换；
4. 检查缩放过滤和画布边缘；
5. 选择 edge bleed 或透明像素颜色修复；
6. 重新生成 SD/HD 后再检查。

不要默认把所有透明像素涂黑；Additive 元素和浅色边缘可能因此变黑。

## 动画识别

把以下文件视为同一帧组：base、`-0..n`、无分隔数字帧、`@2x` 变体以及数据库声明的 pattern。

检查项：

- 是否从 0 开始；
- 是否断帧、重复帧或多余帧；
- 所有帧尺寸、颜色模式和 alpha 是否一致；
- FPS 来自固定 animation.fps、`AnimationFramerate`、BPM 还是 Mania `LightFramePerSecond`；
- `-0` 是否隐藏 base，或 stable hitXX 是否始终加载 base；
- 帧是否属于正确的模式和客户端。

复制/重命名/删除动画时，整组操作并在写后重新列帧。

## instafade

instafade 不只是生成 hitcircle 帧，还可能影响：

- `HitCirclePrefix` 指向的数字图；
- `[Fonts] HitCircleOverlap`；
- HD/SD 资源选择；
- 运行分辨率和数字宽度；
- 帧 base/`-0` 规则。

出现 10 以上数字重叠或白圈时，先保留源皮肤，比较生成前后 hitcircle、数字尺寸和 overlap，再决定修复。
