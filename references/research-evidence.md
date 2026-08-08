# 研究证据到行为规则

复核数据库结论时，运行 `osu-skin db-query "<元素或命令>" --json`。复核图片指标时，运行 `osu-skin image-inspect "<路径>" --json`。记录外部来源 URL、访问日期、版本或 commit，不把脚本 TODO 输出当成证据。

本文件让模型直接使用已整理的外部证据。新增证据按“来源 -> 观察 -> 可迁移规则 -> 适用任务 -> 链接”记录。

## Mania 合并

来源：`Greenest-Guy/osu-mania-Skin-Merger` README、issues #1/#3/#4/#5。

观察：

- 合并按 keycount 选择，不是整目录覆盖；
- `[Mania]` path 指向的图片、默认命名资源、HD receptor、动画和 LN head/tail 都可能遗漏；
- 合并到不同模式皮肤时，目标的菜单、音效和其他 keycount 应保留；
- 大于 9K 的 key layout 需要额外支持，不能硬编码到 4K/7K。

规则：任何 Mania 合并先生成依赖闭包和冲突映射，再复制资源并改 path；写后按 keycount、路径、HD、动画和 H/L/T 复检。

## instafade 和数字

来源：`rednir/OsuSkinMixer` issues #136、#138、#143。

观察：

- instafade 可能改变 `HitCircleOverlap` 的要求；
- 10 以上数字的宽度会导致重叠；
- HD/SD、运行分辨率和生成器使用的资源版本会改变结果；
- 白圈/白边可能来自透明像素或生成素材，而不是游戏随机故障。

规则：诊断 instafade 同时检查数字图、前缀、overlap、HD/SD、分辨率和 alpha；不要只重新生成帧。

## 音频预览

来源：`rednir/OsuSkinMixer` issue #148。

观察：MP3 可能在预览器失败而 WAV/OGG 成功；日志为空不代表游戏或文件一定坏。

规则：报告游戏加载能力和预览器解码能力两个结论，必要时用 ffprobe/ffmpeg 转换副本。

## 透明白边

来源：`RoanH/FringeRemover` README 和 issue/论坛说明。

观察：完全透明像素仍可能保存白色 RGB，缩放和抗锯齿会把它混到可见边缘。

规则：先统计 alpha=0 像素 RGB，再选择 edge bleed 或透明像素修复；保留原文件。

## 客户端文件分类

来源：`RoanH/osuSkinChecker` issue #3、`tools.osuck.net` skinning_tool/skinning_info 分类。

观察：lazer JSON、lazer 专属图片/音频、Skinnable Files List、HD2SD、skin.ini 预览、instafade 和 fringe 修复都是实际需求。

规则：未知文件先按客户端确认分类；Skill 需要覆盖“为什么没生效/怎样处理”而不只是文件名查询。

## 维护

新增外部结论时记录：访问日期、项目/文档版本或 commit、原始问题、可复现输入、结论置信度。社区工具行为不能覆盖数据库和官方文档的明确事实。

## 来源链接

- 官方 skinning：[Skinning](https://osu.ppy.sh/wiki/en/Skinning)、[`skin.ini`](https://osu.ppy.sh/wiki/en/Skinning/skin.ini)、[osu!mania skinning](https://osu.ppy.sh/wiki/en/Skinning/osu%21mania)、[Skinning FAQ](https://osu.ppy.sh/wiki/en/Skinning/FAQ)
- 工具目录：[tools.osuck.net skinning_tool](https://tools.osuck.net/?category=skinning_tool)、[skinning_info](https://tools.osuck.net/?category=skinning_info)、[skins_listing](https://tools.osuck.net/?category=skins_listing)
- 混皮和 Mania：[OsuSkinMixer](https://github.com/rednir/OsuSkinMixer)、[issue #132](https://github.com/rednir/OsuSkinMixer/issues/132)、[issue #136](https://github.com/rednir/OsuSkinMixer/issues/136)、[issue #138](https://github.com/rednir/OsuSkinMixer/issues/138)、[issue #148](https://github.com/rednir/OsuSkinMixer/issues/148)、[osu-mania-Skin-Merger](https://github.com/Greenest-Guy/osu-mania-Skin-Merger)
- Mania 边界：[HD receptors issue](https://github.com/Greenest-Guy/osu-mania-Skin-Merger/issues/1)、[animations issue](https://github.com/Greenest-Guy/osu-mania-Skin-Merger/issues/3)、[LN head/tail issue](https://github.com/Greenest-Guy/osu-mania-Skin-Merger/issues/4)、[key layouts issue](https://github.com/Greenest-Guy/osu-mania-Skin-Merger/issues/5)
- 图片/客户端：[FringeRemover](https://github.com/RoanH/FringeRemover)、[osu-resize](https://github.com/minisbett/osu-resize)、[osuSkinChecker](https://github.com/RoanH/osuSkinChecker)、[lazer files issue](https://github.com/RoanH/osuSkinChecker/issues/3)
