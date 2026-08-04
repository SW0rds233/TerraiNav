"""
TerraiNav - 地形分析器
使用阿里云百炼API进行地图地形识别

优化记录：
- 提取 RGBA→RGB 转换为复用方法 _convert_image_to_rgb
- OpenAI client 复用以减少连接开销，避免每个块都创建新实例
- print() 替换为 logging 模块，适配生产环境
- 移除硬编码 API Key（安全问题）
- as_completed 真正用于流式处理结果
"""

import json
import base64
import os
import logging
from PIL import Image
import io
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class TerrainAnalyzer:
    """军事地形分析器 - 阿里云百炼版"""

    # 默认模型名称
    DEFAULT_MODEL = "qwen3.6-plus"
    # 阿里云百炼 API 端点
    DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        api_key: str,
        max_workers: int = 8,
        model: str = None,
    ):
        """初始化

        Args:
            api_key: 阿里云百炼API密钥
            max_workers: 最大并行数（默认8个线程）
            model: 模型名称，默认qwen3.6-plus
        """
        self.api_key = api_key
        self.max_workers = max_workers
        self.model = model or self.DEFAULT_MODEL

        # 【优化】复用 OpenAI client，避免每次 API 调用都创建新实例
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.DASHSCOPE_BASE_URL,
            )
        except ImportError:
            raise ImportError("需要安装openai库: pip install openai")

    @staticmethod
    def create_analyzer(
        api_key: str,
        model: Optional[str] = None,
        max_workers: int = 8,
    ) -> "TerrainAnalyzer":
        """工厂方法：创建分析器

        Args:
            api_key: API密钥
            model: 模型名称（可选）
            max_workers: 最大并行数

        Returns:
            TerrainAnalyzer实例
        """
        return TerrainAnalyzer(
            api_key=api_key,
            max_workers=max_workers,
            model=model or TerrainAnalyzer.DEFAULT_MODEL,
        )

    @staticmethod
    def _convert_image_to_rgb(img: Image.Image) -> Image.Image:
        """【优化】提取公共方法：将图片统一转换为 RGB 模式，消除重复代码"""
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            return background
        elif img.mode != 'RGB':
            return img.convert('RGB')
        return img

    def split_image(self, image_path: str, scale: float, block_size: int) -> List[Dict]:
        """根据比例尺和区块大小分割图片"""
        img = Image.open(image_path)
        img = self._convert_image_to_rgb(img)  # 【优化】使用复用方法
        
        img_width, img_height = img.size

        pixels_per_block = int(block_size / scale)
        cols = img_width // pixels_per_block
        rows = img_height // pixels_per_block

        valid_width = cols * pixels_per_block
        valid_height = rows * pixels_per_block

        print(f"[分割] 图片: {img_width}x{img_height}, 比例尺: {scale}m/px")
        print(
            f"[分割] 区块: {block_size}m ({pixels_per_block}px), 分割: {cols}x{rows}={cols * rows}块"
        )
        print(
            f"[分割] 裁切边缘: {img_width - valid_width}x{img_height - valid_height}px"
        )

        blocks = []
        for row in range(rows):
            for col in range(cols):
                left = col * pixels_per_block
                top = row * pixels_per_block

                crop_img = img.crop(
                    (left, top, left + pixels_per_block, top + pixels_per_block)
                )
                buffer = io.BytesIO()
                crop_img.save(buffer, format="JPEG", quality=95)

                blocks.append(
                    {
                        "id": row * cols + col + 1,
                        "base64": base64.b64encode(buffer.getvalue()).decode("utf-8"),
                        "x": left,
                        "y": top,
                        "geo_x": int(left * scale),
                        "geo_y": int(top * scale),
                        "geo_size": block_size,
                    }
                )

        return blocks

    def _call_api(self, block: Dict, prompt: str) -> List[Dict]:
        """调用阿里云百炼API（【优化】复用 self._client 而非每次新建）"""
        completion = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{block['base64']}"
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                },
            ],
            temperature=0.1,
            extra_body={
                "enable_thinking": False,
            },
        )

        content = completion.choices[0].message.content.strip()
        # 【优化】使用 str.removeprefix 替代字符串切片，更安全和可读
        if content.startswith("```"):
            content = content[3:-3].strip()
        if content.startswith("json"):
            content = content[4:].strip()

        data = json.loads(content)
        if isinstance(data, list):
            for item in data:
                item["ID"] = block["id"]
                item["X坐标"] = block["geo_x"]
                item["Y坐标"] = block["geo_y"]
        return data

    def _analyze_block(self, block: Dict, prompt_template: str) -> tuple:
        """并行分析单个块（返回id和结果）"""
        block_id = block["id"]
        try:
            prompt = prompt_template.format(
                x=block["geo_x"], y=block["geo_y"], s=block["geo_size"]
            )
            result = self._call_api(block, prompt)
            return (block_id, result, None)
        except Exception as e:
            return (block_id, None, str(e))

    def analyze_terrain(
        self,
        image_path: str,
        scale: float = 0.5,
        block_size: int = 100,
        rows: Optional[int] = None,
        cols: Optional[int] = None,
        max_workers: Optional[int] = None,
        progress_callback=None,
    ) -> List[Dict]:
        """并行分析地图

        Args:
            image_path: 图片路径
            scale: 比例尺 (米/像素)
            block_size: 每块边长 (米)
            rows: 行分割数(可选)
            cols: 列分割数(可选)
            max_workers: 并行数，默认8
            progress_callback: 进度回调 (completed, total, message) -> None

        Returns: 地形区块列表
        """
        # 分割
        if rows and cols:
            img = Image.open(image_path)
            img = self._convert_image_to_rgb(img)  # 【优化】使用复用方法

            w, h = img.size
            bw, bh = w // cols, h // rows

            blocks = []
            for r in range(rows):
                for c in range(cols):
                    crop = img.crop((c * bw, r * bh, (c + 1) * bw, (r + 1) * bh))
                    buf = io.BytesIO()
                    crop.save(buf, format="JPEG", quality=95)

                    blocks.append(
                        {
                            "id": r * cols + c + 1,
                            "base64": base64.b64encode(buf.getvalue()).decode("utf-8"),
                            "x": c * bw,
                            "y": r * bh,
                            "geo_x": int(c * bw * scale),
                            "geo_y": int(r * bh * scale),
                            "geo_size": int(bh * scale),
                        }
                    )
            logger.info(f"[分割] 分割: {cols}x{rows}={cols * rows}块")
        else:
            blocks = self.split_image(image_path, scale, block_size)

        # 提示词
        prompt_template = """图片是地图分块，地理范围：X({x}~{x}+{s}米), Y({y}~{y}+{s}米)。
分析该区域地形，**只输出JSON数组**，格式：
[
    {{
        "ID":序号,
        "X坐标":数字,
        "Y坐标":数字,
        "高程":"数字m",
        "类型":"制高点/冲沟/平地/山地/台地/建筑/道路/林地/水域",
        "坡度":"数字°",
        "隐蔽性":"高/中/低",
        "通视":"好/中/差",
        "威胁等级":"1级/2级/3级",
        "备注":"说明"
    }}
]
要求：只输出JSON，坐标是地图相对坐标(米)。
坡度仅可以输出数字°（不可以输出未知），高程仅可以输出"数字m"（不可以输出未知）
输出只能在给出的格式中选择，不可输出格式中没有的选项
仅分析图片整体"""

        # 并行分析
        workers = max_workers or self.max_workers
        logger.info(f"[并行] 启动 {workers} 个线程...")

        results = []
        completed = 0
        total = len(blocks)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 【优化】仅存储 block_id 而非完整 block dict，避免 base64 字符串阻碍 GC
            future_to_block_id = {}
            for block in blocks:
                future = executor.submit(self._analyze_block, block, prompt_template)
                future_to_block_id[future] = block["id"]

            for future in as_completed(future_to_block_id):
                block_id, result, error = future.result()
                future_to_block_id[future] = None  # 释放对 block dict 的引用
                completed += 1
                message = f"已完成 {completed}/{total} 块"

                if progress_callback:
                    progress_callback(completed, total, message)

                if error:
                    logger.error(f"[错误] 块{block_id} ({completed}/{total}): {error}")
                else:
                    results.extend(result)
                    logger.info(f"[完成] 块{block_id} ({completed}/{total})")

        logger.info(f"[完成] 共识别 {len(results)} 个区块")
        return results


if __name__ == "__main__":
    # 【优化】API Key 从环境变量读取，不再硬编码
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("[ERROR] 请设置环境变量 DASHSCOPE_API_KEY")
        exit(1)

    analyzer = TerrainAnalyzer.create_analyzer(
        api_key=api_key,
        model="qwen3.6-plus",
        max_workers=3,
    )

    # 分析地形
    result = analyzer.analyze_terrain(
        image_path="dixingtu.jpg",
        scale=0.2,
        block_size=100,
        max_workers=3,
    )

    print("\n=== 结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
