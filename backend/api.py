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
import shutil
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
from datetime import datetime, timezone
import time
import secrets
import math
import urllib.request

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
# 【优化】per-session 分析器存储，支持多用户并发使用不同 API Key
_analyzers = {}
_analyzers_lock = threading.Lock()
assessor = TerrainAssessor()
planner = PathPlanner()

# 后端任务管理
TASKS = {}
TASK_LOCK = threading.Lock()

def _cleanup_expired_tasks():
    while True:
        time.sleep(300)
        now = datetime.now(timezone.utc)
        with TASK_LOCK:
            expired = []
            for tid, task in TASKS.items():
                try:
                    created = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                    if (now - created).total_seconds() > 3600 and task["status"] in ("completed", "failed"):
                        expired.append(tid)
                except (ValueError, KeyError):
                    expired.append(tid)
            for tid in expired:
                del TASKS[tid]

_cleanup_thread = threading.Thread(target=_cleanup_expired_tasks, daemon=True)
_cleanup_thread.start()


# ========================== 工具函数 ==========================
def _get_analyzer():
    """【优化】获取当前请求的 analyzer，支持多会话并发使用不同 API Key"""
    session_token = request.headers.get("X-Session-Token", "")
    if session_token and session_token in _analyzers:
        return _analyzers[session_token]
    with _analyzers_lock:
        if len(_analyzers) == 1:
            return next(iter(_analyzers.values()))
    return None


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
    """【优化】统一的起始区块解析函数，消除重复代码"""
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


def build_threat_df_lookup(df):
    """【优化】构建 (矩阵Y, 矩阵X) → 行数据 的快速查找字典"""
    lookup = {}
    for _, row in df.iterrows():
        key = (row.get("矩阵Y"), row.get("矩阵X"))
        if key not in lookup:
            lookup[key] = row
    return lookup


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
    now = datetime.now(timezone.utc)
    record = {
        "task_id": task_id,
        "task_type": task_type,
        "status": "pending",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
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
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
    return task


def get_task_record(task_id):
    with TASK_LOCK:
        return TASKS.get(task_id)


def _run_terrain_analysis(analyzer_local, assessor_local, planner_local, image_path, rows, cols, progress_callback=None):
    """【优化】共享的AI分析→威胁评估→关键点检测管道，消除get_heatmap与build_threat_result的重复代码"""
    terrain_data = analyzer_local.analyze_terrain(
        image_path=image_path, rows=rows, cols=cols, max_workers=2,
        progress_callback=progress_callback,
    )
    df, unique_x, unique_y = assessor_local.assess_terrain(terrain_data)
    threat_matrix = assessor_local.build_threat_matrix(df, unique_x, unique_y)
    keypoints = planner_local.detect_keypoints(threat_matrix)
    return terrain_data, df, unique_x, unique_y, threat_matrix, keypoints


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

    AI_PHASE_WEIGHT = 60

    def inline_progress_callback(completed, total, message):
        percent = int(round(completed / total * AI_PHASE_WEIGHT)) if total else 50
        update_task_record(
            task_id,
            status="running",
            progress=message,
            progress_percent=min(percent, AI_PHASE_WEIGHT),
        )

    # 【优化】使用共享管道函数
    _, df, _, _, threat_matrix, keypoints = _run_terrain_analysis(
        analyzer_local, assessor_local, planner_local, filename, rows, cols,
        progress_callback=inline_progress_callback,
    )

    logging.info(f"AI分析完成，识别到 {len(df)} 个地形要素")
    df_lookup = build_threat_df_lookup(df)

    patrol_points = []
    for idx, (row, col) in enumerate(keypoints):
        block_row = row
        block_col = col
        threat_score = float(threat_matrix[row, col])
        block_width = img_width // cols
        block_height = img_height // rows
        pixel_x = int(block_col * block_width + block_width // 2)
        pixel_y = int(block_row * block_height + block_height // 2)
        pixel_coords = [pixel_x, pixel_y]
        block_position = f"区块({int(block_row)}, {int(block_col)})"

        # 【优化】O(1) 字典查找替代 O(n) 遍历
        threat_reason = ""
        matched = df_lookup.get((row, col))
        if matched is not None:
            threat_reason = f"{matched.get('类型', '未知')}, {matched.get('坡度', '未知')}, {matched.get('威胁等级', '未知')}, {matched.get('备注', '')}"

        patrol_points.append(
            {
                "rank": idx + 1,
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
        "path_description": " -> ".join(
            f"[{int(p[0])},{int(p[1])}]" for p in path_coords
        ) if path_coords else "",
        "best_path_length": float(best_path_length),
        "heatmap_url": heatmap_url,
        "pathmap_url": pathmap_url,
        "upload_url": "/uploads/" + os.path.basename(filename),
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
    """初始化AI分析器 - 支持多会话"""
    try:
        data = request.get_json()
        api_key = data.get("api_key", "").strip()

        if not api_key:
            return jsonify({"success": False, "error": "API Key不能为空"}), 400

        new_analyzer = TerrainAnalyzer.create_analyzer(
            api_key=api_key,
            model="qwen3.6-plus",
            max_workers=2,
        )

        session_token = secrets.token_hex(16)
        with _analyzers_lock:
            _analyzers[session_token] = new_analyzer

        return jsonify({
            "success": True,
            "message": "API初始化成功",
            "session_token": session_token,
        })

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
    try:
        divide = request.form.get("divide", "").strip()
        map_file = request.files.get("map_picture")

        if not divide:
            return jsonify({"success": False, "error": "分块参数不能为空"}), 400
        if not map_file:
            return jsonify({"success": False, "error": "地图图片不能为空"}), 400

        analyzer_local = _get_analyzer()
        if analyzer_local is None:
            return jsonify(
                {"success": False, "error": "请先调用 /api/init 初始化API"}
            ), 400

        rows, cols = parse_divide(divide)

        image_path = save_upload_file(map_file)
        img_width, img_height = get_image_size(image_path)

        logging.info(f"收到图片: {map_file.filename}, 尺寸: {img_width}x{img_height}")
        logging.info(f"分块: {rows} x {cols}")

        # 【优化】使用共享管道函数
        logging.info("开始AI地形分析...")
        _, _, _, _, threat_matrix, keypoints = _run_terrain_analysis(
            analyzer_local, assessor, planner, image_path, rows, cols
        )

        logging.info(f"威胁矩阵构建完成: {threat_matrix.shape}")

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

        output_size = (img_width, img_height)
        fig = planner.get_pure_heatmap(threat_matrix, output_size)
        heatmap_url = save_output_image(fig, "heatmap")
        logging.info(f"纯热力图生成完成: {heatmap_url}")

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
    try:
        divide = request.form.get("divide", "").strip()
        map_file = request.files.get("map_picture")
        start_point_str = request.form.get("start_point", "0,0").strip()

        analyzer_local = _get_analyzer()

        if not divide:
            return jsonify({"success": False, "error": "分块参数不能为空"}), 400
        if not map_file:
            return jsonify({"success": False, "error": "地图图片不能为空"}), 400
        if analyzer_local is None:
            return jsonify({"success": False, "error": "请先调用 /api/init 初始化API"}), 400

        rows, cols = parse_divide(divide)

        start_point = parse_start_point(start_point_str, rows, cols)

        image_path = save_upload_file(map_file)
        img_width, img_height = get_image_size(image_path)

        logging.info(f"收到图片: {map_file.filename}, 尺寸: {img_width}x{img_height}")
        logging.info(f"分块: {rows} x {cols}")
        logging.info(f"起始区块: {start_point}")

        payload = {
            "analyzer": analyzer_local,
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

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """提供上传文件的访问"""
    return send_from_directory(UPLOAD_FOLDER, filename)

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
            <h2>3.5 地图区域分析 (新增)</h2>
            <code>POST /api/analyze_map_region</code>
            <p>输入经纬度边界，后端自动下载拼接卫星瓦片并分析</p>
            <pre>JSON:
{
    "north": 30.29, "south": 30.27,
    "east": 120.14, "west": 120.12,
    "zoom": 16,
    "divide": "4*4",
    "start_point": "1,1",
    "tile_source": "esri"
}
返回: {"task_id": "xxx", "status": "pending"}
</pre>
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


# ========================== 地图瓦片拼接与分析 ==========================

TILE_SIZE = 256
GROUND_RESOLUTION_CONST = 156543.03392


def _lat_lon_to_tile(lat, lon, zoom):
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return int(x), int(y)


def _tile_to_lat_lon(x, y, zoom):
    n = 2 ** zoom
    lon = (x + 0.5) / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 0.5) / n))))
    return lat, lon


def _pixel_to_lat_lon(px, py, x_start, y_start, zoom):
    n = 2 ** zoom
    total_px = n * TILE_SIZE
    lon = (x_start * TILE_SIZE + px) / total_px * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y_start * TILE_SIZE + py) / total_px))))
    return lat, lon


def _compute_scale(lat, zoom):
    return GROUND_RESOLUTION_CONST * math.cos(math.radians(lat)) / (2 ** zoom)


def _fetch_elevations(points):
    """Open-Meteo 免费高程 API, 分批请求 (每批最多100点)"""
    results = []
    for i in range(0, len(points), 100):
        batch = points[i:i + 100]
        lats = ",".join(f"{p[0]:.6f}" for p in batch)
        lons = ",".join(f"{p[1]:.6f}" for p in batch)
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}"
        req = urllib.request.Request(url, headers={"User-Agent": "TerraiNav/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            results.extend(data.get("elevation", []))
        except Exception as e:
            logging.error(f"高程API失败: {e}")
            return None
    return results


def _build_contour_image(x_start, y_start, zoom, cols, rows):
    """用DEM数据本地绘制彩色等高线地形图"""
    import numpy as np
    from scipy.ndimage import zoom as ndi_zoom

    total_w, total_h = cols * TILE_SIZE, rows * TILE_SIZE

    nx, ny = 20, 20
    pts = []
    for j in range(ny):
        for i in range(nx):
            px = (i + 0.5) * total_w / nx
            py = (j + 0.5) * total_h / ny
            pts.append(_pixel_to_lat_lon(px, py, x_start, y_start, zoom))

    elevs = _fetch_elevations(pts)
    if elevs is None or len(elevs) != len(pts):
        raise RuntimeError("无法获取采样高程")

    grid = np.array(elevs, dtype=float).reshape((ny, nx))
    big = ndi_zoom(grid, (256 / ny, 256 / nx), order=1)
    vmin = np.floor(grid.min() / 10) * 10
    vmax = np.ceil(grid.max() / 10) * 10

    rng = vmax - vmin
    if rng <= 30:
        interval = 5
    elif rng <= 100:
        interval = 10
    elif rng <= 300:
        interval = 25
    else:
        interval = 50
    levels = np.arange(vmin, vmax + interval / 2, interval)

    fig = plt.figure(figsize=(total_w / 100, total_h / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(big, cmap="terrain", origin="upper", vmin=vmin, vmax=vmax, interpolation="bicubic")
    cs = ax.contour(big, levels=levels, colors="k", linewidths=0.6, alpha=0.8)
    ax.clabel(cs, inline=True, fontsize=6, fmt="%d")
    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    return img


def _stitch_map_tiles(north, south, east, west, zoom, tile_source):
    """按经纬度边界下载/构造瓦片拼接图, 返回 PIL Image"""
    x_min, y_top = _lat_lon_to_tile(north, west, zoom)
    x_max, y_bot = _lat_lon_to_tile(south, east, zoom)
    tile_cols = x_max - x_min + 1
    tile_rows = y_bot - y_top + 1
    if tile_cols > 10 or tile_rows > 10:
        raise ValueError(f"区域过大 ({tile_cols}x{tile_rows} 瓦片), 请放大后重试")

    x_start, y_start = x_min, y_top

    if tile_source == "demcontour":
        return _build_contour_image(x_start, y_start, zoom, tile_cols, tile_rows), x_start, y_start

    canvas = Image.new("RGB", (tile_cols * TILE_SIZE, tile_rows * TILE_SIZE), (128, 128, 128))
    logging.info(f"下载瓦片: {tile_cols}x{tile_rows}, zoom={zoom}, source={tile_source}")

    for r in range(tile_rows):
        for c in range(tile_cols):
            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y_top + r}/{x_min + c}"
            req = urllib.request.Request(url, headers={"User-Agent": "TerraiNav/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                tile = Image.open(io.BytesIO(data)).convert("RGB")
                canvas.paste(tile, (c * TILE_SIZE, r * TILE_SIZE))
            except Exception as e:
                logging.warning(f"瓦片下载失败 ({x_min + c},{y_top + r}): {e}")
    return canvas, x_start, y_start


@app.route("/api/analyze_map_region", methods=["POST"])
def analyze_map_region():
    """
    新增接口: 通过地图经纬度边界启动分析 (无需上传文件)
    输入 JSON: { north, south, east, west, zoom, divide, start_point, tile_source }
    返回: { task_id }
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "error": "请提供JSON请求体"}), 400

        north = float(data.get("north", 0))
        south = float(data.get("south", 0))
        east = float(data.get("east", 0))
        west = float(data.get("west", 0))
        zoom = int(data.get("zoom", 16))
        divide = str(data.get("divide", "")).strip()
        start_point_str = str(data.get("start_point", "1,1")).strip()
        tile_source = str(data.get("tile_source", "esri")).strip()

        analyzer_local = _get_analyzer()
        if analyzer_local is None:
            return jsonify({"success": False, "error": "请先调用 /api/init 初始化API"}), 400
        if not divide:
            return jsonify({"success": False, "error": "分块参数不能为空"}), 400
        if north <= south or east <= west:
            return jsonify({"success": False, "error": "经纬度边界无效"}), 400

        rows, cols = parse_divide(divide)
        start_point = parse_start_point(start_point_str, rows, cols)

        logging.info(f"地图区域分析: {north:.4f},{west:.4f} - {south:.4f},{east:.4f}, zoom={zoom}")
        logging.info(f"瓦片源: {tile_source}, 分块: {rows}x{cols}, 起点: {start_point}")

        # 下载/构造拼接图
        stitched_img, tile_x_start, tile_y_start = _stitch_map_tiles(
            north, south, east, west, zoom, tile_source
        )
        img_width, img_height = stitched_img.size
        image_path = os.path.join(UPLOAD_FOLDER, f"map_{uuid.uuid4().hex[:8]}.png")
        stitched_img.save(image_path)
        logging.info(f"拼接图保存: {image_path}, 尺寸: {img_width}x{img_height}")

        payload = {
            "analyzer": analyzer_local,
            "assessor": assessor,
            "planner": planner,
            "image_path": image_path,
            "img_width": img_width,
            "img_height": img_height,
            "rows": rows,
            "cols": cols,
            "start_point": start_point,
        }
        task_id, _ = create_task_record("analyze_map_region", payload)
        worker = threading.Thread(target=process_threat_task, args=(task_id,), daemon=True)
        worker.start()

        return jsonify({"success": True, "task_id": task_id, "status": "pending"})

    except Exception as e:
        logging.error(f"地图区域分析失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ========================== 瓦片服务 ==========================

_tile_cache = {}
_tile_cache_max = 300


def _generate_contour_tile_bytes(x, y, z):
    """为单个瓦片生成等高线图 PNG (DEM采样 -> matplotlib等高线)"""
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.ndimage import zoom as ndi_zoom

    # 瓦片四角经纬度 (NW和SE)
    n = 2 ** z
    lat_n = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lon_w = x / n * 360.0 - 180.0
    lat_s = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    lon_e = (x + 1) / n * 360.0 - 180.0

    # 10x10 DEM采样点
    nx, ny = 10, 10
    pts = []
    for j in range(ny):
        for i in range(nx):
            lat = lat_n - (j + 0.5) * (lat_n - lat_s) / ny
            lon = lon_w + (i + 0.5) * (lon_e - lon_w) / nx
            pts.append((lat, lon))

    elevs = _fetch_elevations(pts)
    if elevs is None or len(elevs) < nx * ny:
        img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), (200, 220, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    grid = np.array(elevs, dtype=float).reshape((ny, nx))
    big = ndi_zoom(grid, (256 / ny, 256 / nx), order=1)
    vmin = np.floor(grid.min() / 10) * 10
    vmax = np.ceil(grid.max() / 10) * 10
    if vmax <= vmin:
        vmax = vmin + 10

    rng = vmax - vmin
    if rng <= 20:
        interval = 5
    elif rng <= 80:
        interval = 10
    elif rng <= 200:
        interval = 25
    else:
        interval = 50
    levels = np.arange(vmin, vmax + interval / 2, interval)

    fig = plt.figure(figsize=(2.56, 2.56), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(big, cmap="terrain", origin="upper", vmin=vmin, vmax=vmax, interpolation="bicubic")
    cs = ax.contour(big, levels=levels, colors="k", linewidths=0.4, alpha=0.7)
    ax.clabel(cs, inline=True, fontsize=5, fmt="%d")
    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


@app.route("/api/map_overlay", methods=["POST"])
def map_overlay():
    """生成等高线叠加图 (透明背景 + 等高线 + 注记), 用于地图覆盖层"""
    try:
        import matplotlib.pyplot as plt
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "error": "缺少请求体"}), 400

        north = float(data["north"])
        south = float(data["south"])
        east = float(data["east"])
        west = float(data["west"])
        zoom = int(data.get("zoom", 16))

        import numpy as np
        from scipy.ndimage import zoom as ndi_zoom

        nx, ny = 20, 20
        pts = []
        for j in range(ny):
            for i in range(nx):
                lat = north - (j + 0.5) * (north - south) / ny
                lon = west + (i + 0.5) * (east - west) / nx
                pts.append((lat, lon))

        elevs = _fetch_elevations(pts)
        if elevs is None or len(elevs) < nx * ny:
            return jsonify({"success": False, "error": "无法获取高程数据"}), 500

        grid = np.array(elevs, dtype=float).reshape((ny, nx))
        big = ndi_zoom(grid, (256 / ny, 256 / nx), order=1)
        rng = grid.max() - grid.min()
        if rng <= 30: interval = 5
        elif rng <= 100: interval = 10
        elif rng <= 300: interval = 25
        else: interval = 50
        levels = np.arange(np.floor(grid.min() / 10) * 10, grid.max() + interval / 2, interval)

        x_min, y_top = _lat_lon_to_tile(north, west, zoom)
        x_max, y_bot = _lat_lon_to_tile(south, east, zoom)
        canvas_w = (x_max - x_min + 1) * TILE_SIZE
        canvas_h = (y_bot - y_top + 1) * TILE_SIZE
        dpi = 100
        fig = plt.figure(figsize=(canvas_w / dpi, canvas_h / dpi), dpi=dpi)
        fig.patch.set_alpha(0)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_facecolor((0, 0, 0, 0))

        ax.imshow(big, cmap="terrain", alpha=0.35, origin="upper",
                  vmin=np.floor(grid.min() / 10) * 10, vmax=np.ceil(grid.max() / 10) * 10,
                  extent=[0, canvas_w, canvas_h, 0], interpolation="bicubic")
        cs = ax.contour(np.linspace(0, canvas_w, big.shape[1]),
                        np.linspace(0, canvas_h, big.shape[0]),
                        big, levels=levels, colors="#1a1a2e", linewidths=1.2, alpha=0.85)
        ax.clabel(cs, inline=True, fontsize=7, fmt="%d", colors="#1a1a2e")
        ax.axis("off")
        ax.set_xlim(0, canvas_w)
        ax.set_ylim(canvas_h, 0)

        buf = io.BytesIO()
        fig.savefig(buf, format="PNG", dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        buf.seek(0)

        fname = f"overlay_{uuid.uuid4().hex[:8]}.png"
        fpath = os.path.join(OUTPUT_FOLDER, fname)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        with open(fpath, "wb") as f:
            f.write(buf.getvalue())

        url = url_for("static", filename=f"output/{fname}", _external=False)
        return jsonify({
            "success": True,
            "image_url": url,
            "bounds": {"north": north, "south": south, "east": east, "west": west},
        })
    except Exception as e:
        logging.error(f"等高线叠加图生成失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tile/<source>/<int:z>/<int:x>/<int:y>.png", methods=["GET"])
def serve_tile(source, z, x, y):
    """统一瓦片服务: esri=代理卫星图, demcontour=本地生成等高线"""
    cache_key = f"{source}/{z}/{x}/{y}"

    if cache_key in _tile_cache:
        return _tile_cache[cache_key], 200, {"Content-Type": "image/png"}

    if source == "demcontour":
        try:
            png_data = _generate_contour_tile_bytes(x, y, z)
        except Exception as e:
            logging.error(f"等高线瓦片生成失败: {e}")
            png_data = b""
    else:
        # esri 或任何其他源 -> 代理 Esri 卫星
        url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        req = urllib.request.Request(url, headers={"User-Agent": "TerraiNav/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                png_data = resp.read()
        except Exception as e:
            logging.warning(f"瓦片代理失败 ({z}/{x}/{y}): {e}")
            png_data = b""

    if len(_tile_cache) >= _tile_cache_max:
        # 清理一半缓存
        for k in list(_tile_cache.keys())[:_tile_cache_max // 2]:
            del _tile_cache[k]

    _tile_cache[cache_key] = png_data
    return png_data, 200, {"Content-Type": "image/png"}


if __name__ == "__main__":
    # 确保static/output目录存在
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)