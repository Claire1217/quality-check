# 可移植运行配置

把配置和输出存放在用户项目的批次目录，不写入已安装 skill。所有路径相对配置文件解析；本技能中的相对链接相对 SKILL.md 解析。

建议批次结构：intake.json（来源/哈希/题目清单/抽样范围）、run-config.json（模型与协议）、findings.json、trial-records.jsonl、evidence-index.json、runs/、analysis/、summary/、report.md。

run-config 至少记录：

- source、output_dir、task_ids、模型的真实 ID 与 agent、reviewer。
- provider base URL、凭据环境变量名（不保存值）。
- executor 类型 local/ssh/existing-scheduler，机器资源和并发上限。
- 本包 rubric 版本与哈希；可选 task-review/train-tasks checkout 路径、commit 与适配 diff；Harbor/agent 版本。
- 题目时限、输出 token 上限、协议 ID、重试上限、抽样理由。

模型选择沿用用户已有配置。历史工作流用过 Opus、DeepSeek、GLM；这些是实例，不是可用性保证，也不要求别人拥有相同 API。用两个待比较模型配置 --pair，第三个作为对照。模型/预算缺失先准备实验，不猜测后直接调用。

已有 CCM 或其他调度器时复用其持久化任务、心跳与回收机制；没有则按本地资源顺序执行。不要求安装 CCM。运行前检查原生 harness 的 --help、版本及一个最小环境控制；不要把历史命令当当前有效接口。

默认每题 Opus、DS、GLM 各 4 个正式运行槽位，记为 repeat_index=1..4；每个槽位可有恢复 attempt，但只能选中一个 attempt 进入汇总。仅已定位的部署/API 故障可恢复一次，用户规定优先。先查旧进程是否仍活跃。恢复失败后记录 blocked/error，继续其他独立工作，不无限重试。用户暂停的批次保持暂停。

每个 attempt 保存原始配置、开始结束、score、exception、trajectory、提交和 verifier 输出。预期题目 × 模型清单也要记录，未执行组合不可因没有 trial 文件而消失。原始文件不可覆盖；规范化记录引用原文件及其哈希。
