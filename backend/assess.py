import numpy as np
import pandas as pd


class TerrainAssessor:
    """地形威胁评估器：基于模糊层次分析法计算威胁分数"""

    def __init__(self):
        # 初始化FAHP权重
        self.factors, self.weights = self._get_fahp_weights()
        print("=" * 70)
        print("           【FAHP精准权重】军事地形威胁评估")
        print("=" * 70)
        for i, (n, w) in enumerate(zip(self.factors, self.weights)):
            print(f"{i + 1}. {n:<6} → 权重：{w:.4f}")
        print("=" * 70)

    def _get_fahp_weights(self):
        """获取FAHP权重"""
        fuzzy = np.array(
            [
                [
                    [1, 1, 1],
                    [1 / 2, 2 / 3, 1],
                    [1 / 3, 1 / 2, 2 / 3],
                    [1, 3 / 2, 2],
                    [3 / 2, 2, 5 / 2],
                    [1 / 5, 1 / 4, 1 / 3],
                ],
                [
                    [1, 3 / 2, 2],
                    [1, 1, 1],
                    [1 / 2, 2 / 3, 1],
                    [3 / 2, 2, 5 / 2],
                    [2, 5 / 2, 3],
                    [1 / 4, 1 / 3, 1 / 2],
                ],
                [
                    [3 / 2, 2, 3],
                    [1, 3 / 2, 2],
                    [1, 1, 1],
                    [2, 5 / 2, 3],
                    [5 / 2, 3, 7 / 2],
                    [1 / 3, 1 / 2, 2 / 3],
                ],
                [
                    [1 / 2, 2 / 3, 1],
                    [2 / 5, 1 / 2, 2 / 3],
                    [1 / 3, 1 / 2, 2 / 3],
                    [1, 1, 1],
                    [1, 3 / 2, 2],
                    [1 / 6, 1 / 5, 1 / 4],
                ],
                [
                    [2 / 5, 1 / 2, 2 / 3],
                    [1 / 3, 1 / 2, 2 / 3],
                    [2 / 7, 1 / 3, 1 / 2],
                    [1 / 2, 2 / 3, 1],
                    [1, 1, 1],
                    [1 / 6, 1 / 5, 1 / 4],
                ],
                [[3, 4, 5], [2, 3, 4], [3 / 2, 2, 3], [4, 5, 6], [4, 5, 6], [1, 1, 1]],
            ]
        )
        n = fuzzy.shape[0]
        s = np.sum(fuzzy, axis=1)
        w = []
        for v in s:
            score = (v[2] - v[0]) / 2 + v[1]
            w.append(score)
        w = np.array(w) / sum(w)
        names = ["高程", "地形类型", "坡度", "隐蔽性", "通视", "威胁等级"]
        return names, w

    # 单项评分函数
    @staticmethod
    def _get_ele_score(h, min_h, max_h):
        return round(((h - min_h) / (max_h - min_h)) * 100, 1) if max_h > min_h else 50

    @staticmethod
    def _get_type_score(t):
        d = {
            "制高点": 100,
            "陡坡": 85,
            "冲沟": 70,
            "洼地": 50,
            "平地": 30,
            "山地": 80,
            "台地": 75,
            "建筑": 60,
            "道路": 40,
        }
        return d.get(t, 50)

    @staticmethod
    def _get_slope_score(s):
        s_val = float(s.replace("°", ""))
        return round(min(s_val / 40 * 100, 100), 1)

    @staticmethod
    def _get_hide_score(h):
        d = {"高": 100, "中": 60, "低": 20}
        return d.get(h, 50)

    @staticmethod
    def _get_sight_score(s):
        d = {"好": 100, "中": 60, "差": 10}
        return d.get(s, 50)

    @staticmethod
    def _get_level_score(lvl):
        d = {"3级": 100, "2级": 60, "1级": 20}  # 适配agent返回的1/2/3级
        return d.get(lvl, 30)

    def assess_terrain(self, terrain_data):
        """
        评估地形威胁分数
        :param terrain_data: agent返回的地形区块列表
        :return: 带威胁分数的DataFrame、唯一坐标列表(排序后)
        """
        # 数据预处理
        df = pd.DataFrame(terrain_data)

        # 清洗数据类型
        df["高程数值"] = df["高程"].str.replace("m", "").astype(float)
        df["X坐标"] = df["X坐标"].astype(int)
        df["Y坐标"] = df["Y坐标"].astype(int)

        # 填充缺失的隐蔽性和通视字段
        if "隐蔽性" not in df.columns:
            df["隐蔽性"] = "中"
        else:
            df["隐蔽性"] = df["隐蔽性"].fillna("中")
        if "通视" not in df.columns:
            df["通视"] = "中"
        else:
            df["通视"] = df["通视"].fillna("中")

        # 计算单项100分制分数
        min_h, max_h = df["高程数值"].min(), df["高程数值"].max()
        df["高程_100分"] = df["高程数值"].apply(
            lambda x: self._get_ele_score(x, min_h, max_h)
        )
        df["类型_100分"] = df["类型"].apply(self._get_type_score)
        df["坡度_100分"] = df["坡度"].apply(self._get_slope_score)
        df["隐蔽性_100分"] = df["隐蔽性"].apply(self._get_hide_score)
        df["通视_100分"] = df["通视"].apply(self._get_sight_score)
        df["威胁等级_100分"] = df["威胁等级"].apply(self._get_level_score)

        # 计算最终威胁分数（权重×单项分）
        score_cols = [
            "高程_100分",
            "类型_100分",
            "坡度_100分",
            "隐蔽性_100分",
            "通视_100分",
            "威胁等级_100分",
        ]
        df["最终威胁分数"] = np.dot(df[score_cols], self.weights).round(2)

        # ========== 坐标合并：同一坐标多个要素，取最大威胁分数 ==========
        # 按坐标分组，取最大威胁分数
        df_merged = (
            df.groupby(["X坐标", "Y坐标"], as_index=False)
            .agg(
                {
                    "ID": "first",  # 保留第一个ID作为代表
                    "高程": "first",
                    "类型": lambda x: x.iloc[
                        np.argmax(df.loc[x.index, "最终威胁分数"])
                    ],  # 取最高分对应的类型
                    "坡度": "first",
                    "隐蔽性": "first",
                    "通视": "first",
                    "威胁等级": lambda x: x.iloc[
                        np.argmax(df.loc[x.index, "最终威胁分数"])
                    ],
                    "备注": lambda x: " | ".join(set(x)),  # 合并所有备注
                    "最终威胁分数": "max",  # 取最大威胁分数
                }
            )
            .reset_index(drop=True)
        )

        # 获取唯一的X和Y坐标值（排序后用于构建矩阵索引）
        unique_x = sorted(df["X坐标"].unique())
        unique_y = sorted(df["Y坐标"].unique())

        # 创建坐标到矩阵索引的映射
        x_to_idx = {x: i for i, x in enumerate(unique_x)}
        y_to_idx = {y: i for i, y in enumerate(unique_y)}

        # 为合并后的数据添加矩阵索引
        df_merged["矩阵X"] = df_merged["X坐标"].map(x_to_idx)
        df_merged["矩阵Y"] = df_merged["Y坐标"].map(y_to_idx)

        # 排序输出（按合并后的威胁分数）
        df_merged = df_merged.sort_values("最终威胁分数", ascending=False).reset_index(
            drop=True
        )
        df_merged["排名"] = df_merged.index + 1

        # 输出评估结果
        print("\n" + "=" * 90)
        print("                    三维地图点位威胁评分排序表（100分制）【坐标合并后】")
        print("=" * 90)
        for _, r in df_merged.iterrows():
            print(
                f"第{r['排名']:2d}名 | X:{r['X坐标']:3d} Y:{r['Y坐标']:3d} | 威胁分:{r['最终威胁分数']:6.1f} | "
                f"{r['类型']:<5} {r['坡度']:<4} {r['威胁等级']} | {r['备注'][:30]}"
            )

        print(f"\n[合并统计] 原始要素数: {len(df)} → 合并后: {len(df_merged)} 个坐标点")
        print(f"[矩阵形状] X方向: {len(unique_x)} 个值 {unique_x}")
        print(f"[矩阵形状] Y方向: {len(unique_y)} 个值 {unique_y}")

        return df_merged, unique_x, unique_y

    def build_threat_matrix(self, df, unique_x, unique_y):
        """
        构建威胁分数二维矩阵
        :param df: 带威胁分数的DataFrame（合并后）
        :param unique_x: 排序后的唯一X坐标列表
        :param unique_y: 排序后的唯一Y坐标列表
        :return: 二维威胁矩阵，形状为 (len(unique_y), len(unique_x))
        """
        # 矩阵形状：Y方向为行数，X方向为列数
        rows = len(unique_y)
        cols = len(unique_x)

        # 初始化零矩阵
        threat_matrix = np.zeros((rows, cols), dtype=np.float32)

        # 填充威胁分数（使用矩阵索引）
        for _, row in df.iterrows():
            mat_x = row["矩阵X"]  # X方向的矩阵索引
            mat_y = row["矩阵Y"]  # Y方向的矩阵索引
            threat_matrix[mat_y, mat_x] = row["最终威胁分数"]

        print(
            f"\n[OK] 威胁矩阵构建完成 | 矩阵尺寸：{threat_matrix.shape} ({rows}行×{cols}列)"
        )
        print(f"   矩阵索引对应：threat_matrix[Y_index, X_index]")
        return threat_matrix


if __name__ == "__main__":
    assessor = TerrainAssessor()
    # 测试数据 - 模拟3×3矩阵（X:0,100,200  Y:0,100,200）
    test_data = [
        # (0,0) 位置有2个要素，应该合并取最大威胁分数
        {
            "ID": 1,
            "X坐标": 0,
            "Y坐标": 0,
            "高程": "210m",
            "类型": "建筑",
            "坡度": "5°",
            "隐蔽性": "中",
            "通视": "好",
            "威胁等级": "2级",
            "备注": "主阵地",
        },
        {
            "ID": 2,
            "X坐标": 0,
            "Y坐标": 0,
            "高程": "195m",
            "类型": "道路",
            "坡度": "8°",
            "隐蔽性": "低",
            "通视": "好",
            "威胁等级": "1级",
            "备注": "道路",
        },
        # (100,0) 位置
        {
            "ID": 3,
            "X坐标": 100,
            "Y坐标": 0,
            "高程": "320m",
            "类型": "制高点",
            "坡度": "22°",
            "隐蔽性": "中",
            "通视": "好",
            "威胁等级": "3级",
            "备注": "山脊",
        },
        # (200,0) 位置
        {
            "ID": 4,
            "X坐标": 200,
            "Y坐标": 0,
            "高程": "85m",
            "类型": "林地",
            "坡度": "30°",
            "隐蔽性": "高",
            "通视": "差",
            "威胁等级": "1级",
            "备注": "树林",
        },
        # (0,100) 位置
        {
            "ID": 5,
            "X坐标": 0,
            "Y坐标": 100,
            "高程": "380m",
            "类型": "制高点",
            "坡度": "25°",
            "隐蔽性": "高",
            "通视": "好",
            "威胁等级": "3级",
            "备注": "高点",
        },
        # (100,100) 位置有2个要素
        {
            "ID": 6,
            "X坐标": 100,
            "Y坐标": 100,
            "高程": "100m",
            "类型": "道路",
            "坡度": "5°",
            "隐蔽性": "低",
            "通视": "好",
            "威胁等级": "1级",
            "备注": "道路2",
        },
        {
            "ID": 7,
            "X坐标": 100,
            "Y坐标": 100,
            "高程": "135m",
            "类型": "林地",
            "坡度": "15°",
            "隐蔽性": "高",
            "通视": "差",
            "威胁等级": "2级",
            "备注": "树林2",
        },
        # (200,200) 位置
        {
            "ID": 8,
            "X坐标": 200,
            "Y坐标": 200,
            "高程": "280m",
            "类型": "山地",
            "坡度": "20°",
            "隐蔽性": "中",
            "通视": "中",
            "威胁等级": "2级",
            "备注": "山地",
        },
    ]

    print("\n" + "=" * 60)
    print("测试：坐标合并 + 动态矩阵形状")
    print("=" * 60)

    df_merged, unique_x, unique_y = assessor.assess_terrain(test_data)
    matrix = assessor.build_threat_matrix(df_merged, unique_x, unique_y)

    print("\n威胁矩阵：")
    print(f"形状: {matrix.shape} (3行×3列)")
    print(matrix)
