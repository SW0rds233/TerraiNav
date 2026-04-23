from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import numpy as np
from PIL import Image  # 只用 Pillow，不用 cv2
from path import PathPlanner

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
CORS(app)

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================
# 纯 Pillow 实现区块切割（无 cv2）
# ==========================
class ImageAgent:
    @staticmethod
    def analyze_image_blocks(image_path, block_size=32):
        try:
            # 用 Pillow 打开图片 → 转灰度
            img = Image.open(image_path).convert('L')
            img_np = np.array(img)
            h, w = img_np.shape

            # 计算行列
            rows = h // block_size
            cols = w // block_size

            blocks = []
            for i in range(rows):
                for j in range(cols):
                    y1 = i * block_size
                    y2 = y1 + block_size
                    x1 = j * block_size
                    x2 = x1 + block_size

                    block = img_np[y1:y2, x1:x2]
                    mean_gray = float(np.mean(block))

                    blocks.append({
                        "block_pos": (i, j),
                        "mean_gray": mean_gray
                    })

            return blocks, rows, cols

        except Exception as e:
            logging.error(f"区块分析失败: {e}")
            raise

# ==========================
# 评估模块：生成侦测值矩阵
# ==========================
class Assessor:
    @staticmethod
    def calculate(blocks, rows, cols):
        matrix = np.zeros((rows, cols), dtype=np.float32)
        for b in blocks:
            i, j = b["block_pos"]
            val = b["mean_gray"]
            matrix[i, j] = 100 - val  # 越暗 → 侦测值越高
        return matrix

# ==========================
# 路径规划
# ==========================
planner = PathPlanner()

# ==========================
# 网页上传入口
# ==========================
@app.route('/')
def index():
    return '''
    <h1>图片区块侦测 + 路径规划</h1>
    <form action="/run" method="post" enctype="multipart/form-data">
        <input type="file" name="image" accept="image/*"><br><br>
        <button>开始分析</button>
    </form>
    '''

# ==========================
# 主流程：上传 → 区块 → 矩阵 → 热力图+路线
# ==========================
@app.route('/run', methods=['POST'])
def run():
    try:
        # 1. 保存图片
        file = request.files['image']
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        # 2. Agent 切割区块
        blocks, rows, cols = ImageAgent.analyze_image_blocks(path)

        # 3. Assess 生成矩阵
        matrix = Assessor.calculate(blocks, rows, cols)

        # 4. 生成热力图 + 路线
        planner.plan_path(matrix)

        return jsonify({
            "status": "ok",
            "matrix_shape": [rows, cols],
            "message": "已生成热力图和路径"
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)