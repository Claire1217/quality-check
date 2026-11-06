# 逐次记录、分数/时间对比与完整报告

## 一个 trial 一条记录

按 `assets/trial-record.example.json` 建立 `trial-records.jsonl`，或 JSON 数组/`{"trials":[...]}`。示例中的 example_only 必须在真实记录中移除或设 false。原始目录与结果保持不变，规范化记录是证据索引，不替代原文件。

必填字段：`run_id`、`dataset_id`、`task_id`、`task_version`、`protocol_id`、`model_id`、`role`、`repeat_index`、`attempt`、`selected_for_summary`、`status`、`valid_for_comparison`、`metric_id`、`metric_kind`、`score_direction`、`score`、`passed`、`pass_rule_id`、`times_seconds`。未知值用 null，布尔必须是真正 JSON boolean。

- role 为 solver / control / analysis。参考解、负控制、裁判不进入三模型解题统计。
- task_version 是同一道题的来源指纹或可追溯版本；protocol_id 代表影响可比性的 harness、工具、预算与适配。不要按机器/模型名随意拆 protocol，也不能把 OCR/GUI、不同输出上限假装同协议。
- metric_kind：binary（原生通过）、continuous、answer_key_match、ppl。metric_id 应标明具体指标，不能把所有题都泛写 score 后混平均。
- score_direction 为 higher / lower。score 保留原值，8.7 这类距离不压成 0–1；通过与否来自预先声明的 pass_rule_id。无通过定义时 passed=null、pass_rule_id=null。
- status：completed / timeout / api_error / infra_error / verifier_error / interrupted / running / blocked / deferred / paused。timeout 是否构成有效预算内失败需结合评分和轨迹核定，不机械推断 valid_for_comparison。
- valid_for_comparison 是人工核验的实验有效性，不等于通过。API 失败、材料缺失、评分失效不计作可比较的模型失败；原预算超时可保留为有效的预算内未完成，同时披露原因。
- selected_for_summary 明确选择正式 attempt，同题版本/协议/指标/模型/运行槽位 repeat_index 只有一个；所有原失败保留，选取理由写 selection_reason。不能自动取最高分、最短时间或最后一次。
- times_seconds 数值为秒，包括 queue/preparation/agent/verifier/trial_wall/recovery/analysis。各阶段有实测才写；分析耗时不加入 solver 解题时间；阶段有重叠时不把它们相加冒充墙钟时间。
- evidence 记录 raw_result/trajectory/submission/verifier_output/analysis_result/analysis_provenance 的真实位置和需要的哈希。analysis_status 区分 pending/completed/failed/blocked/not_applicable，不能由文件名推定完成。

## 四次运行与 pass@4

每题每模型 repeat_index=1..4 是四次独立运行，attempt 是同一槽位的基础设施恢复次数，二者不可混淆。保留每次分数、状态、通过与耗时。批次 pass@4 分母仅含同版本同协议下四次都有效、有分数且有明确通过判定的题目，分子为其中至少一次通过的题目；不完整题目单列。无阈值记不适用。单次通过率使用有效且有通过判定的运行数作分母。

正文使用 ../assets/report-template.md，Implementation Review 与轨迹分析分别呈现，最后综合判断。

## 四次试跑确定性汇总工具

脚本要求每条 solver 记录显式提供 repeat_index=1..4；历史一次运行需先核验版本、协议及复用依据，再在独立规范化副本标为 repeat_index=1，不改原始证据。attempt 用于同一槽位恢复，禁止把重试当成新槽位。

```bash
python3 "$SKILL_DIR/scripts/summarize_trials.py" \
  /absolute/batch/trial-records.jsonl --out-dir /absolute/batch/summary \
  --models model-a model-b model-c --pair model-b model-c
```

输出 `trials.csv`（含所有记录的原分数与阶段时间）、保留全部字段的 `records.jsonl` 与 `summary.json`（schema_version=2）。仅使用显式选中的 solver；按数据集、protocol、metric_kind、metric_id、方向和通过规则分组，不混异质分数。它验证重复 run、重复选中 attempt 和字段，不读取凭据或调用 API，不把 CSV 直接伪装成 Excel。

配置选定的两个模型双过口径是 **双方 pass@4**：同题同版本同协议、同指标与通过规则下，两边各有 4 次有效且有明确通过判定的选中记录才进入 eligible_task_pairs 分母；双方各自至少一次通过计入 both_passed_tasks。两模型成功不要求发生在相同 repeat_index。无阈值、无完整有效配对分别计数，分母为零时 rate=null。binary 和答案匹配率不混。

每模型保留全部 attempt 状态、选中状态、单次通过率、pass_at_4_eligible_tasks、pass_at_4_passed_tasks、pass_at_4，以及逐题缺槽位/无效槽位/无阈值槽位明细。missing_selected_repeats 表示缺选中的正式记录，可能已尝试但尚未选入，不能直接宣称从未运行。脚本仅覆盖输入 solver 中出现过的题目版本；完全没有记录的题目必须与 intake 对账，不能靠脚本推断整包完成。

时间给每题三个模型的 agent 秒数及 trial 总秒数；汇总工具另报有效样本 agent 中位数与计数。不同硬件、API延迟、模型思考设置、工具协议会影响时间，披露实际配置，不能把更快直接等同更聪明。计费以实测用量/账单为准，缺定价或用量不猜美元金额。

## 报告与 Excel

正文至少回答：

1. 覆盖：每数据集总题数、每模型尝试/有效完成/失败/异常/未跑，哪些暂缓/暂停/材料缺失，试跑完成与证据验收分开。
2. 难度：分数/时间矩阵、配置选定的两个模型 双过比例与分母、基准模型对照、连续指标原尺度、样例范围和协议差异。双过但耗时很长不自动归为简单。
3. 轨迹：本包 rubric 各项原始结论、完成率与失败分析数；逐题过程，关键事件，模型分歧和证据。成功是否真实满足目标与失败原因两边都审。
4. 评分与交付：题面/评分一致性、参考/空解控制、已发现的捷径、隐藏材料隔离、数据依赖完整性、适配与复现条件。
5. 效率成本：准备/解题/评分/API故障恢复/裁判分别记录，token/工具/实验迭代有证据才统计。
6. 技术与采购建议：哪些优先验收、挑题、修复复测、暂缓或证据不足；逐个修复项有证据和验收条件。缺报价不判断性价比，技术合格不等于批准购买。
7. 逐题附录：所有 attempt、版本、配置、分数、阶段时间、异常、提交与分析证据索引。单次公开样例不能外推整包通过率/缺陷率或稳定成功率。

Excel 建议包含数据集总览、逐题三模型对比、全部运行记录、轨迹分析、问题与修复、时间用量。保持原明细，更新而非删掉旧错误。正式 xlsx 和正文文档遵守对应 artifact skill 的生成/检查流程。

存在阻塞不无限等待才写报告；正文标清完成范围和缺口。主控不会在聊天结束后自动醒来，只有用户要求后续通知/周期跟踪时才配置自动化。

SKILL_DIR 由调用者设为本技能实际目录。汇总只覆盖输入记录；必须用 intake 冻结的题目 × 模型清单另行核对未跑项，不能从现有记录推断全量覆盖。
