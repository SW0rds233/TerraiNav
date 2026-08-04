"""
TerraiNav - 热力图与路径可视化（独立脚本）

优化记录：
- 移除与 path.py 重复的函数定义（detect_keypoints, ACO_TSP, upsample_matrix,
  add_direction_indicators），改为从 path.py 导入
- 颜色映射使用 path.py 中的 create_threat_colormap
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.interpolate import RectBivariateSpline

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'Microsoft YaHei'
import warnings
warnings.filterwarnings("ignore")

# 【优化】从 path 模块导入共享函数和类，消除代码重复
from path import (
    detect_keypoints,
    upsample_matrix,
    add_direction_indicators,
    create_threat_colormap,
    PathPlanner,
)

# ACO_TSP 使用 PathPlanner 内部定义（与原来完全一致）
ACO_TSP = PathPlanner.ACO_TSP


if __name__ == "__main__":
    # 输入矩阵
    grid = np.array([
        [60.28, 25.48, 65.4, 44.41, 52.74, 65.66, 74.52, 57.76],
        [57.19, 64.25, 79.51, 57.19, 65.95, 69.04, 66.81, 66.55],
        [63.67, 56.03, 78.72, 63.28, 68.12, 62.48, 82.9, 62.58],
        [67.54, 60.22, 42.79, 68.12, 57.55, 79.21, 74.87, 48.72],
        [78.72, 73.14, 83.93, 59.45, 89.01, 74.09, 56.45, 65.4],
        [78.71, 58.88, 73.14, 57.76, 88.36, 48.14, 63.59, 76.99]
    ])

    print("输入二维表格：")
    print(f"矩阵形状：{grid.shape}")
    print(f"矩阵数值范围：{grid.min()} ~ {grid.max()}")

    # 关键点检测（改为十字选点）
    target_points = detect_keypoints(grid)
    start = [(0, 0)]
    all_points = start + target_points

    print(f"\n[OK] 检测到目标点: {len(target_points)} 个")
    for idx, p in enumerate(target_points[:10]):
        print(f"目标点 {idx + 1}：{p}")
    if len(target_points) > 10:
        print(f"... 和 {len(target_points) - 10} 个其他目标点")

    if len(target_points) > 0:
        print(f"最后一个目标点 {len(target_points)}：{target_points[-1]}")

    # 运行ACO求解最短路径
    aco = ACO_TSP(all_points, ant_num=50, max_iter=250)
    best_path, best_len = aco.run()

    # 提取路径坐标
    path_coords = []
    for idx in best_path:
        coord = all_points[idx]
        path_coords.append(coord)

    # 优化控制台输出：每行一个点
    print("\n[OK] 最优路径（完整航迹）:")
    for i, coord in enumerate(path_coords):
        print(f"{i}: {coord}")

    print(f"\n最短路径长度：{best_len:.2f}")
    print(f"路径经过点数：{len(path_coords)}")

    # 提高分辨率
    upscale_factor = 8
    grid_upscaled, factor = upsample_matrix(grid, factor=upscale_factor, method='cubic')

    original_rows, original_cols = grid.shape
    upsampled_rows, upsampled_cols = grid_upscaled.shape

    print(f"\n原始矩阵大小：{original_rows} x {original_cols}")
    print(f"上采样后矩阵大小：{upsampled_rows} x {upsampled_cols}")
    print(f"上采样因子：{factor}")

    # 【优化】使用 path.py 的公共颜色映射函数，消除重复代码
    mat_min = grid.min()
    mat_max = grid.max()
    cmap = create_threat_colormap(mat_min, mat_max)
    vmin, vmax = mat_min, mat_max

    # ========== 新增：绘制并保存100×100像素纯热力图 ==========
    # 1. 创建100×100像素的画布（figsize=1×1英寸 + dpi=100 → 100×100像素）
    fig_pure, ax_pure = plt.subplots(figsize=(1, 1), dpi=100)
    # 2. 绘制纯热力图（无任何额外元素）
    x_pure = np.linspace(0, original_cols, upsampled_cols)
    y_pure = np.linspace(0, original_rows, upsampled_rows)
    im_pure = ax_pure.pcolormesh(x_pure, y_pure, grid_upscaled,
                                 cmap=cmap,
                                 vmin=vmin, vmax=vmax,
                                 shading='gouraud',
                                 edgecolors='face',
                                 linewidth=0,
                                 antialiased=True)
    # 3. 隐藏所有坐标轴、边框、刻度
    ax_pure.axis('off')  # 关闭坐标轴
    ax_pure.set_xlim(0, original_cols)
    ax_pure.set_ylim(0, original_rows)
    # 4. 移除所有边距
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    # 5. 保存到指定桌面路径（100×100像素，无多余元素）
    save_path = r'C:\Users\13566\Desktop\pure_heatmap_100x100.png'
    fig_pure.savefig(save_path,
                     dpi=100,  # 确保100dpi，配合1×1英寸画布=100×100像素
                     bbox_inches='tight',
                     pad_inches=0,  # 无边距
                     facecolor='none',
                     edgecolor='none')
    plt.close(fig_pure)  # 关闭画布释放资源
    print(f"\n[OK] 纯热力图已保存至: {save_path}")
    # ========== 原有热力图+路径可视化（保留） ==========
    fig, ax = plt.subplots(figsize=(16, 12))

    x = np.linspace(0, original_cols, upsampled_cols)
    y = np.linspace(0, original_rows, upsampled_rows)

    im = ax.pcolormesh(x, y, grid_upscaled,
                       cmap=cmap,
                       vmin=vmin, vmax=vmax,  # 使用矩阵极值而非固定1-10
                       shading='gouraud',
                       edgecolors='face',
                       linewidth=0,
                       antialiased=True)

    # -------------------------- 核心修改3：颜色条刻度适配矩阵极值 --------------------------
    cbar = plt.colorbar(im, shrink=0.8, label='矩阵数值', location='right', pad=0.02)
    cbar.ax.tick_params(labelsize=10)
    # 生成合理的颜色条刻度（按矩阵范围均分，保留1位小数）
    tick_step = (mat_max - mat_min) / 10  # 分10段显示
    cbar_ticks = np.arange(mat_min, mat_max + tick_step, tick_step)
    cbar.set_ticks(np.round(cbar_ticks, 1))  # 四舍五入到1位小数

    # 绘制最优路径
    path_coords_np = np.array(path_coords)

    # 绘制航迹线
    ax.plot(path_coords_np[:, 1] + 0.5, path_coords_np[:, 0] + 0.5, '-',
            color='black', linewidth=1.0,
            alpha=0.8, label=f'最优路径 (长度: {best_len:.2f})',
            zorder=10)

    ''' 
    在航迹上添加方向指示箭头
    # 参数说明：
    # - interval: 箭头间隔，可调整（默认为5）
    # - arrow_length: 箭头长度，可调整（默认为0.4）
    # - arrow_width: 箭头宽度，可调整（默认为0.2）
    '''
    add_direction_indicators(ax, path_coords_np, interval=1, arrow_length=0.4, arrow_width=0.2)

    # 标记起点
    ax.plot(0.5, 0.5, 'o',
            color='red', markersize=12,
            markeredgecolor='black', markeredgewidth=1.5,
            label='起点(0,0)', zorder=12)

    '''
    标记关键点
    '''
    target_coords_np = np.array(target_points)
    if len(target_coords_np) > 0:
        ax.scatter(target_coords_np[:, 1] + 0.5, target_coords_np[:, 0] + 0.5,
                   color='blue', s=40, marker='s',
                   edgecolor='black', linewidth=0.6,
                   label=f'目标关键点 ({len(target_points)}个)', zorder=11)

    print(f"\n[OK] 在图中绘制了 {len(target_points)} 个目标关键点")

    # 添加网格线
    grid_spacing = 1
    x_grid_lines = np.arange(0, original_cols + grid_spacing, grid_spacing)
    y_grid_lines = np.arange(0, original_rows + grid_spacing, grid_spacing)

    for x_line in x_grid_lines:
        ax.axvline(x=x_line, color='lightgray', linestyle='-', linewidth=0.3, alpha=0.4)
    for y_line in y_grid_lines:
        ax.axhline(y=y_line, color='lightgray', linestyle='-', linewidth=0.3, alpha=0.4)

    # 设置图表属性
    ax.set_xlabel('列坐标', fontsize=12)
    ax.set_ylabel('行坐标', fontsize=12)
    ax.set_title(f'矩阵热力图与TSP最优路径\n检测到 {len(target_points)} 个目标关键点，路径长度: {best_len:.2f}',
                 fontsize=16, fontweight='bold', pad=20)

    ax.set_xlim(-0.5, original_cols + 0.5)
    ax.set_ylim(-0.5, original_rows + 0.5)

    tick_interval = 5
    ax.set_xticks(np.arange(0, original_cols + 1, tick_interval))
    ax.set_yticks(np.arange(0, original_rows + 1, tick_interval))
    ax.tick_params(axis='both', which='major', labelsize=10)

    legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                       ncol=3, fontsize=11, frameon=True,
                       fancybox=True, shadow=True, framealpha=0.9)

    plt.subplots_adjust(bottom=0.12, right=0.85, top=0.95)
    plt.show()

    # 收敛曲线可视化
    plt.figure(figsize=(10, 5))
    plt.plot(aco.history, 'b-', linewidth=2, alpha=0.8)
    plt.fill_between(range(len(aco.history)),
                     np.min(aco.history), aco.history,
                     alpha=0.3, color='blue')
    plt.title('蚁群算法收敛曲线', fontsize=14, fontweight='bold')
    plt.xlabel('迭代次数', fontsize=12)
    plt.ylabel('最短路径长度', fontsize=12)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.show()