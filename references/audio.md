# osu! skin 音频处理手册

检查音频时，运行 `osu-skin audio-inspect "<音频或皮肤目录>" --json`。检查 hitsound 资源族时追加 `--family`；检查循环音效时追加 `--loop`。

## 先查元素

从数据库确认：`looped`、支持格式、是否可被谱面覆盖、是否需要 supporter、适用模式和 `client`。不要因为文件扩展名存在就认定游戏会播放。

## hitsound 资源族

按以下维度定位和替换：

- sample set：Normal、Soft、Drum；
- 用途：`hitnormal`、`hitclap`、`hitfinish`、`hitwhistle`；
- 模式：std/taiko/catch/mania 可能使用不同文件族；
- beatmap 覆盖：谱面或 sample set 可能优先于皮肤默认音效；
- fallback：缺失文件可能回退到默认音效，不等于静音。

用户说“换 hitsound”时先问或从请求判断是单个音效、完整 sample set、某模式还是全部模式。

## 格式诊断

对音频报告：真实容器/codec、采样率、声道、位深、时长、峰值、开头/结尾静音和解码错误。分开记录：

1. osu! 理论支持的格式；
2. 当前客户端可能加载的格式；
3. 当前预览器/库能否解码。

MP3 预览失败不能直接证明游戏不支持；扩展名为 `.wav` 也不代表文件内部是 PCM WAV。

## 转码与处理

- 默认保留源文件，输出到新目录或新文件；
- 避免重复有损转码；
- 转码后重新检查 codec、采样率、声道、时长和峰值；
- 归一化前记录原始峰值/响度，避免把 hitsound 放大到削波；
- 去除静音时保留必要 attack/release，不要截断点击声；
- 循环音效检查首尾波形、DC offset 和 crossfade click；
- 用户要静音时生成合法静音文件，除非用户明确要触发 fallback。

## 报告格式

```text
客户端/模式：
元素和 sample set：
原文件 codec/指标：
预览结果：
游戏加载风险：
替换文件族：
验证结果：
```
