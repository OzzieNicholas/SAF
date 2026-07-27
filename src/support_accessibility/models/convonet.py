"""ConvONet-lite：3D-CNN 全局编码器 + 点查询解码器（形状条件跨模型可达性预测；D-015 主线真模型）。

对比 tiny numpy（仅局部 patch、无全局上下文）：整块 occ 经 3D-CNN → 特征体 → 在查询点 trilinear 采样
局部特征 + 归一坐标 → MLP → 不可达 logit。深腔全局遮挡（docs §10 强调）由卷积感受野带入。
grid_sample 用归一坐标 [-1,1]，故不同尺寸 occ 无需 resize（逐模型前向）。需 torch（environment.yml，D-007）；
GPU 可用则用。坐标序坑（grid 末维 = W,H,D 序）由 to_grid_coords 统一处理，须经 sanity（采样 occ 自身≈占据值）验证。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


def to_grid_coords(points, occ_shape):
    """体素坐标 (N,3)=(px,py,pz) → grid_sample 归一坐标 (N,3)。

    occ tensor 记为 [1,1,nx,ny,nz]（conv 视 D=nx,H=ny,W=nz）；grid_sample 末维序 = (W,H,D) = (pz,py,px)。
    故先按 (px,py,pz) 归一到 [-1,1]，再重排为 (pz,py,px)。
    """
    p = torch.as_tensor(points, dtype=torch.float32)
    s = torch.as_tensor(occ_shape, dtype=torch.float32)              # (nx,ny,nz)
    norm = 2.0 * p / (s - 1.0).clamp(min=1.0) - 1.0                  # (N,3) 序 (px,py,pz)
    return norm[:, [2, 1, 0]].contiguous()                          # → (pz,py,px)=(W,H,D)


class ConvONetLite(nn.Module):
    """occ [1,1,nx,ny,nz] → 3D-CNN 特征体 → 查询点采样 + 坐标 → MLP → 不可达 logit [N]。"""

    def __init__(self, feat=32, hidden=64):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Conv3d(1, 16, 3, padding=1), nn.ReLU(inplace=True),
            nn.Conv3d(16, feat, 3, padding=1), nn.ReLU(inplace=True),
            nn.Conv3d(feat, feat, 3, padding=1), nn.ReLU(inplace=True),
        )
        self.dec = nn.Sequential(
            nn.Linear(feat + 3, hidden), nn.ReLU(inplace=True),
            nn.Linear(hidden, hidden), nn.ReLU(inplace=True),
            nn.Linear(hidden, 1),
        )

    def forward(self, occ, grid_coords):
        feat = self.enc(occ)                                        # [1,C,nx,ny,nz]
        grid = grid_coords.view(1, -1, 1, 1, 3)                     # [1,N,1,1,3]
        sampled = F.grid_sample(feat, grid, align_corners=True, padding_mode='border')  # [1,C,N,1,1]
        sampled = sampled.view(feat.shape[1], -1).t()              # [N,C]
        x = torch.cat([sampled, grid_coords], dim=1)               # [N,C+3]
        return self.dec(x).view(-1)                                # [N]
