# 限定schema定位补充（保留v1及其未定位结果）

v1精确标题`Original MCP ID`未匹配，输出schema_unresolved；尚无功能/蛋白数值解析。为核原始表实际字段，允许仅输出符合以下metadata关键词的字符串及其单元地址：包含`original`、规范化后等于`mcp`/`mcpid`/`originalmcpid`/`replicate`/`sampleid`。不输出其他字符串或任何数值单元，不猜前四行是表头。

先保存metadata候选，再仅以被源文件实际显示的唯一ID标题定位完整表头。其余v1禁令和暴露记录全部保留；这次解析修正不改变科学候选或观察结果。

初次metadata检索显示EGFR表A1带重复说明，Q1/T1又重复标题；允许检索含`MCP`的标题/ID字符串以核真实原文拼写。ID仅作索引，不读取功能分组、分析入选或数值；重复标题不凭结果选列。
