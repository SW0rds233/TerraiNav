# -*- coding: utf-8 -*-
"""
TerraiNav 开发环境一键启动脚本

用法:
    python start_dev.py

功能:
    1. 启动 Flask 后端 (端口 5000)
    2. 启动 Vite 前端 (端口 5173)
    3. Ctrl+C 关闭所有服务
"""

import subprocess
import sys
import os
import time
import signal
import platform
import socket
import threading

# ========== 配置 ==========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
FRONTEND_DIR = os.path.join(SCRIPT_DIR, "frontend")

BACKEND_PORT = int(os.getenv("PORT", "5000"))
FRONTEND_PORT = 5173

# 进程引用和停止标志
backend_proc = None
frontend_proc = None
shutdown_flag = threading.Event()


def check_port(port):
    """检查端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.bind(("127.0.0.1", port))
            return False
    except OSError:
        return True


def kill_process_on_port(port):
    """杀掉占用指定端口的进程 (Windows)"""
    if platform.system() != "Windows":
        return
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in line:
                    pid = parts[-1]
                    subprocess.run(
                        f"taskkill /F /PID {pid}",
                        shell=True,
                        capture_output=True,
                    )
                    print(f"  [清理] 端口 {port} 已释放 (PID {pid})")
    except Exception:
        pass


def stream_reader(stream, label):
    """在线程中读取子进程输出，逐行打印"""
    try:
        for line in iter(stream.readline, ""):
            if shutdown_flag.is_set():
                break
            line = line.strip()
            if line:
                print(f"  {label} {line}")
    except (ValueError, OSError):
        pass  # 流已关闭


def start_backend():
    """启动 Flask 后端"""
    global backend_proc

    if check_port(BACKEND_PORT):
        print(f"  [!] 端口 {BACKEND_PORT} 已被占用, 尝试释放...")
        kill_process_on_port(BACKEND_PORT)
        time.sleep(1)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # 禁止生成 .pyc 缓存，避免旧代码残留

    backend_proc = subprocess.Popen(
        [sys.executable, "-B", "api.py"],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    print(f"  [OK] 后端进程已启动 (PID: {backend_proc.pid})")

    # 启动输出读取线程
    t = threading.Thread(
        target=stream_reader,
        args=(backend_proc.stdout, "[后端]"),
        daemon=True,
    )
    t.start()


def start_frontend():
    """启动 Vite 前端"""
    global frontend_proc

    if check_port(FRONTEND_PORT):
        print(f"  [!] 端口 {FRONTEND_PORT} 已被占用, 尝试释放...")
        kill_process_on_port(FRONTEND_PORT)
        time.sleep(1)

    env = os.environ.copy()
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"

    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    print(f"  [OK] 前端进程已启动 (PID: {frontend_proc.pid})")

    # 启动输出读取线程
    t = threading.Thread(
        target=stream_reader,
        args=(frontend_proc.stdout, "[前端]"),
        daemon=True,
    )
    t.start()


def cleanup():
    """关闭所有服务"""
    shutdown_flag.set()
    if backend_proc or frontend_proc:
        print("\n正在关闭服务...")
    for name, proc in [("后端", backend_proc), ("前端", frontend_proc)]:
        if proc and proc.poll() is None:
            print(f"  关闭{name}...", end=" ", flush=True)
            if platform.system() == "Windows":
                proc.terminate()
            else:
                proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=5)
                print("OK")
            except subprocess.TimeoutExpired:
                proc.kill()
                print("强制终止")
    print("所有服务已关闭")
    sys.exit(0)


def signal_handler(signum, frame):
    """Ctrl+C / SIGTERM 处理"""
    cleanup()


def main():
    print()
    print("=" * 60)
    print("       TerraiNav 开发环境一键启动")
    print("=" * 60)
    print()

    # 检查前提
    print("[*] 检查环境...")
    print(f"    Python: {sys.version.split()[0]}")
    print(f"    后端目录: {BACKEND_DIR}")
    print(f"    前端目录: {FRONTEND_DIR}")
    print()

    # 检查后端依赖
    try:
        import flask
        import numpy
        import PIL
        import pandas
        import scipy
        import openai
    except ImportError as e:
        print(f"  [X] 缺少 Python 依赖: {e}")
        print("  请运行: pip install -r backend/requirements.txt")
        sys.exit(1)

    # 启动后端
    print(f"[*] 启动后端服务 (端口 {BACKEND_PORT})...")
    start_backend()

    # 稍等让后端先启动
    time.sleep(1)

    # 启动前端
    print(f"[*] 启动前端服务 (端口 {FRONTEND_PORT})...")
    start_frontend()

    print()
    print("=" * 60)
    print("       服务启动完成!")
    print("=" * 60)
    print()
    print(f"   前端地址:  http://localhost:{FRONTEND_PORT}")
    print(f"   后端 API:  http://localhost:{BACKEND_PORT}")
    print(f"   API 文档:  http://localhost:{BACKEND_PORT}/")
    print()
    print("   测试账户:  admin / 123456")
    print()
    print("   按 Ctrl+C 关闭所有服务")
    print()

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 主线程保持运行，等待 Ctrl+C 或所有子进程退出
    try:
        while True:
            # 检查子进程是否还活着
            if backend_proc and backend_proc.poll() is not None:
                print(f"\n  [X] 后端进程异常退出 (code: {backend_proc.returncode})")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print(f"\n  [X] 前端进程异常退出 (code: {frontend_proc.returncode})")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == "__main__":
    main()
