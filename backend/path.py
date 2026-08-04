"""
TerraiNav - 路径规划与可视化

优化记录：
- 提取 create_threat_colormap() 消除 5 处重复的热力图颜色映射生成代码
- ACO 增加收敛检测，连续 N 轮无改进则提前终止
- build_path 增加除零保护
- add_direction_indicators 参数 original_rows 默认值从 1 改为 None，自动适配
- print() 替换为 logging
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from itertools import product
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.interpolate import RectBivariateSpline
import logging

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.family"] = "Microsoft YaHei"
import warnings

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


# ============================================================================
# 【优化】公共工具函数：热力图颜色映射生成（消除 5+ 处重复代码）
# ============================================================================
def create_threat_colormap(mat_min: float, mat_max: float, n_colors: int = 256):
    """
    根据矩阵数值范围生成绿→黄→红渐变色映射。

    Args:
        mat_min: 矩阵最小值
        mat_max: 矩阵最大值
        n_colors: 颜色数量，默认 256

    Returns:
        matplotlib.colors.LinearSegmentedColormap
    """
    mid_value = (mat_min + mat_max) / 2.0
    colors_custom = []
    for i in range(n_colors):
        value = mat_min + (i / (n_colors - 1)) * (mat_max - mat_min)
        if value <= mid_value:
            ratio = (value - mat_min) / (mid_value - mat_min) if mid_value > mat_min else 0.5
            r = int(ratio * 255)
            g = 255
            b = 0
        else:
            ratio = (value - mid_value) / (mat_max - mid_value) if mat_max > mid_value else 0.5
            r = 255
            g = int(255 * (1 - ratio))
            b = 0
        colors_custom.append(f"#{r:02x}{g:02x}{b:02x}")

    return mcolors.LinearSegmentedColormap.from_list("threat_cmap", colors_custom, N=n_colors)


def detect_keypoints(matrix, quantile=0.65, cluster_threshold=1.4, max_points_per_cluster=3):
    """
    热力筛选 + 空间聚类 + 多点生成 + 高评分强制包含，平衡覆盖度和路径平滑度
    :param quantile: 热力值分位数，降低可增加候选点
    :param cluster_threshold: 聚类合并距离，控制聚类数量
    :param max_points_per_cluster: 单个聚类最多生成的关键点数量

    逻辑说明：
    1. 基于分位数筛选高值点并进行空间聚类
    2. 对每个聚类生成多个关键点
    3. 额外强制包含所有评分≥70的区块，确保高威胁区域都被覆盖
    """
    # 1. 热力值筛选高值点 + 高评分点（合并为单次扫描，避免重复遍历）
    danger_threshold = np.quantile(matrix, quantile)
    rows, cols = matrix.shape
    high_value_points = []
    high_score_points = []
    high_score_threshold = 70.0
    for i in range(rows):
        for j in range(cols):
            val = matrix[i, j]
            if val >= danger_threshold:
                high_value_points.append((i, j))
            if val >= high_score_threshold:
                high_score_points.append((i, j))

    if not high_value_points:
        return []

    # 2. 空间聚类
    points_np = np.array(high_value_points)
    Z = linkage(points_np, method='single', metric='euclidean')
    labels = fcluster(Z, t=cluster_threshold, criterion='distance')

    # 3. 对每个聚类生成多个关键点（避免只取中心点导致覆盖不足）
    unique_labels = np.unique(labels)
    keypoints = []
    for label in unique_labels:
        cluster_points = points_np[labels == label]
        cluster_size = len(cluster_points)

        # 根据聚类大小决定生成的关键点数量
        if cluster_size <= 3:
            # 小聚类：只取1个点（聚类中心）
            center_i = np.mean(cluster_points[:, 0]).round().astype(int)
            center_j = np.mean(cluster_points[:, 1]).round().astype(int)
            keypoints.append((center_i, center_j))
        else:
            # 大聚类：按热力值高低取多个点
            # 计算每个点的热力值
            cluster_values = np.array([matrix[p[0], p[1]] for p in cluster_points])
            # 按热力值降序排序
            sorted_idx = np.argsort(-cluster_values)
            # 取前N个点，N不超过max_points_per_cluster
            take_n = min(max_points_per_cluster, cluster_size)
            selected_points = cluster_points[sorted_idx[:take_n]]
            for p in selected_points:
                keypoints.append((p[0], p[1]))

    logger.info(f"自动计算阈值: >= {danger_threshold:.2f}")
    logger.info(f"   筛选到高值点: {len(high_value_points)} 个 -> 聚类后关键点: {len(keypoints)} 个")

    # 4. 将高评分区块（已在步骤1合并扫描）添加到关键点列表中（避免重复）
    existing_keypoints = set(keypoints)
    for point in high_score_points:
        if point not in existing_keypoints:
            keypoints.append(point)
            existing_keypoints.add(point)

    if high_score_points:
        logger.info(f"   额外添加评分>=70的区块: {len(high_score_points)} 个 -> 最终关键点: {len(keypoints)} 个")

    return keypoints


def upsample_matrix(matrix, factor=4, method="cubic"):
    """增加矩阵分辨率，使小方格更小"""
    rows, cols = matrix.shape
    
    # 根据矩阵大小选择合适的插值阶数
    if rows <= 3 or cols <= 3:
        # 矩阵太小时使用线性插值
        kx = ky = 1
    elif rows <= 5 or cols <= 5:
        # 矩阵较小时降低插值阶数
        kx = ky = 2
    else:
        kx = ky = 3 if method == "cubic" else 1

    x = np.arange(cols)
    y = np.arange(rows)

    try:
        f = RectBivariateSpline(y, x, matrix, kx=kx, ky=ky)
        x_new = np.linspace(0, cols - 1, cols * factor)
        y_new = np.linspace(0, rows - 1, rows * factor)
        matrix_upscaled = f(y_new, x_new)
    except Exception:
        # 插值失败时使用简单的最近邻上采样
        matrix_upscaled = np.repeat(np.repeat(matrix, factor, axis=0), factor, axis=1)

    return matrix_upscaled, factor


def add_direction_indicators(
    ax, path_coords, interval=5, arrow_length=0.4, arrow_width=0.2, original_rows=None
):
    """
    在航迹上添加方向指示箭头

    参数:
    - ax: matplotlib的坐标轴对象
    - path_coords: 航迹坐标数组，形状为(n, 2)，每行是(row, col)坐标
    - interval: 箭头间隔（多少个点添加一个箭头）
    - arrow_length: 箭头长度
    - arrow_width: 箭头宽度
    - original_rows: 原始矩阵行数（用于正确的坐标反转）
    """

    # 计算线段长度，用于确定箭头是否足够长
    def segment_length(i):
        if i + 1 < len(path_coords):
            dx = path_coords[i + 1][1] - path_coords[i][1]
            dy = path_coords[i + 1][0] - path_coords[i][0]
            return (dx**2 + dy**2) ** 0.5
        return 0

    for i in range(0, len(path_coords) - 1, interval):
        if i + 1 < len(path_coords):
            start = path_coords[i]
            end = path_coords[i + 1]

            # 计算线段中点（col是x，row是y）
            # 注意：这里的坐标与 ax.plot 保持一致
            # plot 使用: (col + 0.5, row + 0.5) 然后 y 轴反转
            # 所以 arrow 也需要反转 y 坐标
            mid_x = (start[1] + end[1]) / 2 + 0.5
            mid_y = (original_rows or 1) - ((start[0] + end[0]) / 2 + 0.5)  # 【优化】None 安全

            # 计算方向向量（col是x，row是y）
            # 在图片坐标系中，row 增大意味着向下移动
            # 在反转后的 matplotlib 坐标系中，row 增大意味着向上移动（数值变小）
            dx = end[1] - start[1]
            dy = -(end[0] - start[0])  # 保持 dy 方向一致（因为 ax.plot 也做了反转）

            # 箭头长度标准化（不超过线段长度的80%）
            seg_len = segment_length(i)
            arrow_scale = min(0.3, seg_len * 0.4)
            if arrow_scale < 0.05:  # 线段太短，跳过箭头
                continue

            ax.arrow(
                mid_x,
                mid_y,
                dx * arrow_scale,
                dy * arrow_scale,
                head_width=arrow_width,
                head_length=arrow_length * arrow_scale / 0.3,
                fc="black",
                ec="black",
                alpha=0.8,
                zorder=12,
            )


class PathPlanner:
    """路径规划器：关键点检测 + ACO求解TSP + 可视化"""

    @staticmethod
    def detect_keypoints(matrix):
        """检测关键点（调用全局函数，兼容边缘和角落）"""
        return detect_keypoints(matrix)

    class ACO_TSP:
        """蚁群算法求解TSP

        优化记录：
        - 增加收敛检测：连续 patience 轮无改进则提前终止
        - build_path 增加除零保护
        """

        def __init__(
            self, points, ant_num=50, max_iter=200, alpha=1, beta=5, rho=0.1, Q=100,
            patience: int = 30
        ):
            self.points = np.array(points)
            self.point_num = len(points)
            self.ant_num = ant_num
            self.max_iter = max_iter
            self.alpha = alpha
            self.beta = beta
            self.rho = rho
            self.Q = Q
            self.patience = patience  # 【优化】收敛容忍轮数
            self.dist_matrix = np.linalg.norm(
                self.points[:, None] - self.points[None, :], axis=2
            )
            self.dist_matrix[self.dist_matrix == 0] = 1e-8
            self.pheromone = np.ones_like(self.dist_matrix)
            self.best_len = np.inf
            self.best_path = []
            self.history = []

        def run(self):
            stagnate_count = 0  # 【优化】收敛检测计数器
            for iteration in range(self.max_iter):
                all_paths = []
                all_lens = []
                prev_best = self.best_len
                for _ in range(self.ant_num):
                    path, path_len = self.build_path()
                    all_paths.append(path)
                    all_lens.append(path_len)
                    if path_len < self.best_len:
                        self.best_len = path_len
                        self.best_path = path.copy()
                self.update_pheromone(all_paths, all_lens)
                self.history.append(self.best_len)

                # 【优化】收敛检测
                if abs(self.best_len - prev_best) < 1e-6:
                    stagnate_count += 1
                else:
                    stagnate_count = 0

                if stagnate_count >= self.patience:
                    logger.info(f"ACO 收敛于第 {iteration + 1} 轮，提前终止")
                    break

            return self.best_path, self.best_len

        def build_path(self):
            path = [0]
            visited_mask = np.zeros(self.point_num, dtype=bool)
            visited_mask[0] = True
            while len(path) < self.point_num:
                cur = path[-1]
                prob = (self.pheromone[cur] ** self.alpha) * (
                    (1.0 / self.dist_matrix[cur]) ** self.beta
                )
                prob[visited_mask] = 0
                prob_sum = prob.sum()
                if prob_sum < 1e-12:
                    remaining = np.where(~visited_mask)[0]
                    next_p = np.random.choice(remaining)
                else:
                    prob /= prob_sum
                    next_p = np.random.choice(self.point_num, p=prob)
                path.append(next_p)
                visited_mask[next_p] = True
            path.append(0)
            path_len = sum(
                self.dist_matrix[path[k], path[k + 1]] for k in range(len(path) - 1)
            )
            return path, path_len

        def update_pheromone(self, all_paths, all_lens):
            self.pheromone *= 1 - self.rho
            for path, path_len in zip(all_paths, all_lens):
                rows = path[:-1]
                cols = path[1:]
                np.add.at(self.pheromone, (rows, cols), self.Q / path_len)

    def plan_path(self, threat_matrix):
        """
        路径规划主逻辑
        :param threat_matrix: 威胁分数矩阵
        :return: None（生成可视化图）
        """
        # 1. 检测关键点
        keypoints = self.detect_keypoints(threat_matrix)
        logger.info(f"[关键点检测] 检测到 {len(keypoints)} 个关键点")
        for idx, p in enumerate(keypoints):
            logger.info(f"关键点 {idx + 1}: {p} | 威胁分数: {threat_matrix[p]:.1f}")

        # 2. ACO求解最短路径
        if not keypoints:
            logger.warning("未检测到关键点，跳过路径规划")
            self.plot_heatmap(threat_matrix)
            return

        # 加入起点(0,0)
        all_points = [(0, 0)] + keypoints
        aco = self.ACO_TSP(all_points, ant_num=50, max_iter=250)
        best_path, best_len = aco.run()

        # 输出最优路径
        logger.info("最优路径:")
        path_coords = []
        for idx in best_path:
            coord = all_points[idx]
            path_coords.append(coord)
        path_str = " -> ".join(str(c) for c in path_coords)
        logger.info(f"  {path_str}")
        logger.info(f"最短路径长度: {best_len:.2f}")

        # 3. 可视化热力图+路径
        self.plot_heatmap_with_path(threat_matrix, path_coords)

    def plot_heatmap(self, matrix):
        """仅绘制热力图"""
        # 颜色映射
        colors = [
            "#006400",
            "#007000",
            "#008000",
            "#009000",
            "#00A000",
            "#00B000",
            "#00C000",
            "#20D020",
            "#40E040",
            "#60F060",
            "#7CFC00",
            "#ADFF2F",
            "#FFFF00",
            "#FFD700",
            "#FFA500",
            "#FF8C00",
            "#FF4500",
            "#FF0000",
        ]
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "threat_heatmap", colors, N=512
        )

        # 绘制热力图
        fig, ax = plt.subplots(figsize=(15, 12))
        im = ax.imshow(matrix, cmap=cmap, aspect="auto")

        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("威胁分数", fontsize=12)

        # 设置标题和标签
        ax.set_title("地形威胁分数热力图", fontsize=16, fontweight="bold")
        ax.set_xlabel("X坐标", fontsize=12)
        ax.set_ylabel("Y坐标", fontsize=12)

        plt.tight_layout()
        plt.show()

    def plot_heatmap_with_path(self, matrix, path_coords):
        """绘制热力图+最优路径"""
        # 颜色映射
        colors = [
            "#006400",
            "#007000",
            "#008000",
            "#009000",
            "#00A000",
            "#00B000",
            "#00C000",
            "#20D020",
            "#40E040",
            "#60F060",
            "#7CFC00",
            "#ADFF2F",
            "#FFFF00",
            "#FFD700",
            "#FFA500",
            "#FF8C00",
            "#FF4500",
            "#FF0000",
        ]
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "threat_heatmap", colors, N=512
        )

        # 绘制热力图
        fig, ax = plt.subplots(figsize=(15, 12))
        im = ax.imshow(matrix, cmap=cmap, aspect="auto")

        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("威胁分数", fontsize=12)

        # 绘制最优路径
        path_x = [p[1] for p in path_coords]  # X是列
        path_y = [p[0] for p in path_coords]  # Y是行
        ax.plot(
            path_x,
            path_y,
            "b-",
            linewidth=2,
            marker="o",
            markersize=8,
            label="最优路径",
        )
        ax.legend(fontsize=12)

        # 设置标题和标签
        ax.set_title("地形威胁分数热力图 + 最优路径", fontsize=16, fontweight="bold")
        ax.set_xlabel("X坐标", fontsize=12)
        ax.set_ylabel("Y坐标", fontsize=12)

        plt.tight_layout()
        plt.show()

    def get_heatmap_figure(self, matrix, path_coords=None):
        """返回热力图（及路径）的 Figure 对象，用于嵌入 Tkinter"""
        # 上采样增加分辨率
        upscale_factor = 4
        grid_upscaled, factor = upsample_matrix(
            matrix, factor=upscale_factor, method="cubic"
        )

        original_rows, original_cols = matrix.shape
        upsampled_rows, upsampled_cols = grid_upscaled.shape

        mat_min = matrix.min()
        mat_max = matrix.max()

        # 【优化】使用提取的公共颜色映射函数
        cmap = create_threat_colormap(mat_min, mat_max)

        fig, ax = plt.subplots(figsize=(10, 8), dpi=100)

        x = np.linspace(0, original_cols, upsampled_cols)
        # 反转 y 坐标，使左上角为 (0,0)，y轴向下增加
        y = np.linspace(original_rows, 0, upsampled_rows)

        im = ax.pcolormesh(
            x,
            y,
            grid_upscaled,
            cmap=cmap,
            vmin=mat_min,
            vmax=mat_max,
            shading="gouraud",
            edgecolors="face",
            linewidth=0,
            antialiased=True,
        )

        # 颜色条
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("威胁分数", fontsize=10)
        # 生成合理的颜色条刻度
        tick_step = (mat_max - mat_min) / 10
        cbar_ticks = np.arange(mat_min, mat_max + tick_step, tick_step)
        cbar.set_ticks(np.round(cbar_ticks, 1))

        if path_coords:
            path_coords_np = np.array(path_coords)

            # 绘制航迹线
            # 注意：pcolormesh 的 y 坐标是 np.linspace(original_rows, 0, ...)，即顶部是 original_rows
            # 为了与图片坐标系一致（row=0 在顶部），需要反转 y 坐标
            path_y_reversed = original_rows - (path_coords_np[:, 0] + 0.5)
            ax.plot(
                path_coords_np[:, 1] + 0.5,
                path_y_reversed,
                "-",
                color="black",
                linewidth=1.5,
                alpha=0.9,
                label=f"最优路径",
                zorder=10,
            )

            # 添加方向指示箭头（传入 original_rows 用于正确的坐标反转）
            add_direction_indicators(
                ax,
                path_coords_np,
                interval=2,
                arrow_length=0.3,
                arrow_width=0.15,
                original_rows=original_rows,
            )

            # 标记起点（row=0, col=0，反转后 y = original_rows - 0.5）
            ax.plot(
                0.5,
                original_rows - 0.5,
                "o",
                color="red",
                markersize=10,
                markeredgecolor="black",
                markeredgewidth=1,
                label="起点(0,0)",
                zorder=12,
            )

            # 标记关键点
            if len(path_coords_np) > 1:
                keypoints = path_coords_np[1:]  # 排除起点
                keypoints_y_reversed = original_rows - (keypoints[:, 0] + 0.5)
                ax.scatter(
                    keypoints[:, 1] + 0.5,
                    keypoints_y_reversed,
                    color="blue",
                    s=30,
                    marker="s",
                    edgecolor="black",
                    linewidth=0.5,
                    label=f"目标点 ({len(keypoints)}个)",
                    zorder=11,
                )

            ax.legend(
                loc="upper center",
                bbox_to_anchor=(0.5, -0.08),
                ncol=3,
                fontsize=8,
                frameon=True,
            )

        # 网格线
        grid_spacing = 1
        x_grid_lines = np.arange(0, original_cols + grid_spacing, grid_spacing)
        y_grid_lines = np.arange(0, original_rows + grid_spacing, grid_spacing)

        for x_line in x_grid_lines:
            ax.axvline(
                x=x_line, color="lightgray", linestyle="-", linewidth=0.3, alpha=0.4
            )
        for y_line in y_grid_lines:
            ax.axhline(
                y=y_line, color="lightgray", linestyle="-", linewidth=0.3, alpha=0.4
            )

        ax.set_title("地形威胁热力图与巡逻路线", fontsize=12, fontweight="bold")
        ax.set_xlabel("X坐标", fontsize=10)
        ax.set_ylabel("Y坐标", fontsize=10)

        ax.set_xlim(-0.5, original_cols + 0.5)
        ax.set_ylim(original_rows + 0.5, -0.5)  # 反转y轴极限以匹配矩阵坐标系

        fig.tight_layout()
        return fig

    def get_pure_heatmap(self, matrix, output_size):
        """生成纯热力图，无坐标轴图例，尺寸与原图一致

        Args:
            matrix: 威胁度矩阵
            output_size: (width, height) 输出图片尺寸
        """
        width, height = output_size
        original_rows, original_cols = matrix.shape

        mat_min = matrix.min()
        mat_max = matrix.max()

        # 上采样增加分辨率
        upscale_factor = 8
        grid_upscaled, factor = upsample_matrix(matrix, factor=upscale_factor, method='cubic')
        upsampled_rows, upsampled_cols = grid_upscaled.shape

        # 【优化】使用提取的公共颜色映射函数
        cmap = create_threat_colormap(mat_min, mat_max)
        
        # 创建图片，使用实际的输出尺寸（去除白边）
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        fig.patch.set_facecolor('white')
        
        # 使用pcolormesh + gouraud shading（与heatmap.py相同）
        x = np.linspace(0, original_cols, upsampled_cols)
        y = np.linspace(0, original_rows, upsampled_rows)
        im = ax.pcolormesh(x, y, grid_upscaled,
                         cmap=cmap,
                         vmin=mat_min, vmax=mat_max,
                         shading='gouraud',
                         edgecolors='face',
                         linewidth=0,
                         antialiased=True)
        
        # 移除所有坐标元素
        ax.set_axis_off()
        ax.set_xticks([])
        ax.set_yticks([])
        # 设置正确的坐标范围（填满整个图片）
        ax.set_xlim(0, original_cols)
        ax.set_ylim(0, original_rows)
        # 关键：去除白边
        ax.set_position([0, 0, 1, 1])  # 填满整个figure
        plt.subplots_adjust(bottom=0, top=1, left=0, right=1)
        fig.tight_layout(pad=0)
        
        return fig

    def get_pure_pathmap(self, matrix, path_coords, output_size):
        """生成纯路径图，在热力图上叠加路径线（经过分块中心）
        
        Args:
            matrix: 威胁度矩阵
            path_coords: 路径坐标列表 [(row, col), ...] - 分块中心坐标
            output_size: (width, height) 输出图片尺寸
        """
        width, height = output_size
        original_rows, original_cols = matrix.shape
        
        # 先生成纯热力图（使用改进的插值）
        fig = self.get_pure_heatmap(matrix, output_size)
        ax = fig.axes[0]
        
        if path_coords and len(path_coords) > 0:
            path_coords_np = np.array(path_coords)
            
            # 绘制路径线 - 使用矩阵坐标（+0.5偏移到分块中心）
            # 与heatmap.py相同的方式
            ax.plot(path_coords_np[:, 1] + 0.5, path_coords_np[:, 0] + 0.5, '-',
                    color='black', linewidth=2.5,
                    alpha=0.9, zorder=10)
            
            # 添加方向箭头（更明显，每隔1个点一个箭头）
            for i in range(0, len(path_coords_np) - 1, 1):
                start = path_coords_np[i]
                end = path_coords_np[i + 1]
                
                # 计算线段中点
                mid_x = (start[1] + end[1]) / 2 + 0.5
                mid_y = (start[0] + end[0]) / 2 + 0.5
                
                # 计算方向向量
                dx = end[1] - start[1]
                dy = end[0] - start[0]
                
                # 箭头长度标准化
                seg_len = (dx**2 + dy**2) ** 0.5
                if seg_len > 0.1:  # 线段太短时跳过
                    arrow_scale = min(0.4, seg_len * 0.5)
                    
                    ax.annotate('', 
                              xy=(mid_x + dx * 0.3, mid_y + dy * 0.3),
                              xytext=(mid_x, mid_y),
                              arrowprops=dict(arrowstyle='->', 
                                          lw=2.5,  # 更粗的箭头
                                          color='blue',  # 橙红色更明显
                                          alpha=0.95),
                              zorder=15)
            
            # 标记起点（红色大圆点）
            if len(path_coords_np) > 0:
                start = path_coords_np[0]
                ax.plot(start[1] + 0.5, start[0] + 0.5, 'o',
                       color='red', markersize=15,
                       markeredgecolor='black', markeredgewidth=2,
                       zorder=20)
            
            # 标记目标点（蓝色方块）
            for pt in path_coords_np[1:]:
                ax.plot(pt[1] + 0.5, pt[0] + 0.5, 's',
                       color='blue', markersize=10,
                       markeredgecolor='black', markeredgewidth=1.5,
                       zorder=20)
        
        # 紧密裁边
        fig.tight_layout(pad=0)
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        return fig


if __name__ == "__main__":
    # 测试
    test_matrix = np.array([[10, 20, 30], [40, 50, 60], [70, 80, 90]])
    planner = PathPlanner()
    planner.plan_path(test_matrix)
