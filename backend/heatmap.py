import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.interpolate import RectBivariateSpline

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'Microsoft YaHei'
import warnings

warnings.filterwarnings("ignore")


from scipy.cluster.hierarchy import fcluster, linkage

def detect_keypoints(matrix, quantile=0.65, cluster_threshold=1.4, max_points_per_cluster=3):
    """
    热力筛选 + 空间聚类 + 多点生成，平衡覆盖度和路径平滑度
    :param quantile: 热力值分位数，降低可增加候选点
    :param cluster_threshold: 聚类合并距离，控制聚类数量
    :param max_points_per_cluster: 单个聚类最多生成的关键点数量
    """
    # 1. 热力值筛选高值点
    danger_threshold = np.quantile(matrix, quantile)
    rows, cols = matrix.shape
    high_value_points = []
    for i in range(rows):
        for j in range(cols):
            if matrix[i, j] >= danger_threshold:
                high_value_points.append((i, j))

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

    print(f"✅ 自动计算阈值：≥ {danger_threshold:.2f}")
    print(f"   筛选到高值点：{len(high_value_points)} 个 → 聚类后关键点：{len(keypoints)} 个")
    return keypoints

class ACO_TSP:
    """蚁群算法求解TSP问题"""

    def __init__(self, points, ant_num=50, max_iter=200, alpha=1, beta=5, rho=0.1, Q=100):
        self.points = np.array(points)
        self.point_num = len(points)
        self.ant_num = ant_num
        self.max_iter = max_iter
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        self.dist_matrix = np.linalg.norm(self.points[:, None] - self.points[None, :], axis=2)
        self.dist_matrix[self.dist_matrix == 0] = 1e-8
        self.pheromone = np.ones_like(self.dist_matrix)
        self.best_len = np.inf
        self.best_path = []
        self.history = []

    def run(self):
        for _ in range(self.max_iter):
            all_paths = []
            all_lens = []
            for _ in range(self.ant_num):
                path, path_len = self.build_path()
                all_paths.append(path)
                all_lens.append(path_len)
                if path_len < self.best_len:
                    self.best_len = path_len
                    self.best_path = path.copy()
            self.update_pheromone(all_paths, all_lens)
            self.history.append(self.best_len)
        return self.best_path, self.best_len

    def build_path(self):
        path = [0]
        visited = set(path)
        while len(path) < self.point_num:
            cur = path[-1]
            prob = (self.pheromone[cur] ** self.alpha) * ((1.0 / self.dist_matrix[cur]) ** self.beta)
            prob[list(visited)] = 0
            prob /= prob.sum()
            next_p = np.random.choice(self.point_num, p=prob)
            path.append(next_p)
            visited.add(next_p)
        path.append(0)
        path_len = sum(self.dist_matrix[path[k], path[k + 1]] for k in range(len(path) - 1))
        return path, path_len

    def update_pheromone(self, all_paths, all_lens):
        self.pheromone *= (1 - self.rho)
        for path, path_len in zip(all_paths, all_lens):
            for k in range(len(path) - 1):
                i, j = path[k], path[k + 1]
                self.pheromone[i, j] += self.Q / path_len


def upsample_matrix(matrix, factor=4, method='cubic'):
    """增加矩阵分辨率，使小方格更小"""
    rows, cols = matrix.shape
    x = np.arange(cols)
    y = np.arange(rows)

    if method == 'linear':
        kx, ky = 1, 1
    elif method == 'cubic':
        kx, ky = 3, 3
    else:
        kx, ky = 3, 3

    f = RectBivariateSpline(y, x, matrix, kx=kx, ky=ky)

    x_new = np.linspace(0, cols - 1, cols * factor)
    y_new = np.linspace(0, rows - 1, rows * factor)

    matrix_upsampled = f(y_new, x_new)

    return matrix_upsampled, factor


# ====================== 【新增功能：航迹方向指示】 ======================
def add_direction_indicators(ax, path_coords, interval=5, arrow_length=0.4, arrow_width=0.2):
    """
    在航迹上添加方向指示箭头

    参数:
    - ax: matplotlib的坐标轴对象
    - path_coords: 航迹坐标数组，形状为(n, 2)，每行是(row, col)坐标
    - interval: 箭头间隔（多少个点添加一个箭头）
    - arrow_length: 箭头长度
    - arrow_width: 箭头宽度
    """
    for i in range(0, len(path_coords) - 1, interval):
        if i + 1 < len(path_coords):
            start = path_coords[i]
            end = path_coords[i + 1]

            # 计算线段中点
            mid_x = (start[1] + end[1]) / 2 + 0.5
            mid_y = (start[0] + end[0]) / 2 + 0.5

            # 计算方向向量
            dx = end[1] - start[1]
            dy = end[0] - start[0]

            # 计算方向角度
            angle = np.arctan2(dy, dx)

            # 添加箭头
            ax.arrow(mid_x, mid_y,
                     dx * 0.3, dy * 0.3,  # 缩短箭头长度以便在线上显示
                     head_width=arrow_width,
                     head_length=arrow_length,
                     fc='black',  # 箭头填充色
                     ec='black',  # 箭头边缘色
                     alpha=0.8,
                     zorder=12)


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

    print(f"\n✅ 检测到目标点：{len(target_points)} 个")
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
    print("\n✅ 最优路径（完整航迹）：")
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

    # -------------------------- 核心修改1：适配矩阵极值的颜色生成 --------------------------
    # 获取矩阵实际极值
    mat_min = grid.min()
    mat_max = grid.max()
    # 生成自定义配色（从绿到红，基于矩阵实际数值范围）
    colors_custom = []
    for i in range(256):
        # 归一化到矩阵的最小值-最大值范围
        value = mat_min + (i / 255) * (mat_max - mat_min)
        # 计算颜色渐变的分界点（矩阵范围的中点）
        mid_value = (mat_min + mat_max) / 2
        # 前半段（最小值→中点）：绿→黄；后半段（中点→最大值）：黄→红
        if value <= mid_value:
            ratio = (value - mat_min) / (mid_value - mat_min)
            r = int(ratio * 255)
            g = 255
            b = 0
        else:
            ratio = (value - mid_value) / (mat_max - mid_value)
            r = 255
            g = int(255 * (1 - ratio))
            b = 0
        color = f'#{r:02x}{g:02x}{b:02x}'
        colors_custom.append(color)

    cmap = mcolors.LinearSegmentedColormap.from_list('custom_green_red', colors_custom, N=256)
    # -------------------------- 核心修改2：设置vmin/vmax为矩阵极值 --------------------------
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
    print(f"\n✅ 纯热力图已保存至：{save_path}")
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

    print(f"\n✅ 在图中绘制了 {len(target_points)} 个目标关键点")

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