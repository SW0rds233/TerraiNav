"""
TerraiNav Web API - 地形威胁评估与路径规划服务
提供核心API：
1. /api/get_heatmap - 返回热力图图片URL
2. /api/get_pathmap - 返回路径规划图URL
3. /api/get_threat_data - 返回威胁度矩阵和巡逻点信息
4. /api/auth/login - 用户登录
5. /api/auth/register - 用户注册
6. /api/history - 历史记录管理
"""

from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
import os
import logging
import uuid
import json
import base64
import io
import threading
import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.interactive(False)
from PIL import Image
from datetime import datetime
import secrets

# 导入业务模块
from agent import TerrainAnalyzer
from assess import TerrainAssessor
from path import PathPlanner

# 导入数据库模块
from database import init_db, UserManager, HistoryManager

# ========================== 配置 ==========================
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
app = Flask(__name__, static_folder="static", static_url_path="/static")

# CORS配置 - 支持开发和生产环境
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
CORS(
    app,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS.split(",") if ALLOWED_ORIGINS != "*" else "*"}},
    supports_credentials=False,
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    expose_headers=["Content-Type", "X-API-Key", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

app.config["CORS_HEADERS"] = "Content-Type, X-API-Key, Authorization"
app.config["CORS_SUPPORTS_CREDENTIALS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))

# 初始化数据库
try:
    init_db()
    logging.info("数据库初始化成功")
except Exception as e:
    logging.error(f"数据库初始化失败: {e}")

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    allowed = ALLOWED_ORIGINS.split(",") if ALLOWED_ORIGINS != "*" else ["*"]
    if "*" in allowed or origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response

@app.route("/api/<path:path>", methods=["OPTIONS"])
def api_options(path):
    return "", 204

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "static", "output")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)

# 上传文件最大大小 50MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# ========================== 业务组件 ==========================
# 全局分析器（需要在前端初始化时设置）
analyzer = None
assessor = TerrainAssessor()
planner = PathPlanner()

# 后端任务管理
TASKS = {}
TASK_LOCK = threading.Lock()


# ========================== 工具函数 ==========================
def parse_divide(divide_str):
    """解析分块字符串，如 '4*6' -> (4, 6)"""
    try:
        parts = divide_str.strip().split("*")
        if len(parts) != 2:
            raise ValueError("分块字符串格式错误，应为 '行*列'，如 '4*6'")
        rows = int(parts[1])
        cols = int(parts[0])
        if rows <= 0 or cols <= 0:
            raise ValueError("行和列必须为正整数")
        return rows, cols
    except Exception as e:
        raise ValueError(f"分块字符串解析失败: {e}")


def parse_start_point(start_point_str, rows, cols, default=(0, 0)):
    """解析起始区块字段，如 '1,1' -> (1, 1)"""
    if not start_point_str:
        return default

    try:
        parts = [p.strip() for p in start_point_str.split(",") if p.strip()]
        if len(parts) != 2:
            raise ValueError("起始区块格式错误，应为 '行,列'，如 '1,1'")
        start_row = int(parts[0])
        start_col = int(parts[1])
        if start_row < 0 or start_col < 0 or start_row >= rows or start_col >= cols:
            raise ValueError(
                f"起始区块超出范围，应在 0-{rows-1}, 0-{cols-1} 之间"
            )
        return (start_row, start_col)
    except Exception as e:
        raise ValueError(f"起始区块解析失败: {e}")


def json_safe_point(point):
    """Convert a coordinate tuple to JSON-safe [int, int] list."""
    if point is None:
        return None
    return [int(point[0]), int(point[1])]


def save_upload_file(file):
    """保存上传的图片文件"""
    if file is None:
        raise ValueError("未上传文件")

    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".bmp"]:
        raise ValueError(f"不支持的图片格式: {ext}")

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filepath


def save_output_image(fig, prefix="img"):
    """保存matplotlib生成的图片，返回URL路径"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{prefix}_{timestamp}_{unique_id}.png"
    filepath = os.path.join(OUTPUT_FOLDER, filename)

    fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
    import matplotlib.pyplot as plt

    plt.close(fig)

    # 返回相对URL路径
    return f"/static/output/{filename}"


def get_image_size(filepath):
    """获取图片尺寸 (width, height)"""
    with Image.open(filepath) as img:
        return img.size  # (width, height)


def create_task_record(task_type, payload):
    task_id = uuid.uuid4().hex
    record = {
        "task_id": task_id,
        "task_type": task_type,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "progress": "pending",
        "progress_percent": 0,
        "result": None,
        "error": None,
        "payload": payload,
    }
    with TASK_LOCK:
        TASKS[task_id] = record
    return task_id, record


def update_task_record(task_id, **fields):
    with TASK_LOCK:
        task = TASKS.get(task_id)
        if not task:
            return
        task.update(fields)
        task["updated_at"] = datetime.utcnow().isoformat() + "Z"
    return task


def get_task_record(task_id):
    with TASK_LOCK:
        return TASKS.get(task_id)


def build_threat_result(task_id, filename, img_width, img_height, rows, cols, start_point):
    """重用现有威胁数据处理逻辑，返回结果字典。"""
    task = get_task_record(task_id)
    if not task:
        raise ValueError("任务不存在")

    payload = task["payload"]
    analyzer_local = payload["analyzer"]
    assessor_local = payload["assessor"]
    planner_local = payload["planner"]

    update_task_record(task_id, progress="AI地形分析中", progress_percent=5)
    logging.info("开始AI地形分析...")

    def inline_progress_callback(completed, total, message):
        percent = int(round(completed / total * 60)) if total else 50
        update_task_record(
            task_id,
            status="running",
            progress=message,
            progress_percent=min(percent, 60),
        )

    terrain_data = analyzer_local.analyze_terrain(
        image_path=filename,
        rows=rows,
        cols=cols,
        max_workers=2,
        progress_callback=inline_progress_callback,
    )

    logging.info(f"AI分析完成，识别到 {len(terrain_data)} 个地形要素")
    update_task_record(task_id, progress="AI分析完成，开始威胁评估", progress_percent=65)

    # 威胁评估
    df, unique_x, unique_y = assessor_local.assess_terrain(terrain_data)
    threat_matrix = assessor_local.build_threat_matrix(df, unique_x, unique_y)

    logging.info(f"威胁矩阵构建完成: {threat_matrix.shape}")
    update_task_record(task_id, progress="威胁矩阵构建完成，开始关键点检测", progress_percent=70)

    # 检测关键点
    keypoints = planner_local.detect_keypoints(threat_matrix)

    patrol_points = []
    for idx, (row, col) in enumerate(keypoints):
        rank = idx + 1
        block_row = row
        block_col = col
        threat_score = float(threat_matrix[row, col])
        block_width = img_width // cols
        block_height = img_height // rows
        pixel_x = int(block_col * block_width + block_width // 2)
        pixel_y = int(block_row * block_height + block_height // 2)
        pixel_coords = [pixel_x, pixel_y]
        block_position = f"区块({int(block_row)}, {int(block_col)})"
        threat_reason = ""
        for _, r in df.iterrows():
            if r.get("矩阵Y") == row and r.get("矩阵X") == col:
                threat_reason = f"{r.get('类型', '未知')}, {r.get('坡度', '未知')}, {r.get('威胁等级', '未知')}, {r.get('备注', '')}"
                break
        patrol_points.append(
            {
                "rank": rank,
                "block": f"({block_row}, {block_col})",
                "threat_score": threat_score,
                "pixel_coords": pixel_coords,
                "block_position": block_position,
                "threat_reason": threat_reason,
            }
        )

    patrol_points.sort(key=lambda x: x["threat_score"], reverse=True)
    for idx, pt in enumerate(patrol_points):
        pt["rank"] = idx + 1

    logging.info(f"巡逻点信息构建完成: {len(patrol_points)} 个点")
    update_task_record(task_id, progress="关键点检测完成，开始生成热力图", progress_percent=75)

    output_size = (img_width, img_height)
    fig_heatmap = planner_local.get_pure_heatmap(threat_matrix, output_size)
    heatmap_url = save_output_image(fig_heatmap, "heatmap")
    logging.info(f"热力图生成完成: {heatmap_url}")
    update_task_record(task_id, progress="热力图生成完成", progress_percent=90)

    path_coords = None
    best_path_length = 0
    pathmap_url = ""
    if keypoints:
        update_task_record(task_id, progress="开始路径规划", progress_percent=92)
        all_points = [start_point] + keypoints
        aco = planner_local.ACO_TSP(all_points, ant_num=50, max_iter=200)
        best_path, best_len = aco.run()
        path_coords = [all_points[idx] for idx in best_path]
        best_path_length = float(best_len)
        logging.info(f"路径规划完成: {len(path_coords)} 个点, 长度: {best_path_length:.2f}")
        update_task_record(task_id, progress="路径规划完成，正在生成路径图", progress_percent=94)
        fig_path = planner_local.get_pure_pathmap(threat_matrix, path_coords, output_size)
        pathmap_url = save_output_image(fig_path, "pathmap")
        logging.info(f"路径图生成完成: {pathmap_url}")
        update_task_record(task_id, progress="路径图生成完成", progress_percent=96)

    return {
        "success": True,
        "threat_matrix": threat_matrix.astype(float).tolist(),
        "patrol_points": patrol_points,
        "matrix_shape": [int(threat_matrix.shape[0]), int(threat_matrix.shape[1])],
        "image_size": [int(img_width), int(img_height)],
        "path_coords": [json_safe_point(pt) for pt in path_coords] if path_coords else None,
        "best_path_length": float(best_path_length),
        "heatmap_url": heatmap_url,
        "pathmap_url": pathmap_url,
    }


def process_threat_task(task_id):
    task = get_task_record(task_id)
    if not task:
        return

    payload = task["payload"]
    image_path = payload["image_path"]
    img_width = payload["img_width"]
    img_height = payload["img_height"]
    rows = payload["rows"]
    cols = payload["cols"]
    start_point = payload["start_point"]

    update_task_record(task_id, status="running", progress="任务执行中", progress_percent=1)
    try:
        result = build_threat_result(
            task_id,
            image_path,
            img_width,
            img_height,
            rows,
            cols,
            start_point,
        )
        update_task_record(task_id, status="completed", progress="完成", progress_percent=100, result=result)
    except Exception as e:
        logging.error(f"后台任务失败: {e}")
        import traceback
        traceback.print_exc()
        update_task_record(task_id, status="failed", progress="失败", error=str(e))


# ========================== API 1: 热力图 ==========================
@app.route("/api/init", methods=["POST"])
def init_api():
    """初始化AI分析器"""
    global analyzer

    try:
        data = request.get_json()
        api_key = data.get("api_key", "").strip()

        if not api_key:
            return jsonify({"success": False, "error": "API Key不能为空"}), 400

        # 创建分析器（使用用户提供的API Key）
        analyzer = TerrainAnalyzer.create_analyzer(
            api_key=api_key,
            model="qwen3.6-plus",
            max_workers=2,
        )

        return jsonify({"success": True, "message": "API初始化成功"})

    except Exception as e:
        logging.error(f"API初始化失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/get_heatmap", methods=["POST"])
def get_heatmap():
    """
    API 1: 获取热力图
    输入: divide (分块字符串如 "4*6"), map_picture (地图图片文件)
    输出: heatmap_url (热力图图片URL)
    """
    global analyzer

    try:
        # 1. 获取参数
        divide = request.form.get("divide", "").strip()
        map_file = request.files.get("map_picture")

        if not divide:
            return jsonify({"success": False, "error": "分块参数不能为空"}), 400
        if not map_file:
            return jsonify({"success": False, "error": "地图图片不能为空"}), 400
        if analyzer is None:
            return jsonify(
                {"success": False, "error": "请先调用 /api/init 初始化API"}
            ), 400

        # 2. 解析分块参数
        rows, cols = parse_divide(divide)

        # 3. 保存上传的图片
        image_path = save_upload_file(map_file)
        img_width, img_height = get_image_size(image_path)

        logging.info(f"收到图片: {map_file.filename}, 尺寸: {img_width}x{img_height}")
        logging.info(f"分块: {rows} x {cols}")

        # 4. 调用AI分析地形
        logging.info("开始AI地形分析...")
        terrain_data = analyzer.analyze_terrain(
            image_path=image_path,
            rows=rows,
            cols=cols,
            max_workers=2,
        )

        logging.info(f"AI分析完成，识别到 {len(terrain_data)} 个地形要素")

        # 5. 威胁评估
        df, unique_x, unique_y = assessor.assess_terrain(terrain_data)
        threat_matrix = assessor.build_threat_matrix(df, unique_x, unique_y)

        logging.info(f"威胁矩阵构建完成: {threat_matrix.shape}")

        # 6. 检测关键点并生成路径
        keypoints = planner.detect_keypoints(threat_matrix)

        path_coords = None
        best_path_length = 0

        if keypoints:
            start_point_str = (
                request.form.get("start_point")
                or (request.get_json(silent=True) or {}).get("start_point")
                or "0,0"
            )
            start_point = parse_start_point(start_point_str, rows, cols)
            all_points = [start_point] + keypoints
            aco = planner.ACO_TSP(all_points, ant_num=50, max_iter=200)
            best_path, best_len = aco.run()
            path_coords = [all_points[idx] for idx in best_path]
            best_path_length = float(best_len)
            logging.info(f"路径规划: {len(path_coords)} 点, 长度: {best_path_length:.2f}")
        
        # 7. 生成纯热力图（与原图尺寸一致，无坐标轴图例）
        output_size = (img_width, img_height)
        fig = planner.get_pure_heatmap(threat_matrix, output_size)
        heatmap_url = save_output_image(fig, "heatmap")
        logging.info(f"纯热力图生成完成: {heatmap_url}")

        # 8. 生成路径图（与原图尺寸一致，无坐标轴图例）
        pathmap_url = ""
        if path_coords:
            fig_path = planner.get_pure_pathmap(threat_matrix, path_coords, output_size)
            pathmap_url = save_output_image(fig_path, "pathmap")
            logging.info(f"路径图生成完成: {pathmap_url}")

        return jsonify(
            {
                "success": True,
                "heatmap_url": heatmap_url,
                "pathmap_url": pathmap_url,
                "matrix_shape": [int(threat_matrix.shape[0]), int(threat_matrix.shape[1])],
                "original_size": [int(img_width), int(img_height)],
                "path_coords": [json_safe_point(pt) for pt in path_coords]
                if path_coords
                else None,
                "best_path_length": float(best_path_length),
            }
        )

    except Exception as e:
        logging.error(f"生成热力图失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ========================== API 2: 路径规划图 ==========================
@app.route("/api/get_pathmap", methods=["POST"])
def get_pathmap():
    """
    API 2: 获取路径规划图
    输入: threat_matrix (威胁度矩阵，JSON格式二维数组)
    输出: pathmap_url (路径规划图URL)
    """
    try:
        # 1. 获取威胁矩阵
        data = request.get_json()
        threat_matrix_list = data.get("threat_matrix", [])

        if not threat_matrix_list:
            return jsonify({"success": False, "error": "威胁矩阵不能为空"}), 400

        # 转换为numpy数组
        threat_matrix = np.array(threat_matrix_list, dtype=np.float32)

        logging.info(f"收到威胁矩阵: {threat_matrix.shape}")

        # 2. 检测关键点
        keypoints = planner.detect_keypoints(threat_matrix)
        logging.info(f"检测到 {len(keypoints)} 个关键点")

        # 3. 路径规划
        path_coords = None
        best_len = 0

        if keypoints:
            all_points = [(0, 0)] + keypoints
            aco = planner.ACO_TSP(all_points, ant_num=50, max_iter=200)
            best_path, best_len = aco.run()
            path_coords = [all_points[idx] for idx in best_path]

        # 4. 生成路径规划图（不扩展到原图尺寸，只需要与矩阵尺寸匹配）
        fig = planner.get_heatmap_figure(threat_matrix, path_coords)

        # 5. 保存并返回URL
        pathmap_url = save_output_image(fig, "pathmap")

        logging.info(f"路径规划图生成完成: {pathmap_url}")

        return jsonify(
            {
                "success": True,
                "pathmap_url": pathmap_url,
                "keypoints_count": len(keypoints),
                "best_path_length": float(best_len),
                "path_coords": [json_safe_point(pt) for pt in path_coords]
                if path_coords
                else None,
            }
        )

    except Exception as e:
        logging.error(f"生成路径规划图失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ========================== API 3: 威胁数据 ==========================
@app.route("/api/get_threat_data", methods=["POST"])
def get_threat_data():
    """
    API 3: 启动威胁分析后台任务
    输入: divide, map_picture, start_point
    返回: task_id
    """
    global analyzer

    try:
        divide = request.form.get("divide", "").strip()
        map_file = request.files.get("map_picture")
        start_point_str = request.form.get("start_point", "0,0").strip()

        if not divide:
            return jsonify({"success": False, "error": "分块参数不能为空"}), 400
        if not map_file:
            return jsonify({"success": False, "error": "地图图片不能为空"}), 400
        if analyzer is None:
            return jsonify({"success": False, "error": "请先调用 /api/init 初始化API"}), 400

        rows, cols = parse_divide(divide)

        try:
            start_parts = start_point_str.split(",")
            if len(start_parts) != 2:
                raise ValueError("起始区块格式错误，应为 '行,列'，如 '1,1'")
            start_row = int(start_parts[0].strip())
            start_col = int(start_parts[1].strip())
            if start_row < 0 or start_col < 0 or start_row >= rows or start_col >= cols:
                raise ValueError(f"起始区块超出范围，应在 0-{rows-1}, 0-{cols-1} 之间")
            start_point = (start_row, start_col)
        except Exception as e:
            raise ValueError(f"起始区块参数解析失败: {e}")

        image_path = save_upload_file(map_file)
        img_width, img_height = get_image_size(image_path)

        logging.info(f"收到图片: {map_file.filename}, 尺寸: {img_width}x{img_height}")
        logging.info(f"分块: {rows} x {cols}")
        logging.info(f"起始区块: {start_point}")

        payload = {
            "analyzer": analyzer,
            "assessor": assessor,
            "planner": planner,
            "image_path": image_path,
            "img_width": img_width,
            "img_height": img_height,
            "rows": rows,
            "cols": cols,
            "start_point": start_point,
        }
        task_id, _ = create_task_record("get_threat_data", payload)
        worker = threading.Thread(target=process_threat_task, args=(task_id,), daemon=True)
        worker.start()

        return jsonify({"success": True, "task_id": task_id, "status": "pending"})

    except Exception as e:
        logging.error(f"获取威胁数据失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/task_status/<task_id>", methods=["GET"])
def task_status(task_id):
    task = get_task_record(task_id)
    if not task:
        return jsonify({"success": False, "error": "任务不存在"}), 404

    response = {
        "success": True,
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "progress_percent": task.get("progress_percent", 0),
        "error": task["error"],
        "result": task["result"] if task["status"] == "completed" else None,
    }
    return jsonify(response)


# ========================== 健康检查 ==========================
@app.route("/api/health", methods=["GET"])
def health_check():
    """Railway 健康检查端点"""
    return jsonify({"status": "ok", "service": "TerraiNav API"})

@app.route("/")
def index():
    """API说明页"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>TerraiNav API</title>
        <style>
            body { font-family: Microsoft YaHei, Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2980b9; }
            .api-card { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; }
            pre { background: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🗺️ TerraiNav API</h1>
        <p>地形威胁评估与路径规划服务</p>
        
        <div class="api-card">
            <h2>1. 初始化API</h2>
            <code>POST /api/init</code>
            <p>需要先调用此接口初始化AI分析器</p>
            <pre>{
    "api_key": "your-api-key"
}</pre>
        </div>
        
        <div class="api-card">
            <h2>2. 获取热力图</h2>
            <code>POST /api/get_heatmap</code>
            <p>输入分块字符串和地图图片，返回热力图URL</p>
            <pre>form-data:
    divide: "4*6"
    map_picture: [图片文件]</pre>
        </div>
        
        <div class="api-card">
            <h2>3. 获取路径规划图</h2>
            <code>POST /api/get_pathmap</code>
            <p>输入威胁度矩阵，返回路径规划图URL</p>
            <pre>{
    "threat_matrix": [[...], [...], ...]
}</pre>
        </div>
        
        <div class="api-card">
            <h2>4. 获取威胁数据</h2>
            <code>POST /api/get_threat_data</code>
            <p>输入分块字符串和地图图片，返回威胁矩阵和巡逻点信息</p>
            <pre>form-data:
    divide: "4*6"
    map_picture: [图片文件]

返回:
{
    "threat_matrix": [[...], [...], ...],
    "patrol_points": [
        {"rank": 1, "block": "(0,1)", "threat_score": 87.5, "pixel_coords": [200, 100], "block_position": "区块(0,1)", "threat_reason": "制高点,35°,3级,..."},
        ...
    ]
}</pre>
        </div>
    </body>
    </html>
    """


# ========================== 用户认证API ==========================
@app.route("/api/auth/login", methods=["POST"])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"success": False, "error": "用户名和密码不能为空"}), 400

        # 验证用户
        user = UserManager.authenticate_user(username, password)

        if user:
            # 生成token（简单实现，实际项目应使用JWT）
            token = secrets.token_hex(32)
            
            return jsonify({
                "success": True,
                "message": "登录成功",
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "usertype": user.usertype
                }
            })
        else:
            return jsonify({"success": False, "error": "用户名或密码错误"}), 401

    except Exception as e:
        logging.error(f"登录失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/register", methods=["POST"])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        # 验证输入
        if not username or not email or not password:
            return jsonify({"success": False, "error": "用户名、邮箱和密码不能为空"}), 400

        if len(username) < 3:
            return jsonify({"success": False, "error": "用户名至少3个字符"}), 400

        if len(password) < 6:
            return jsonify({"success": False, "error": "密码至少6个字符"}), 400

        # 创建用户
        user = UserManager.create_user(username, email, password)

        if user:
            return jsonify({
                "success": True,
                "message": "注册成功",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "usertype": user.usertype
                }
            })
        else:
            return jsonify({"success": False, "error": "用户名或邮箱已存在"}), 409

    except Exception as e:
        logging.error(f"注册失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ========================== 历史记录API ==========================
@app.route("/api/history", methods=["GET"])
def get_histories():
    """获取用户历史记录"""
    try:
        user_id = request.args.get("user_id", type=int)
        limit = request.args.get("limit", 20, type=int)

        if not user_id:
            return jsonify({"success": False, "error": "用户ID不能为空"}), 400

        # 获取历史记录
        histories = HistoryManager.get_user_histories(user_id, limit)

        return jsonify({
            "success": True,
            "histories": [h.to_dict() for h in histories],
            "count": len(histories)
        })

    except Exception as e:
        logging.error(f"获取历史记录失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history/recent", methods=["GET"])
def get_recent_histories():
    """获取最近的历史记录（用于首页展示）"""
    try:
        user_id = request.args.get("user_id", type=int)
        limit = request.args.get("limit", 5, type=int)

        if not user_id:
            return jsonify({"success": False, "error": "用户ID不能为空"}), 400

        # 获取最近的历史记录
        histories = HistoryManager.get_recent_histories(user_id, limit)

        return jsonify({
            "success": True,
            "histories": histories,
            "count": len(histories)
        })

    except Exception as e:
        logging.error(f"获取最近历史记录失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history/<int:history_id>", methods=["GET"])
def get_history_detail(history_id):
    """获取历史记录详情"""
    try:
        history = HistoryManager.get_history_by_id(history_id)

        if history:
            return jsonify({
                "success": True,
                "history": history.to_dict()
            })
        else:
            return jsonify({"success": False, "error": "历史记录不存在"}), 404

    except Exception as e:
        logging.error(f"获取历史记录详情失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history", methods=["POST"])
def create_history():
    """创建历史记录"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        task_name = data.get("task_name", "").strip()
        description = data.get("description", "")
        input_image_url = data.get("input_image_url", "")
        heatmap_url = data.get("heatmap_url", "")
        route_url = data.get("route_url", "")
        report_url = data.get("report_url", "")
        task_status = data.get("task_status", "completed")
        task_time = data.get("task_time")

        # 验证输入
        if not user_id or not task_name:
            return jsonify({"success": False, "error": "用户ID和任务名称不能为空"}), 400

        # 解析任务时间
        from datetime import datetime
        task_time_obj = None
        if task_time:
            try:
                task_time_obj = datetime.fromisoformat(task_time.replace('Z', '+00:00'))
            except:
                task_time_obj = None

        # 创建历史记录
        history = HistoryManager.create_history(
            user_id=user_id,
            task_name=task_name,
            description=description,
            input_image_url=input_image_url,
            heatmap_url=heatmap_url,
            route_url=route_url,
            report_url=report_url,
            task_status=task_status,
            task_time=task_time_obj
        )

        if history:
            return jsonify({
                "success": True,
                "message": "历史记录创建成功",
                "history": history.to_dict()
            })
        else:
            return jsonify({"success": False, "error": "创建历史记录失败"}), 500

    except Exception as e:
        logging.error(f"创建历史记录失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history/<int:history_id>", methods=["DELETE"])
def delete_history(history_id):
    """删除历史记录"""
    try:
        success = HistoryManager.delete_history(history_id)

        if success:
            return jsonify({
                "success": True,
                "message": "历史记录删除成功"
            })
        else:
            return jsonify({"success": False, "error": "历史记录不存在"}), 404

    except Exception as e:
        logging.error(f"删除历史记录失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ========================== 用户统计 API ==========================
@app.route("/api/user/stats", methods=["GET"])
def get_user_stats():
    """获取用户存储统计信息"""
    try:
        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return jsonify({"success": False, "error": "用户ID不能为空"}), 400

        from database import get_db
        from models import History
        db = get_db()

        try:
            # 历史记录数量
            history_count = db.query(History).filter(
                History.user_id == user_id
            ).count()

            # 最近任务时间
            latest = db.query(History).filter(
                History.user_id == user_id
            ).order_by(History.created_at.desc()).first()

            latest_time = latest.created_at.strftime("%Y-%m-%d") if latest and latest.created_at else "暂无"

            # 估算存储占用 (历史记录数 × 平均每条 base64 图片约 500KB)
            estimated_mb = round(history_count * 0.5, 2)

            return jsonify({
                "success": True,
                "stats": {
                    "history_count": history_count,
                    "latest_time": latest_time,
                    "estimated_mb": estimated_mb,
                    "estimated_kb": int(estimated_mb * 1024)
                }
            })
        finally:
            db.close()

    except Exception as e:
        logging.error(f"获取用户统计失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # 确保static/output目录存在
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)