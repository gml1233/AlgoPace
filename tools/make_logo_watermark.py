#!/usr/bin/env python
# coding=utf-8
"""把白底 logo 处理成「透明背景 + 调浅」的水印 PNG，用于叠加到视频里。

做了三件事：
  1. 去白底：按「白度」软抠图（边缘平滑、保留抗锯齿），白色 → 全透明，彩色 → 不透明。
  2. 调浅：可把颜色向白色混合（--lighten），并整体降低不透明度（--opacity）。
  3. 自动裁掉四周全透明的空白，输出尺寸紧凑、便于定位的 PNG（带 alpha 通道）。

用法示例：
    # 默认：去白底 + 不透明度 0.5（适合做淡水印），保持原色
    python tools/make_logo_watermark.py logo.jpg logo_wm.png

    # 更淡、更浅（颜色向白混 35%，整体不透明度 0.4）
    python tools/make_logo_watermark.py logo.jpg logo_wm.png --lighten 0.35 --opacity 0.4

    # 想要清晰不透明的透明底版本（只去白底，不调浅）
    python tools/make_logo_watermark.py logo.jpg logo_clear.png --opacity 1.0
"""
import argparse

import numpy as np
from PIL import Image


def make_watermark(
    src_path: str,
    out_path: str,
    opacity: float = 0.5,
    lighten: float = 0.0,
    white_hi: float = 252.0,
    white_lo: float = 205.0,
    trim: bool = True,
) -> None:
    """生成透明背景的水印 PNG。

    Args:
        src_path: 输入图片（白底 logo），jpg/png 均可。
        out_path: 输出 PNG 路径（带透明通道）。
        opacity:  整体不透明度 0~1，越小越淡。
        lighten:  颜色向白色混合比例 0~1，越大越浅（0 表示保持原色）。
        white_hi: 亮度 >= 该值的像素视为纯白 → 完全透明。
        white_lo: 亮度 <= 该值的像素视为纯前景 → 完全不透明。
                  两者之间线性过渡，保证边缘平滑、抗锯齿不发灰。
        trim:     是否自动裁掉四周全透明的空白。
    """
    img = Image.open(src_path).convert("RGBA")
    arr = np.array(img).astype(np.float32)
    r, g, b, a0 = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

    # —— 1) 去白底：用各通道最小值衡量「白度」。白色三通道都高 → minc 大；
    #     彩色/深色至少有一个通道低 → minc 小。据此把白色映射为透明。
    minc = np.minimum(np.minimum(r, g), b)
    alpha = np.clip((white_hi - minc) / max(white_hi - white_lo, 1e-6), 0.0, 1.0) * 255.0
    alpha = np.minimum(alpha, a0)  # 尊重原图已有的透明信息

    # —— 2) 调浅：颜色向白色混合
    if lighten > 0:
        r = r + (255.0 - r) * lighten
        g = g + (255.0 - g) * lighten
        b = b + (255.0 - b) * lighten

    # —— 3) 整体不透明度
    alpha = alpha * float(opacity)

    out = np.stack([r, g, b, alpha], axis=-1).clip(0, 255).astype(np.uint8)

    # —— 4) 自动裁掉四周全透明区域
    if trim:
        mask = out[..., 3] > 3
        if mask.any():
            ys, xs = np.where(mask)
            y0, y1 = ys.min(), ys.max() + 1
            x0, x1 = xs.min(), xs.max() + 1
            out = out[y0:y1, x0:x1]

    Image.fromarray(out, "RGBA").save(out_path)
    h, w = out.shape[:2]
    print(f"已生成水印: {out_path}  ({w}x{h}, opacity={opacity}, lighten={lighten})")


def main() -> None:
    p = argparse.ArgumentParser(description="把白底 logo 处理成透明背景 + 调浅的水印 PNG")
    p.add_argument("src", help="输入图片（白底 logo）")
    p.add_argument("out", help="输出 PNG 路径")
    p.add_argument("--opacity", type=float, default=0.5, help="整体不透明度 0~1（默认 0.5）")
    p.add_argument("--lighten", type=float, default=0.0, help="颜色向白混合比例 0~1（默认 0，不调浅）")
    p.add_argument("--white-hi", type=float, default=252.0, help="纯白阈值（默认 252）")
    p.add_argument("--white-lo", type=float, default=205.0, help="纯前景阈值（默认 205）")
    p.add_argument("--no-trim", action="store_true", help="不自动裁切空白边")
    args = p.parse_args()

    make_watermark(
        args.src, args.out,
        opacity=args.opacity, lighten=args.lighten,
        white_hi=args.white_hi, white_lo=args.white_lo,
        trim=not args.no_trim,
    )


if __name__ == "__main__":
    main()
