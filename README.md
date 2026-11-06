# Quality Check

用于核验供应商交付题目的质检工具包：检查交付材料是否完整、题目是否可解、参考答案与评分是否可靠，以及模型试跑是否暴露质量问题，最终形成逐题验收建议和修复复测要求。

**Implementation Review → 控制验证 → 三模型各 4 次 → 逐次轨迹分析 → 统一报告**

## 如何核验供应商交付

1. 登记供应商、交付批次、题目清单、原包版本与哈希，以及约定的验收要求；核对题面、输入材料、参考答案或参考解、评分器及运行说明的完整性。
2. 按下列五阶段开展工作；可使用 agent 辅助读取材料、执行已配置实验、分析轨迹和汇总结果。
3. 独立核验供应商关于可解性、难度、评分正确性和运行结果的声明，不把供应商自测报告直接当作验证结论。
4. 形成“可验收 / 需修复后复测 / 证据不足”的逐题建议，列出缺失材料、问题证据及验收条件；供应商修复后按新版本复测，保留原交付与旧结论。

| 阶段 | 质检重点 | 工具辅助 |
|---|---|---|
| Implementation Review | 题意、参考解、评分实现、数据与答案隔离 | 16 项 rubric 与补充清单 |
| 控制验证 | 参考解、空解、简单基线、等价解与异常输入的评分是否合理 | 控制协议及可选探针 |
| 三模型各 4 次 | 十二个正式运行的协议、独立性与结果完整性 | 已配置的执行器与汇总脚本 |
| 逐次轨迹分析 | 成败原因、得分有效性及是否存在题目缺陷 | 8 项 rubric 与原始证据索引 |
| 统一报告 | 逐题质量判断、问题影响和复测条件 | 统一报告模板 |

质检负责人负责质量判断，外部专家可参与复核；模型 reviewer 提供分析建议。报告须区分供应商声明、实际验证结果、自动分析和已复核结论，未经负责人确认的结论标为草稿。采购或最终接收决定由委托方依据约定的验收要求作出。

## 安装

克隆本仓库后，将 `skills/data-quality-review` 整个目录复制到你的工具支持的 skills 目录。项目级示例（在目标项目运行，仓库路径自行替换）：

```sh
# Codex 项目
mkdir -p .agents/skills
cp -R /path/to/quality-check/skills/data-quality-review .agents/skills/
# Claude Code 项目
mkdir -p .claude/skills
cp -R /path/to/quality-check/skills/data-quality-review .claude/skills/
```

已有同名技能时先比较版本再替换。目录内部结构必须保持完整。

## 使用

向支持技能的 agent 发出：

> 使用 data-quality-review 核验供应商交付的 ./incoming 题包，报告输出到 ./qc/batch-001。核对交付清单及约定的验收要求，独立验证供应商声明，逐题给出验收建议与修复复测条件。用途为评测，按 Implementation Review → 控制验证 → 三模型各 4 次 → 逐次轨迹分析 → 统一报告执行。模型、reviewer 和预算读取我的项目配置；缺少时先完成不依赖这些配置的审查。

运行前准备题目清单、任务用途、目标能力、评分协议、三个实际模型 ID、独立模型 reviewer、质检复核负责人、预算及执行环境。默认模型角色是 Opus、DeepSeek、GLM，可以由用户指定替换；不假设任何 API 可用。凭据通过环境变量提供，不写入仓库。

本仓库是 agent 技能与确定性汇总工具，**不是自动完成十二次运行的一键调度器**。安装不会启动模型或 Docker。技能协调已有 harness/本地执行器；Harbor 题可选择 task-review 或 train-tasks 适配。

## 开始前需要提供什么

不用自己把所有配置整理成文件。把题包位置告诉 AI，让它先找项目中已有的配置；只需补充它找不到的信息。

| 信息 | 你需要提供，或让 AI 查找 |
|---|---|
| 待检题包 | 本地目录或可访问的交付地址；供应商清单、验收要求有则一并提供 |
| 模型访问 | 三个 solver 与 reviewer 的实际模型 ID、API 地址及调用方式；可沿用已有 agent 登录或网关配置 |
| 凭据位置 | 已设置的环境变量名称、项目 `.env` 路径或已有登录配置位置；不必把密钥粘贴到聊天里 |
| 执行环境 | 本机还是已授权的远程环境；已有运行脚本、Harbor/Docker 或调度器配置在哪里 |
| 范围与预算 | 检查哪些题、每次时间/token 限制，以及允许的费用或总运行上限 |
| 输出位置 | 报告保存目录；没指定时 AI 可在项目内创建批次目录 |

可以直接对 AI 说：

> 题包在 `<题包路径>`，请用这个 skill 质检。先查本项目的 README、运行脚本、配置文件及已有模型环境变量，复用能用的 API、模型和执行方式，不要显示密钥。缺什么再集中问我。先完成审题和运行准备，模型与预算明确后按三模型各四次运行，逐次分析并生成报告。

AI 应先检查项目文档、已有命令和配置，再查看明确相关的环境变量是否已设置；不要遍历无关私人目录或输出凭据值。多个配置冲突时说明差异并询问。已有授权和明确预算可直接沿用；未找到模型访问、执行方式或预算时先完成可做的审查，不猜配置、不擅自启动付费批次。实际运行前用现有工具的帮助信息及预算内最小请求确认接入可用，检查通过后继续正式流程。

## 内容

- [技能入口](skills/data-quality-review/SKILL.md)
- [16 项 Implementation rubric](skills/data-quality-review/rubrics/task-implementation.toml)
- [8 项逐次轨迹 rubric](skills/data-quality-review/rubrics/trial-analysis.toml)
- [控制验证](skills/data-quality-review/references/controls.md)
- [模型与执行配置](skills/data-quality-review/references/execution.md)
- [统计口径](skills/data-quality-review/references/reporting.md)
- [统一报告模板](skills/data-quality-review/assets/report-template.md)
- [来源与改写](skills/data-quality-review/references/provenance.md)

## 汇总与验证

汇总脚本只依赖 Python 标准库，输入使用实际 trial 记录，不能直接拿 example_only 示例当实测数据。

```sh
python3 skills/data-quality-review/scripts/summarize_trials.py /path/to/trial-records.jsonl \
  --out-dir /path/to/summary --models model-a model-b model-c --pair model-b model-c
python3 -m unittest discover -s skills/data-quality-review/scripts -p 'test_*.py'
```

输出原始明细 CSV、JSONL 和分组 summary.json，支持四次独立运行、pass@4 与双方 pass@4。所有未跑题需另与 intake 对账。不同题型、协议和指标不混算；未知费用与时间不当作零。

可选动态工具需要对应的 Harbor、Docker、模型访问和工具自身依赖。其原始报告不自动等于本包标准的验收结果。当前发布内容不含客户数据、原题、运行记录或凭据。
