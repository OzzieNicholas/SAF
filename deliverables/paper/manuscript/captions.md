# SAF 主图图注定稿

全图统一语义：蓝色表示可达，红色表示不可达或被挡，紫色表示漏报不可达（FN），橙色表示潜在支撑接触区代理或误报（FP），灰色表示零件；橙色不在同一面板中复用两种含义。除非图注明确给出统计母集，定性案例只用于展示几何关系，不代表总体分布。

## 图 1  SAF 的标签、训练与推理闭环

**中文图注：** SAF 的离线几何标签、形状条件训练与未见零件推理流程。输入网格经归一化、占据化和潜在支撑接触区代理提取后，由距离场筛选与连续胶囊—网格距离细化生成监督标签；点级网络输出不可达概率，方向级网络一次输出 64 个固定方向的被挡概率。示例来自 Fusion 留出件，仅说明数据流和输出语义，不表示总体性能。

**English caption:** SAF workflow for offline geometric labeling, shape-conditioned training, and inference on unseen parts. Distance-field screening and continuous capsule--mesh refinement produce supervision on the potential support-contact proxy; the point model predicts inaccessibility, whereas the directional model outputs blocking probabilities for 64 fixed directions. Fusion examples illustrate the data flow rather than population-level performance.

## 图 2  构建方向改变支撑接触区

**中文图注：** 同一 Fusion CAD 零件在构建方向 $+Z$ 与 $+Y$ 下的潜在支撑接触区代理。橙色区域由 $45^\circ$ 悬垂阈值提取；代理随构建方向改变，因而 SAF 必须与给定方向下的代理共同解释。该图不进行构建方向优化，也不表示物理支撑形貌。

**English caption:** Potential support-contact proxy triangles on the same Fusion CAD part for the $+Z$ and $+Y$ build directions. Orange regions are extracted with the $45^\circ$ overhang threshold. The figure demonstrates orientation dependence of the queried proxy region; it neither optimizes orientation nor reconstructs physical supports.

## 图 3  有限球工具的离散直线逼近语义

**中文图注：** 多方向直线逼近判据的三类几何情形。开阔下朝面存在无碰撞方向；盲腔的候选方向均被零件本体遮挡；窄缝中零半径射线可见，但有限半径球工具不能通过。蓝色为可达方向，红色为碰撞或被挡方向。判据不包含基板、刀柄、夹具、弯曲路径或材料行为。

**English caption:** Three geometric cases for the discrete straight-approach criterion. An open downward-facing surface admits a collision-free direction; all sampled directions are blocked in a blind cavity; and a zero-radius ray passes through a narrow gap that rejects the finite spherical tool. Build plate, holder, fixtures, curved paths, and material behavior are excluded.

## 图 4  两级几何判定与边界细化

**中文图注：** 距离场筛选与边界带连续细化。最长轴为 48 个体素的占据栅格先生成自由空间距离场；方向最小净空位于 $r\pm\varepsilon$ 之外时直接判定，边界带内才调用连续胶囊—三角网格距离细化，最后按“任一方向可达”归约为点级标签。最长轴分辨率 48 与 96 的总体一致率为 97.28%，该值衡量稳定性而非证明绝对真值。

**English caption:** Two-stage distance-field screening and continuous boundary refinement. Directions outside the $r\pm\varepsilon$ clearance band are classified on an occupancy grid with 48 voxels along its longest axis, while ambiguous directions invoke continuous capsule--triangle intersection before existential point-level reduction. Agreement between longest-axis resolutions 48 and 96 is 97.28%, a stability measure rather than proof of ground truth.

## 图 5  形状条件点查询网络

**中文图注：** ConvONetLite 的张量与查询流程。$1\times n_x\times n_y\times n_z$ 占据栅格（$\max(n_x,n_y,n_z)=48$）经三层 $3\times3\times3$ 卷积编码为同分辨率的 32 通道特征体；查询位置的三线性特征与归一化坐标拼接后由两层 64 单元 MLP 解码。三层卷积的理论感受野为 $7^3$ 个体素；点级和方向级模型结构同构但权重独立，分别输出 1 个不可达 logit 和 64 个被挡 logit。

**English caption:** Tensor and query flow of ConvONetLite. Three $3\times3\times3$ convolutions encode a $1\times n_x\times n_y\times n_z$ occupancy grid, whose longest axis has 48 voxels, into a same-resolution 32-channel feature volume. Trilinearly sampled features and normalized coordinates are decoded by a two-layer, 64-unit MLP. Independently trained point and directional models output one inaccessibility logit and 64 blocking logits, respectively.

## 图 6  接触量与工具可达性是不同维度

**中文图注：** Fusion 数据中的匹配实例与全量统计。左侧两件零件均保留 84 个接触面，但不可达比例显著不同；蓝/红分别表示几何判定器给出的可达/不可达接触面。右侧分别以接触面计数代理和真实三角面积为横轴，在 8,590 件有效物化件上得到 Spearman $\rho=0.264$ 和 0.124。相关性为弱相关，不支持“严格独立”或“接触量无用”的结论。

**English caption:** Matched Fusion examples and full-corpus statistics. Both parts contain 84 retained contact faces but have markedly different inaccessible fractions; blue and red denote accessible and inaccessible faces. Across 8,590 materialized parts, Spearman correlations are 0.264 for the face-count proxy and 0.124 for true triangle area. These are weak associations, not evidence of strict independence.

## 图 7  未见零件上的点级预测

**中文图注：** Fusion 留出件与 Thingi10K 固定跨域测试件上的点级结果。每行依次给出全局定位，以及围绕同一证据焦点、相机朝向匹配的几何标签、连续不可达概率和显式误差面；紫色为漏报不可达（FN），橙色为误报（FP）。Thingi10K 最右 ROI 在邻近原始三角面会遮挡映射误差面时，以半透明 CAD 上下文显示同一映射 face ID 集合，不改变 face mapping 或误差计数。案例用于检查面映射和错误形态，不参与总体统计推断；总体性能见表 5 和表 6。

**English caption:** Point-level predictions on a held-out Fusion part and a fixed cross-domain Thingi10K part. Each row pairs global context with geometric labels, continuous inaccessibility probabilities, and explicit errors around the same evidence focus with matched camera orientation. Purple and orange denote false negatives and false positives. In the rightmost Thingi10K ROI, translucent CAD context keeps the same mapped face-ID set visible when neighboring raw triangles would otherwise occlude it; it changes neither face mapping nor error count. Cases audit face mapping and error morphology; aggregate performance is reported in Tables 5 and 6.

## 图 8  点级基线与形状上下文消融

**中文图注：** 同一 80 件 Fusion 留出集上的六方法比较（左）与 400 件受控子集上的网络消融（右）。左图圆点及区间表示逐件 F1 与其均值 95% bootstrap 区间，空心菱形表示 6,033 个点连接后的点池 F1；shape-conditioned surrogate 相对零半径射线的逐件配对差为 0.459，95% CI 为 $[0.372,0.545]$。完整 128 全局 / 64 下半球方向的 refined oracle 仅提供标签；粗有限工具 proxy 使用 16 全局 / 8 下半球方向。右图为 seed 0、60 轮训练的相对趋势，不与五次重复模型级留出主结果作绝对值比较。

**English caption:** Six-method comparison on the same 80 held-out Fusion parts (left) and shape-context ablation on a controlled 400-part subset (right). Per-part F1 values, mean bootstrap intervals, and point-pooled F1 are shown separately. The shape-conditioned surrogate minus zero-radius-ray paired difference is 0.459 with a 95% CI of $[0.372,0.545]$. The full 128-global/64-lower-direction refined oracle supplies labels only; the coarse finite-tool proxy uses 16 global/8 lower-hemisphere directions. The single-seed, 60-epoch ablation supports only within-setting comparisons.

## 图 9  方向级场与 Top-1 推荐

**中文图注：** 同一 Fusion 留出代理查询点上的几何方向标签、网络被挡概率与 Top-1 离散逼近方向。方向盘圆心对应竖直向下，圆周对应水平逼近；蓝色为可达，红色为被挡。箭头指向网络最低被挡概率且经几何判定可达的 64 个预设方向之一；该箭头不是连续姿态轨迹或完整刀路。

**English caption:** Geometric direction labels, predicted blocking probabilities, and the Top-1 discrete approach on one held-out Fusion proxy query point. The disk center represents vertically downward motion and the rim represents horizontal motion. The arrow marks the lowest predicted blocking probability that is geometrically accessible. The recommendation is discrete and is not a continuous pose trajectory or toolpath.

## 图 10  错误集中于临界可达区域

**中文图注：** 五个训练种子在 Fusion 400 件子集上的失败分析及固定留出案例。按每点可达方向数分箱后，全被挡、1--2、3--5 和至少 6 个可达方向的误判率分别为 $2.7\%\pm0.7\%$、$14.2\%\pm3.2\%$、$14.3\%\pm3.7\%$ 和 $4.1\%\pm0.6\%$；右侧展示固定 test 案例的全局、剖切与 18 个误差面。紫色为 FN，橙色为 FP；案例是代表性高误差样本，不称为绝对最坏件。

**English caption:** Five-seed failure analysis on the 400-part Fusion subset and a fixed held-out case. Error rates for 0, 1--2, 3--5, and at least 6 viable directions are $2.7\%\pm0.7\%$, $14.2\%\pm3.2\%$, $14.3\%\pm3.7\%$, and $4.1\%\pm0.6\%$. The fixed test case shows global, sectioned, and local views of 18 errors. Purple and orange denote false negatives and false positives; the case is representative, not an asserted global worst case.
