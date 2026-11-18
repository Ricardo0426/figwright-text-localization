# 恢复原生可编辑文字

## 先判断为何不可编辑或不可见

读取可见链中的 TEXT 与同名文字图片，检查 characters、fills、segments、fontName、fontSize、lineHeight、textAutoResize、opacity、locked 和祖先状态。

常见情况：原生 TEXT 已存在且 visible=true，但 fills=[]，画面由栅格显示；字体被换成默认值、逐段填充为空、行高过小或固定框截字；原生文字与栅格已被移到不同位置；标题脱离画板在顶层覆盖产品；数字组来自智能对象而数字和箭头原本是独立层。

建立 text_id → raster_id → source_layer_id 映射。产品印刷型号、软件截图内文字不因这项任务自动重绘。

## Photoshop 有效样式

只读确认文档 ID、分辨率、画板和可见语言组。需检查智能对象时只打开相关子文档，读完关闭且不回写父稿；保持源 PSD 内容、保存状态和原打开文档集合。

- 取内容、PostScript/family/style、逐段范围、impliedFontSize、impliedLeading、tracking、横纵缩放、transform、大小写与合成样式。
- DOM size 可能是变换前小字号。有效 impliedFontSize（pt）通常乘 resolution / 72 得像素字号，不再乘一次 transform；只有基础 size 时才按已确认的变换推导，并用源字形核验。
- 颜色叠加/渐变效果可覆盖 DOM 原色。区分基础色、效果色和图层 opacity，避免重复乘透明度。
- PS 显示成功不代表 Figma 可 load。实际验证字体加载。没有对应合成斜体时，不自行制作安装字库，按用户偏好处理或说明差异。

## 修复现有 TEXT

优先复用现有节点；一段混合字体、数字单位和颜色使用一个 TEXT 加范围样式。

小批顺序可为：字体/基础字号 → 内容/完整范围样式 → 自动宽度与字距 0 → 行高及明确换行 → 读实际 width/height → 校准位置 → 隐藏对应旧栅格 → 截图。默认显式设置 `textAutoResize: "WIDTH_AND_HEIGHT"`、`letterSpacing: { unit: "PIXELS", value: 0 }`；不沿用导入文字或 PS 原稿的旧字距。

在当前工具版本核验这些已观察行为：

- resize_nodes 可能将文字的自动尺寸模式重置为 NONE；调整后恢复默认 WIDTH_AND_HEIGHT，再读实际宽高。用户明确要求固定宽度时才按其要求选择 HEIGHT 等模式，不能把该例外当作默认。
- set_text 会延续部分旧范围，长短句变化可能整段继承红色，或单位最后一字母继承大号数字。先设整段基准样式，再对最终索引设置完整富文本范围，核对末尾字符；范围样式不要带回旧字距，最后读回节点及范围的字距均为 0。
- 真实字形宽度受字体、大小写、tracking 和横向缩放影响；不能只凭字号估计。

## 对齐字形，不对齐透明边界

栅格可能含透明 padding 和强阴影。用 alpha 求 ink bounds；亮色标题可再以前景亮度排除阴影，深红装饰不能套同阈值。

单独导出的 TEXT 可能被裁到 render bounds，导出 ink=(0,0) 不代表节点没有字形 inset。

需要精确校准时，在临时透明 FRAME 中 clone 文字，放到已知坐标并留足边界，固定 wrapper 尺寸；按明确倍率导出 wrapper，求 ink left/top 与已知放置点的差；目标字形减去 inset 得位置。居中标题按字形中心，左齐正文按字形左边缘。读回并按原尺寸/缩略比例检查，只删本轮临时节点。

旋转、复杂 transform、效果越界和遮罩会影响推导，先用小样验证，不固化阈值或示例坐标。
