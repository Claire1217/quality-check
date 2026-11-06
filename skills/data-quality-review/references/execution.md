# 可移植运行配置

把配置和输出存放在用户项目的批次目录，不写入已安装 skill。所有路径相对配置文件解析；本技能中的相对链接相对 SKILL.md 解析。

建议批次结构：intake.json（来源/哈希/题目清单/抽样范围）、run-config.json（模型与协议）、findings.json、trial-records.jsonl、evidence-index.json、runs/、analysis/、summary/、report.md。

run-config 至少记录：

- source、output_dir、task_ids、模型的真实 ID 与 agent、reviewer。
- provider base URL、凭据环境变量名（不保存值）。
- executor 类型 local/ssh/existing-scheduler，机器资源和并发上限。
- 本包 rubric 版本与哈希；可选 task-review/train-tasks checkout 路径、commit 与适配 diff；Harbor/agent 版本。
- 题目时限、输出 token 上限、协议 ID、重试上限、抽样理由。

模型选择沿用用户已有配置。本流程使用 Claude Opus 5.5、DeepSeek、GLM；API ID 与 DeepSeek、GLM 的具体版本读取项目现有配置，缺失时询问，不猜测或静默替换。用户明确指定替换模型时记录协议变更。用两个待比较模型配置 --pair，第三个作为对照。模型/预算缺失先准备实验，不猜测后直接调用。

已有 CCM 或其他调度器时复用其持久化任务、心跳与回收机制；没有则按本地资源顺序执行。不要求安装 CCM。运行前检查原生 harness 的 --help、版本及一个最小环境控制；不要把历史命令当当前有效接口。

每题 Claude Opus 5.5、DeepSeek、GLM 各 4 个正式运行槽位，记为 repeat_index=1..4；每个槽位可有恢复 attempt，但只能选中一个 attempt 进入汇总。仅已定位的部署/API 故障可恢复一次，用户规定优先。先查旧进程是否仍活跃。恢复失败后记录 blocked/error，继续其他独立工作，不无限重试。用户暂停的批次保持暂停。

每个 attempt 保存原始配置、开始结束、score、exception、trajectory、提交和 verifier 输出。预期题目 × 模型清单也要记录，未执行组合不可因没有 trial 文件而消失。原始文件不可覆盖；规范化记录引用原文件及其哈希。

批次用途和逐项适用性按 [适用性配置](implementation-profiles.md) 在试跑前冻结。

## 先发现已有配置，再询问缺失项

用户只需给出题包位置和任务意图，不要求预先手写完整 run-config。由 agent 根据以下来源整理实际配置：

1. 当前项目的规则、README、运行说明、已有脚本与批次配置，优先复用相同协议。
2. 项目明确引用的 `.env` 或私有配置，以及相关模型环境变量的名称和是否已设置。读取必要字段时不得在工具输出、命令行、报告或聊天中回显密钥；不要运行无过滤的 env/printenv 或直接输出整个凭据文件。
3. 已有 agent 登录方式、harness 帮助信息、本机 Docker 或已授权远程执行资源；不假设必须使用某个供应商或网关，不扫描无关私人目录。

整理题包/输出位置、三个 solver 与 reviewer 的真实 ID、provider/API 地址与调用协议、凭据引用、执行方式、预算和范围。多个配置冲突时列出差异；只向用户集中询问无法确认的字段，不重复索要已有配置或授权。

凭据由现有运行工具从环境或私有配置读取，不要求用户在聊天粘贴密钥。已有登录能够满足所选 agent 时不额外要求 API key。查看实际 CLI 帮助并在已授权预算内作最小连通性验证；没有模型访问、执行方式或预算时先完成静态审查及准备，标明动态阶段缺口。连通性成功不等于质检完成，后续仍执行五阶段流程。
