"""support_accessibility — 金属增材制造支撑接触区的几何可达性代理评价与神经预测。

= Support Accessibility Field (SAF)。包内模块：
  oracle/  几何 oracle：语义C 判定器（体素腐蚀 + 方向 ray-march），冻结口径见 charter/decisions.md
  data/    程序化已知答案件生成 + 公开数据（Fusion360/Thingi10K）接入
  eval/    指标：点/区域/方向/效率 + 预算外推
  models/  形状条件神经网络（编码器 + 点查询解码器）
  viz/     热图 / 方向球面图 / 失败案例

治理与决策：见仓库根 charter/。"""
