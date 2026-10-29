# Maya Workflow Kit for Blender · 简体中文本地化

[English](README.en.md) · [汉化与维护说明](LOCALIZATION.md) · [GPL-3.0-or-later](LICENSE)

将 Maya 风格工作流带入 Blender，并在 Blender 使用**简体中文界面**时显示中文。基于 [5hyuns/maya-workflow-kit-for-blender](https://github.com/5hyuns/maya-workflow-kit-for-blender)，保留上游操作符、场景命名、快捷键和英文工作流。

这是独立的社区本地化衍生版本；原项目作者、许可证和资产声明均保留。上游基线及本地化修改详见 [UPSTREAM.json](UPSTREAM.json) 和 [LOCALIZATION.md](LOCALIZATION.md)。

## 安装

1. 从本仓库 **Releases** 下载 `maya-workflow-kit-0.6.2-zh.2.zip`，不要选择 GitHub 自动生成的源码压缩包。
2. 在 Blender 中打开“编辑 → 偏好设置 → 获取扩展”，在右上角菜单选择“从磁盘安装”，选中 ZIP 并启用扩展。
3. 将“偏好设置 → 界面 → 翻译”的语言设为**简体中文**，启用“翻译界面”。
4. 点击顶栏的 Maya 按钮，或按 `Ctrl+Alt+Shift+M`，启用 Maya 工作流。

切回英文后，插件恢复英文显示，无需重新启用扩展。关闭“翻译界面”时，自绘界面使用英文；原生工具提示遵循 Blender 自身的翻译开关。当前提供简体中文，繁体中文不会触发简体汉化。

> 扩展内部 ID 为 `allset`。本地化版与上游版使用同一 ID，安装前请停用或移除另一版本，避免同时启用。

## 功能与术语

覆盖热盒、标记菜单、通道盒、属性编辑器、工具架、菜单集、工具选项、建模、UV、绑定、蒙皮、动画、灯光及渲染等界面。译文目录包含 **7,677 个不同原文**，并为多义词保留语境差异。

| Maya 英文 | 中文 |
|---|---|
| Channel Box | 通道盒 |
| Construction History | 构建历史 |
| Freeze Transformations | 冻结变换 |
| Set Driven Key | 设置驱动关键帧 |
| Paint Skin Weights | 绘制蒙皮权重 |
| UV Shell | UV 壳 |
| Playblast | 播放预览 |
| Clamped / Stepped | 钳制 / 阶跃 |

用户对象名、自定义工具架与按钮名称、节点标识、命令参数、文件路径和脚本内容保持原样。运行时采用整句及完整消息模板查找，不进行模糊词组替换。

## 兼容与验证

扩展清单支持 Blender **4.5–5.2**。本地化版已在 **5.1.0 / 5.2.2** 完成 60 项语言与生命周期检查；ZIP 隔离安装后的 16 项语言检查及 16 项相关上游回归测试通过。尚未在 4.5 重测，也未对所有面板和场景状态逐一做人工视觉验收。

本插件提供 Maya 风格的 Blender 操作，功能仍受 Blender 能力限制；不支持直接打开 Maya `.ma` / `.mb` 文件，也不执行 MEL。上游完整功能说明请参见[原项目](https://github.com/5hyuns/maya-workflow-kit-for-blender)。

## 从源码构建

```sh
python tools/build.py
```

输出到 `dist/maya-workflow-kit-0.6.2-zh.2.zip`，目录根部含 `blender_manifest.toml`，可直接在 Blender 中安装。

修改译文并重新编译运行时目录：

```sh
python tools/build_runtime_catalog.py
python tools/build.py
```

[完整译文审阅稿](docs/localization_review/全量译文审阅稿.md)包含英文、中文、使用位置与语境；欢迎用具体菜单路径、原文及建议译法提交 Issue 或 PR。

## 许可证与鸣谢

原项目由 ohnsk / 5hyuns 开发；Python 代码使用 **GPL-3.0-or-later**。原项目自行创作的非代码资产按 [ASSETS_LICENSE.txt](src/allset/ASSETS_LICENSE.txt) 使用 **CC0-1.0**。本地化及相关修改保持 GPL-3.0-or-later，相关本地 Blender 中文词条沿用 Blender 的 GPL 许可。

Maya、Autodesk 属于其各自权利人。本项目与 Autodesk 或 Blender Foundation 无隶属关系，未获得其认可或赞助，也不包含 Autodesk 的代码、图标或 MEL 脚本。
