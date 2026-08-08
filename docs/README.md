# 文档边界

`docs/` 不是 SAF 的第二套治理入口。

- 顶层五份编号文档是只读的研究参考：问题背景、研究定位、文献、实验设计和执行路线。它们解释领域内容，不直接裁决当前项目状态。
- `docs/references/` 是只读的文献输入区；其中的 PDF 和候选书目服务于研究与论文引用，不是论文交付物，也不参与运行状态裁决。
- `docs/other/project-control-plane/` 是可复用的通用控制平面规范；SAF 的具体路径、能力和检查器由 `governance/project.json` 适配。
- SAF 当前活动规则、决策、证据和结果只认 `governance/`；运行状态由 `tests/gate.py` 和结构化产物生成。

个人 GPT/LLM 备忘不属于 `docs/` 的项目资产，不纳入治理检查。
