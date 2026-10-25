"""视频评估工具模块

提供两个小工具：
- extract_answer_from_response: 清洗 LLM 响应文本（去掉围栏、思考块等）
- eva_video_list: 扫描目录下的 mp4 文件，构造待评估列表
"""

import glob
import os
import re
from typing import Any, Dict, List, Optional, Union


def extract_answer_from_response(response: str) -> str:
    """从 LLM 响应中提取核心答案文本。

    依次处理：
    1. 去掉 <think>...</think> 推理块
    2. 去掉 ```json ... ``` / ``` ... ``` 等代码围栏
    3. 去掉首尾空白
    """
    if not response:
        return ""

    text = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL | re.IGNORECASE)

    fence_match = re.search(r"```(?:json|JSON)?\s*(.*?)```", text, flags=re.DOTALL)
    if fence_match:
        text = fence_match.group(1)

    return text.strip()


def eva_video_list(
    knowledge_points: Optional[Union[List[Dict[str, Any]], Dict[str, Any], str]] = None,
    base_dir: str = "",
) -> List[Dict[str, Any]]:
    """扫描 base_dir 下的 mp4 文件，构造 [{"path", "knowledge_point"}] 列表。

    Args:
        knowledge_points: 可选，支持三种形式：
            - str: 所有视频共用一个知识点
            - dict: {文件名(不含扩展名) : knowledge_point}
            - list: [{"name": <文件名前缀>, "knowledge_point": ...}, ...]
        base_dir: 视频所在目录

    Returns:
        [{"path": <绝对路径>, "knowledge_point": <字符串，可能为空>}, ...]
    """
    if not base_dir or not os.path.isdir(base_dir):
        print(f"警告：目录不存在或无效: {base_dir}")
        return []

    mp4_paths = sorted(glob.glob(os.path.join(base_dir, "*.mp4")))

    kp_lookup: Dict[str, str] = {}
    default_kp: str = ""

    if isinstance(knowledge_points, str):
        default_kp = knowledge_points
    elif isinstance(knowledge_points, dict):
        kp_lookup = {str(k): str(v) for k, v in knowledge_points.items()}
    elif isinstance(knowledge_points, list):
        for item in knowledge_points:
            if isinstance(item, dict) and "name" in item:
                kp_lookup[str(item["name"])] = str(item.get("knowledge_point", ""))

    video_list: List[Dict[str, Any]] = []
    for path in mp4_paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        kp = kp_lookup.get(stem, default_kp)
        video_list.append({"path": os.path.abspath(path), "knowledge_point": kp})

    return video_list
