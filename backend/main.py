"""
TerraiNav - 地形适应无人机巡逻系统
命令行主程序

功能：
1. 调用AI识别地形要素
2. FAHP模糊层次分析评估威胁
3. ACO蚁群算法规划最优路径
4. 生成热力图与路线可视化
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import TerrainAnalyzer
from assess import TerrainAssessor
from path import PathPlanner


def main():
    print("=" * 70)
    print("           TerraiNav - 地形适应无人机巡逻系统")
    print("=" * 70)
    print()

    # ========== 配置区 ==========
    # 阿里云API Key（可设置环境变量 DASHSCOPE_API_KEY）
    api_key = os.getenv("DASHSCOPE_API_KEY") or "sk-6dc29ccf2738472dbc3900dc48eb5d42"

    # 图片路径
    image_path = "微信图片_20260417183430.jpg"

    # 分析参数
    scale = 0.35  # 比例尺 (米/像素)
    block_size = 100  # 每块边长 (米)
    max_workers = 2  # 并行线程数

    # 路径规划参数
    ant_num = 50  # 蚁群数量
    max_iter = 200  # 最大迭代次数
    # ========== 配置区结束 ==========

    try:
        # 0. 检查图片是否存在
        if not os.path.exists(image_path):
            print(f"❌ 错误：图片文件不存在 - {image_path}")
            print("请将地形图片放在当前目录，或修改 image_path 配置")
            return

        print(f"📁 使用图片：{image_path}")
        print()

        # 1. 初始化分析器
        print("=" * 70)
        print("【第1步】初始化AI分析器")
        print("=" * 70)
        analyzer = TerrainAnalyzer.create_analyzer(
            api_key=api_key,
            model="qwen3.6-plus",
            max_workers=max_workers,
        )
        print("✅ AI分析器初始化成功\n")

        # 2. 地形识别
        print("=" * 70)
        print("【第2步】AI地形识别")
        print("=" * 70)
        print(f"参数：比例尺={scale}m/px, 区块大小={block_size}m, 并行数={max_workers}")
        print("-" * 70)

        terrain_data = analyzer.analyze_terrain(
            image_path=image_path,
            scale=scale,
            block_size=block_size,
            max_workers=max_workers,
        )

        print()
        print(f"✅ 地形识别完成，共识别到 {len(terrain_data)} 个地形要素\n")

        # 3. 威胁评估
        print("=" * 70)
        print("【第3步】FAHP威胁度评估")
        print("=" * 70)
        assessor = TerrainAssessor()
        df, unique_x, unique_y = assessor.assess_terrain(terrain_data)

        print(f"\n✅ 威胁评估完成")
        print(f"   - X方向: {len(unique_x)} 个唯一坐标点")
        print(f"   - Y方向: {len(unique_y)} 个唯一坐标点\n")

        # 4. 构建威胁矩阵
        print("=" * 70)
        print("【第4步】构建威胁矩阵")
        print("=" * 70)
        threat_matrix = assessor.build_threat_matrix(df, unique_x, unique_y)
        print(
            f"✅ 威胁矩阵构建完成，尺寸：{threat_matrix.shape[0]} x {threat_matrix.shape[1]}\n"
        )

        # 5. 路径规划
        print()
        print("=" * 70)
        print("【第5步】ACO蚁群路径规划")
        print("=" * 70)
        planner = PathPlanner()

        # 检测关键点
        keypoints = planner.detect_keypoints(threat_matrix)
        print(f"检测到 {len(keypoints)} 个关键威胁点")

        best_len = 0
        path_coords = None

        if keypoints:
            print("关键点坐标：")
            for i, p in enumerate(keypoints):
                print(
                    f"  关键点{i + 1}: ({p[0]}, {p[1]}) | 威胁分数：{threat_matrix[p]:.1f}"
                )

            # 加入起点(0,0)
            all_points = [(0, 0)] + keypoints
            print(f"\n🔍 使用蚁群算法规划最优路径...")
            print(f"   - 蚁群数量: {ant_num}")
            print(f"   - 最大迭代: {max_iter}")

            aco = planner.ACO_TSP(all_points, ant_num=ant_num, max_iter=max_iter)
            best_path, best_len = aco.run()

            path_coords = [all_points[idx] for idx in best_path]
            print(f"\n✅ 路径规划完成！")
            print(f"   最短路径长度：{best_len:.2f}")
            print(f"   最优路径：")
            for i, p in enumerate(path_coords):
                if i < len(path_coords) - 1:
                    print(f"     ({p[0]}, {p[1]}) → ", end="")
                else:
                    print(f"     ({p[0]}, {p[1]})")
        else:
            print("⚠️ 未检测到有效关键点，跳过路径规划")

        # 6. 可视化
        print()
        print("=" * 70)
        print("【第6步】生成可视化")
        print("=" * 70)

        # 保存威胁矩阵到文件
        import numpy as np

        matrix_file = "threat_matrix.csv"
        np.savetxt(matrix_file, threat_matrix, delimiter=",", fmt="%.2f")
        print(f"✅ 威胁矩阵已保存到: {matrix_file}")

        # 生成热力图
        print("正在生成热力图...")
        if path_coords:
            fig = planner.get_heatmap_figure(threat_matrix, path_coords)
        else:
            fig = planner.get_heatmap_figure(threat_matrix, None)

        # 保存图片
        heatmap_file = "threat_heatmap.png"
        fig.savefig(heatmap_file, dpi=150, bbox_inches="tight")
        print(f"✅ 热力图已保存到: {heatmap_file}")

        # 关闭matplotlib窗口（如果show了的话）
        import matplotlib.pyplot as plt

        plt.close(fig)

        # 7. 保存结果到JSON
        print()
        print("=" * 70)
        print("【第7步】保存分析结果")
        print("=" * 70)

        import json

        # 保存评估结果
        result_file = "analysis_result.json"
        result_data = {
            "terrain_count": len(terrain_data),
            "threat_matrix_shape": list(threat_matrix.shape),
            "keypoints_count": len(keypoints),
            "keypoints": [(int(p[0]), int(p[1])) for p in keypoints],
            "best_path_length": float(best_len) if keypoints else None,
            "best_path": [(int(p[0]), int(p[1])) for p in path_coords]
            if path_coords
            else None,
            "threat_ranking": [
                {
                    "rank": int(row["排名"]),
                    "coordinates": f"({int(row['X坐标'])}, {int(row['Y坐标'])})",
                    "threat_score": float(row["最终威胁分数"]),
                    "type": str(row["类型"]),
                    "slope": str(row["坡度"]),
                    "threat_level": str(row["威胁等级"]),
                    "remarks": str(row["备注"])[:50],
                }
                for _, row in df.iterrows()
            ],
        }

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 分析结果已保存到: {result_file}")

        # 打印威胁排名Top10
        print()
        print("=" * 70)
        print("           威胁评分排名 Top 10")
        print("=" * 70)
        print(
            f"{'排名':^4} | {'坐标':^12} | {'威胁分':^8} | {'类型':^6} | {'坡度':^6} | {'等级':^4}"
        )
        print("-" * 70)

        for _, row in df.head(10).iterrows():
            print(
                f"{row['排名']:^4} | "
                f"({row['X坐标']:>3}, {row['Y坐标']:>3}) | "
                f"{row['最终威胁分数']:^8.1f} | "
                f"{row['类型']:<6} | "
                f"{row['坡度']:<6} | "
                f"{row['威胁等级']:<4}"
            )

        print()
        print("=" * 70)
        print("🎉 所有任务执行完成！")
        print("=" * 70)
        print()
        print("生成的文件：")
        print(f"  📊 {matrix_file}  - 威胁矩阵CSV")
        print(f"  🗺️  {heatmap_file}  - 威胁热力图")
        print(f"  📄 {result_file} - 完整分析结果JSON")
        print()

    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 执行失败：{e}")
        print("=" * 70)
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
