# Figwright Text Localization

用于 Figma 原生可编辑文字恢复、多语言版本制作、文案核对和分组导出的 Codex 技能。

## 安装

在 Codex 中使用 skill-installer 安装本仓库的 skills/figwright-text-localization 目录。也可将该目录复制到自己的 Codex skills 目录。

安装后在下一轮对话中调用：

    $figwright-text-localization

## 工作流程

- 将文字图片或异常 TEXT 恢复为原生可编辑文字，参考 Photoshop 的有效字体字号与效果。
- 按文案表复制独立语言版本，保留当前产品构图和用户已调整的版式。
- 逐模块核对词间空格、重音、数字、单位和条件，并检查额外旧文案。
- 按最新 Figma 状态导出分组图片，核验数量、尺寸、格式与覆盖结果。

新建、恢复或制作语言副本时，文字默认使用自动宽度（WIDTH_AND_HEIGHT），字距为 0；仅校对和重新导出时不重设已有版式。

## 依赖

设计读写需要当前可连接的 Figwright 插件；参考 Photoshop 源文档时需要可用的 Photoshop 工具。工具名称和参数以当前环境为准。

附带的 scripts/audit_copy.py 仅使用 Python 标准库，对显式映射的来源文案和实际文字做只读比对。它不连接 Figma，也不代替来源覆盖、可见性或视觉审核。

## 目录

- skills/figwright-text-localization/SKILL.md：技能入口
- references/：文字恢复、多语言排版、导出与文案审核说明
- scripts/audit_copy.py：保留词边界的审核脚本

本仓库不包含产品素材、字体文件、项目文案或私有设计数据。

