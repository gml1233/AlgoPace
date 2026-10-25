"""Gemini 视频请求封装模块

通过 OpenAI 兼容协议代理（https://api.jiekou.ai/openai）调用 Gemini 多模态模型，
将本地 mp4 视频以 base64 data URL 形式内联到 chat.completions 的 content 里，
让 Gemini 直接进行原生视频理解（而非先抽帧）。
"""

import base64
import os
import time
from typing import Optional

from openai import OpenAI


API_CONFIG = {
    "base_url": "https://api.jiekou.ai/openai",
    "api_key": "sk_Sj24uPRx3d_Q3KU1SQ6ldLmG_w54xXhzZsHE31vFRos",
    "model": "gemini-3.1-pro-preview",
}

VIDEO_FIELD_NAME = "video_url"

DEFAULT_TIMEOUT = 300


def _encode_video_to_base64(video_path: str) -> str:
    """把本地 mp4 读成 base64 字符串。"""
    with open(video_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _build_video_content_block(video_path: str) -> dict:
    """构造多模态消息中的视频片段。

    使用 data URL 把 mp4 内联进去，字段名由 VIDEO_FIELD_NAME 控制，
    兼容大部分 Gemini OpenAI 兼容代理（video_url / input_video / video 任选其一）。
    """
    b64 = _encode_video_to_base64(video_path)
    data_url = f"data:video/mp4;base64,{b64}"
    return {
        "type": VIDEO_FIELD_NAME,
        VIDEO_FIELD_NAME: {"url": data_url},
    }


def request_gemini_with_video(
    prompt: str,
    video_path: str,
    log_id: Optional[str] = None,
    max_tokens: int = 8000,
    max_retries: int = 3,
    temperature: float = 0.3,
) -> str:
    """向 Gemini 发送 "文本 prompt + 本地视频" 的多模态请求。

    Args:
        prompt: 文本指令
        video_path: 本地 mp4 绝对路径
        log_id: 日志标记（仅用于打印）
        max_tokens: 返回的最大 token 数
        max_retries: 失败重试次数（指数退避）
        temperature: 采样温度

    Returns:
        模型返回的纯文本内容 (response.choices[0].message.content)
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    client = OpenAI(
        base_url=API_CONFIG["base_url"],
        api_key=API_CONFIG["api_key"],
        timeout=DEFAULT_TIMEOUT,
    )

    video_block = _build_video_content_block(video_path)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                video_block,
            ],
        }
    ]

    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            tag = f"[{log_id}] " if log_id else ""
            print(f"{tag}调用 Gemini (尝试 {attempt}/{max_retries}) - 视频: {os.path.basename(video_path)}")

            response = client.chat.completions.create(
                model=API_CONFIG["model"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("模型返回空内容")
            return content

        except Exception as e:
            last_error = e
            print(f"{tag if 'tag' in locals() else ''}请求失败: {e}")
            if attempt < max_retries:
                backoff = 2 ** attempt
                print(f"  {backoff}s 后重试...")
                time.sleep(backoff)

    raise RuntimeError(f"Gemini 视频请求在 {max_retries} 次重试后仍失败: {last_error}")
