# evidence — 论文证据

只放论文用到的小型、脱敏证据：

- `manifest.json`：机器可读的冻结清单，记录每个实验结果文件的相对路径、SHA-256 和运行标识，由 `python -m paper.pipeline.audits.freeze_evidence` 从 `artifacts/runs/` 生成。
- `证据清单.md`：每个实验支撑论文的哪些内容、统计单位和限制的文字说明。

记录一律使用逻辑数据标识和哈希，不含本机绝对路径（论文门会检查）。原始运行记录、检查点、NPZ、日志和候选图属于 `artifacts/` 或数据根，不入库。
