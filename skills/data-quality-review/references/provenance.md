# 来源与改写范围

本包 rubric 版本：1.0.0（2026-11-06）。采用本包文件及 SHA-256 固定标准，不能用上游默认规则静默替代。

- https://github.com/apexin-ai/task-review ：参考 task-implementation.toml 的 16 个维度与 trial-analysis.toml 的 8 个维度。本包以中文重新编写说明，去掉领域限定，将 scientifically_grounded 替换为 task_relevance；保留证据不足、静态/动态区分及逐次归因原则。
- https://github.com/apexin-ai/train-tasks ，查阅 commit c99eba4：参考 ci/review/roles 的评分器和实例检查视角、T1 控制探针、ci/analysis 的证据引用校验设计及本地运行方式。本包不复制其实现代码或角色提示词。
- 不沿用 RL 专用假设：快速通过不自动无效；超时不将其他维度全部清空；不统一使用相对参考解 10% 阈值；训练/评测用途和合法基线由批次声明。

不捆绑上述仓库代码、模型凭据、内部平台配置或数据。可选依赖由使用者单独安装并固定版本；复制第三方实现时另行核对许可并保留归属。
