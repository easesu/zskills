# zskills

Claude Code 自定义技能集合，用于提升多语言项目中的开发效率。

## 技能列表

### i18n-sync

同步 i18n 翻译键，以 `en.json` 为基准，对齐其他语言文件的键结构。

**触发词：** `补全翻译`、`同步翻译`、`sync translations`、`i18n key diff`

**使用方法：**

在 Claude Code 中直接说"补全翻译"或"同步翻译"，然后提供以下信息：

1. 基准文件路径（如 `i18n/locales/subscription/en.json`）
2. 同步范围（整个文件或某个 key path，如 `purchaseModule`）
3. 目标语言（默认全部非 en 语言，也可指定如 `zh-CN,ja`）

技能会先对比差异、展示变更计划，确认后再执行同步。同步后需要手动将英文占位文本翻译为对应语言。
