# Quality Check

面向训练与评测数据的通用质检技能，覆盖 Agent 题包、问答和原生 PPL 数据。不限定学科，不绑定内部平台。

**Implementation Review → 控制验证 → 三模型各 4 次 → 逐次轨迹分析 → 统一报告**

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

> 使用 data-quality-review 检查 ./incoming，报告输出到 ./qc/batch-001。用途为评测，按 Implementation Review → 控制验证 → 三模型各 4 次 → 逐次轨迹分析 → 统一报告执行。模型、reviewer 和预算读取我的项目配置；缺少时先完成不依赖这些配置的审查。

运行前准备题目清单、任务用途、目标能力、评分协议、三个实际模型 ID、独立 reviewer、预算及执行环境。默认模型角色是 Opus、DeepSeek、GLM，可以由用户指定替换；不假设任何 API 可用。凭据通过环境变量提供，不写入仓库。

本仓库是 agent 技能与确定性汇总工具，**不是自动完成十二次运行的一键调度器**。安装不会启动模型或 Docker。技能协调已有 harness/本地执行器；Harbor 题可选择 task-review 或 train-tasks 适配。

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
