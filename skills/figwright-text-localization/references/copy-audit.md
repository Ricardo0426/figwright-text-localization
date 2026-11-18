# 文案审核脚本

scripts/audit_copy.py 只读显式映射 JSON 并写报告，不直接读取表格/Figma或修改设计。输入来自本轮最新来源与实际可见文字。

    python scripts/audit_copy.py --input audit-input.json --output audit-report.json

--strict 强制大小写敏感。返回码 0 全通过，1 不匹配，2 输入/IO错误；输出不得覆盖输入。

## 输入

顶层仅含非空 items 数组。每项：

- id：唯一标识。
- source_cell：可选的实际来源位置。
- expected：来源完整模块字符串。
- actual：一个实际字符串，或按明确语义顺序排列的非空字符串数组；以单空格组合。
- ignore_case：默认true，--strict强制关闭。
- ignore_list_markers：默认false；开启仅移除行首后跟空白的列表前缀。
- mode：默认exact比较整模块；仅显式映射到较大段落片段时用contains。

见 [audit-input-example.json](audit-input-example.json)。contains只证明子串出现，报告标出范围，须另查其余文字，不能声称整图无旧文案。

归一化为Unicode NFC、空白折叠，保留词边界；数字、小数符号、标点、x/×、单位与连字符不自动互换。

## 脚本之外的核查

脚本不知道来源模块总数，也不检查可见性、截字、字体、蒙版和导出。先完整列举来源，再映射实际文字，检查遗漏、重复与额外旧文案，不能只给已经匹配的片段造输入。

这是保词边界的基础核对。德语视觉大小写、东亚文字人工断行等可能需独立人工判断并记录，不能为通过而删除所有空白。

跨节点仅按明确语义顺序组装。需要从较大节点取模块时记录节点和字符范围，不全图搜索重排词语。
