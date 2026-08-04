"""
TerraiNav - 地形威胁评估器

优化记录：
- print() → logging 模块，适配生产环境
- 评分映射字典提取为类级常量（TYPE_SCORES, HIDE_SCORES, SIGHT_SCORES, LEVEL_SCORES）
- _get_slope_score 增加异常处理，坡度解析失败时返回默认值 50
- assess_terrain 中的 groupby lambda 优化：预计算 argmax 索引避免重复查找
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TerrainAssessor:
    """地形威胁评估器：基于模糊层次分析法计算威胁分数"""

    # 【优化】评分映射提取为类级常量
    TYPE_SCORES = {
        "制高点": 100, "陡坡": 85, "冲沟": 70, "洼地": 50,
        "平地": 30, "山地": 80, "台地": 75, "建筑": 60, "道路": 40,
    }
    HIDE_SCORES = {"高": 100, "中": 60, "低": 20}
    SIGHT_SCORES = {"好": 100, "中": 60, "差": 10}
    LEVEL_SCORES = {"3级": 100, "2级": 60, "1级": 20}
    DEFAULT_SCORE = 50
    MAX_SLOPE_DEGREES = 40.0  # 坡度评分的参考最大角度

    def __init__(self):
        # 初始化FAHP权重
        self.factors, self.weights = self._get_fahp_weights()
        logger.info("=" * 70)
        logger.info("           【FAHP精准权重】军事地形威胁评估")
        logger.info("=" * 70)
        for i, (n, w) in enumerate(zip(self.factors, self.weights)):
            logger.info(f"{i + 1}. {n:<6} → 权重：{w:.4f}")
        logger.info("=" * 70)

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
    @classmethod
    def _get_ele_score(cls, h, min_h, max_h):
        return round(((h - min_h) / (max_h - min_h)) * 100, 1) if max_h > min_h else cls.DEFAULT_SCORE

    @classmethod
    def _get_type_score(cls, t):
        return cls.TYPE_SCORES.get(t, cls.DEFAULT_SCORE)

    @classmethod
    def _get_slope_score(cls, s):
        """【优化】增加异常处理：坡度解析失败时返回默认值"""
        try:
            s_val = float(str(s).replace("°", ""))
            return round(min(s_val / cls.MAX_SLOPE_DEGREES * 100, 100), 1)
        except (ValueError, AttributeError):
            return float(cls.DEFAULT_SCORE)

    @classmethod
    def _get_hide_score(cls, h):
        return cls.HIDE_SCORES.get(h, cls.DEFAULT_SCORE)

    @classmethod
    def _get_sight_score(cls, s):
        return cls.SIGHT_SCORES.get(s, cls.DEFAULT_SCORE)

    @classmethod
    def _get_level_score(cls, lvl):
        return cls.LEVEL_SCORES.get(lvl, 30)

    @classmethod
    def _score_row(cls, row, min_h, max_h):
        """【优化】单次遍历计算所有6项评分，替代6次 .apply() 扫描"""
        return pd.Series({
            "高程_100分": cls._get_ele_score(row["高程数值"], min_h, max_h),
            "类型_100分": cls._get_type_score(row["类型"]),
            "坡度_100分": cls._get_slope_score(row["坡度"]),
            "隐蔽性_100分": cls._get_hide_score(row["隐蔽性"]),
            "通视_100分": cls._get_sight_score(row["通视"]),
            "威胁等级_100分": cls._get_level_score(row["威胁等级"]),
        })

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

        # 【优化】单次 apply(axis=1) 替代 6 次 .apply()，减少 DataFrame 扫描次数
        min_h, max_h = df["高程数值"].min(), df["高程数值"].max()
        scores = df.apply(lambda row: self._score_row(row, min_h, max_h), axis=1)
        df["高程_100分"] = scores["高程_100分"]
        df["类型_100分"] = scores["类型_100分"]
        df["坡度_100分"] = scores["坡度_100分"]
        df["隐蔽性_100分"] = scores["隐蔽性_100分"]
        df["通视_100分"] = scores["通视_100分"]
        df["威胁等级_100分"] = scores["威胁等级_100分"]

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

        # 【优化】预计算每组最高分对应的行索引，避免 groupby lambda 中重复查找
        idx_max = df.groupby(["X坐标", "Y坐标"])["最终威胁分数"].idxmax()

        # ========== 坐标合并：同一坐标多个要素，取最大威胁分数 ==========
        df_merged = (
            df.groupby(["X坐标", "Y坐标"], as_index=False)
            .agg(
                {
                    "ID": "first",
                    "高程": "first",
                    "类型": lambda x: df.loc[idx_max[x.name], "类型"]
                        if x.name in idx_max else x.iloc[0],
                    "坡度": "first",
                    "隐蔽性": "first",
                    "通视": "first",
                    "威胁等级": lambda x: df.loc[idx_max[x.name], "威胁等级"]
                        if x.name in idx_max else x.iloc[0],
                    "备注": lambda x: " | ".join(set(x)),
                    "最终威胁分数": "max",
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
        logger.info("\n" + "=" * 90)
        logger.info("                    三维地图点位威胁评分排序表（100分制）【坐标合并后】")
        logger.info("=" * 90)
        for _, r in df_merged.iterrows():
            logger.info(
                f"第{r['排名']:2d}名 | X:{r['X坐标']:3d} Y:{r['Y坐标']:3d} | 威胁分:{r['最终威胁分数']:6.1f} | "
                f"{r['类型']:<5} {r['坡度']:<4} {r['威胁等级']} | {r['备注'][:30]}"
            )

        logger.info(f"\n[合并统计] 原始要素数: {len(df)} → 合并后: {len(df_merged)} 个坐标点")
        logger.info(f"[矩阵形状] X方向: {len(unique_x)} 个值 {unique_x}")
        logger.info(f"[矩阵形状] Y方向: {len(unique_y)} 个值 {unique_y}")

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

        # 填充威胁分数（使用矩阵索引）- 【优化】向量化赋值替代 df.iterrows()
        threat_matrix[df["矩阵Y"].values, df["矩阵X"].values] = df["最终威胁分数"].values

        logger.info(
            f"\n[OK] 威胁矩阵构建完成 | 矩阵尺寸：{threat_matrix.shape} ({rows}行×{cols}列)"
        )
        logger.info(f"   矩阵索引对应：threat_matrix[Y_index, X_index]")
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
