# Rubric 与逐次轨迹分析接入

两份权威 rubric 随本技能分发：`rubrics/task-implementation.toml`、`rubrics/trial-analysis.toml`。运行前计算 SHA-256，记录版本 1.0.0；上游 task-review 或 train-tasks 只是可选执行工具，不替换本包标准。

## 执行方式

- 用已有 reviewer 按本包 rubric 输出逐项结论与证据，可用于任意题型。不依赖 Harbor；使用人工审查时明确 reviewer 类型，不冒称自动分析。
- task-review / Harbor：确认所用版本 CLI 与 schema 支持后，将本包 `trial-analysis.toml` 传给 `harbor analyze` 的 rubric 参数；不要默认使用上游 rubric。保留原始 Harbor job。
- train-tasks：`trajectory_analysis index` 可生成原始试验索引；`analyze` 默认只分析未通过项，必须用 `--all` 覆盖成功项。其内置 criteria 和检查器含训练题语义，不能直接冒充本包 rubric。若采用，先在独立适配副本将本包八项映射成其 name/axis/description/guidance 结构，验证生成的 brief、结果字段和证据引用，记录 diff/hash；不支持适配则选前两种方式。

不要强制 reset 用户 checkout 或静默升级依赖。命令、参数、工具版本由实际环境确认。索引生成不是完成轨迹分析。工具不可用时保留可做的审查，并明确自动分析未完成。

## 全量覆盖与证据

以 intake 的题目 × 三模型 × 四次清单核对正式槽位，再加入所有真实恢复 attempt。每条记录 expected、produced、completed/failed/missing/not_applicable 及原因。未运行槽位单列，不能因没有轨迹而消失。

每份分析至少包含 task_id、task_version、run_id、repeat_index、attempt、八项 checks（name、outcome、explanation、evidence）、过程摘要、失败或成功归因、修复建议。PASS/FAIL 的证据必须指向原始文件或轨迹真实 step_id；检查文件存在、行号和 step_id 有效，摘录可追溯。NOT_APPLICABLE 说明原因；缺材料标 INSUFFICIENT_EVIDENCE:。格式合格不等于实质判断正确。

保存 analysis-provenance.json：本包 rubric 版本和哈希、执行工具来源与 commit、dirty patch/hash、题目版本、trial ID、reviewer 模型与 agent 版本、真实命令（移除凭据）、时间。保存原始分析输出和 analysis-coverage.json。

分析员只接触隔离副本；路径修复和轨迹适配记录 diff、保留原文。没有原评分环境时仅依据现有输出判断，不声称重跑过。若适配工具跳过大文件或链接，列出缺失及影响，不称无损。

人工复核关键动作、首次错误、循环、恢复、得分捷径及跨模型差异。外部阻塞不抹去此前证据；裁判失败不触发 solver 重跑；原始分数不变。未经支持的归因保持不确定。
