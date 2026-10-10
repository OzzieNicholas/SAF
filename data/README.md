# data — 数据根

本目录是 SAF 默认的数据根，内容不入库（只有本说明入库）。需要换位置时，设置环境变量 `SAF_DATA_ROOT`，或在不入库的 `configs/paths.local.yaml` 里覆盖（字段同 `configs/paths.yaml`，可单独为某个数据集写绝对路径）。

## 目录约定

```text
data/
├─ raw/                                      公开原始网格（自行下载，只读）
│  ├─ fusion360_gallery/reconstruction/      Fusion 360 Gallery 重建数据集，用其中的 .obj 网格
│  └─ thingi10k/raw_meshes/                  Thingi10K 原始网格（.stl / .obj）
└─ processed/                                构建产物，每个数据集一个目录
   ├─ fusion360/                             主 CAD 数据集
   ├─ thingi10k/                             跨域测试集（恒为 test，不进训练）
   └─ procedural/                            程序化已知答案件
```

每个处理后数据集目录包含：`models/*.npz`（占据栅格、接触点、标签）、`manifest.csv`（每个零件一行的元数据）、`dataset.json`（构建参数与切分统计；标签审核结果由 `experiments/label_audit.py --write` 写入）。

## 准备步骤

1. 下载两个公开数据集，放到上面的 `raw/` 位置（来源以官方说明为准）：
   - Fusion 360 Gallery：<https://github.com/AutodeskAILab/Fusion360GalleryDataset>，取重建（reconstruction）数据集。
   - Thingi10K：<https://github.com/Thingi10K/Thingi10K>，取原始网格。
2. 在仓库根目录构建处理后数据集（构建耗时较长；真实数据可先用 `--max-models` 抽样试跑，程序化件用 `--n-models`）：

   ```bash
   python tools/build_procedural_dataset.py
   python tools/build_fusion360_dataset.py
   python tools/build_thingi10k_dataset.py
   ```

3. 对真实网格数据集做标签审核（命门，见 `governance/铁律约束.md`）：

   ```bash
   python experiments/label_audit.py --write
   ```

## 不入库的原因

处理后数据集是已压缩的二进制文件。每次重建都会在 git 历史里留下一份新副本，体积持续膨胀；而构建过程是确定性的（遍历顺序固定，`manifest.csv` 可用于校验），任何人下载同样的公开数据即可重建。
