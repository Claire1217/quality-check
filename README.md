# Quality Check

核验供应商交付题目的 AI skill，检查题目可解性、评分正确性和实际模型表现，输出逐题验收建议、问题证据及修复要求。适用于不同领域的训练与评测题目。

## 质检流程

**Implementation Review → 控制验证 → 三模型各 4 次 → 逐次轨迹分析 → 统一报告**

- **审题**：按 16 项 rubric 检查题面、材料、参考解与评分器。
- **控制验证**：运行参考解、空解和适用的异常输入，核验评分。
- **模型试跑**：默认 Opus、DeepSeek、GLM 各独立运行 4 次，模型可替换。
- **轨迹分析**：按 8 项 rubric 逐次分析成败原因与得分有效性。
- **报告**：逐题给出可验收、修复后复测或证据不足的建议。

## 安装

克隆仓库，将 `skills/data-quality-review` 文件夹复制到目标项目的技能目录：

| 工具 | 目标目录 |
|---|---|
| Codex | `.agents/skills/` |
| Claude Code | `.claude/skills/` |

## 使用

安装后对 AI 说：

> 用 data-quality-review 质检 `<题包路径>`，报告保存到 `<输出目录>`。先查项目已有的模型 API、运行脚本和配置，缺什么再问我。按完整五阶段流程执行，预算为 `<时间或费用上限>`。

需要提供或让 AI 从项目中查找：

- **题包与要求**：交付目录、检查范围、验收要求。
- **模型接入**：三个做题模型及分析模型的 ID、API 地址、凭据环境变量或已有登录配置。
- **执行与预算**：本机或远程运行环境、运行方式、时间或费用上限。

密钥保留在环境变量或私有配置中，无需粘贴到聊天。模型执行复用已有工具；配置不足时先审题，再补齐运行条件。

## 标准与报告

[技能说明](skills/data-quality-review/SKILL.md) · [审题 rubric](skills/data-quality-review/rubrics/task-implementation.toml) · [轨迹 rubric](skills/data-quality-review/rubrics/trial-analysis.toml) · [报告模板](skills/data-quality-review/assets/report-template.md) · [运行配置](skills/data-quality-review/references/execution.md)
