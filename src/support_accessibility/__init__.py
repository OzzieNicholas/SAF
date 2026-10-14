"""support_accessibility — 金属增材制造支撑接触区的几何可达性代理评价与神经预测。

= Support Accessibility Field (SAF)。包内模块：
  oracle/     几何判定：体素距离场腐蚀、方向 ray-march、边界带精确胶囊细化、方向级可达性场
  data/       网格前端、下朝悬垂面提取、程序化已知答案件与公开数据（Fusion360、Thingi10K）接入
  models/     形状条件神经网络（编码器 + 点查询解码器）
  baselines/  对照基线：不经细化的体素判定（含零半径射线）、多数类、局部规则
  eval/       指标、预算外推与输入数据摘要
  runtime/    数据位置解析、运行记录、冻结参数与终端设置

治理与决策：见仓库根 governance/。"""
