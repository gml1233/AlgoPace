"""用 AIgo Conda 环境批量渲染 Manim 动画。

示例（在仓库根目录运行）：
    python render_aigo.py --source codetest/python版 --output D:/videos
    python render_aigo.py --source codetest/07_排序 --output D:/videos -q l
    python render_aigo.py --source codetest --output D:/videos --dry-run

视频保存在输出目录下对应的章节目录中。Manim 会继续按
videos/<脚本名>/<分辨率>/<场景名>.mp4 建立子目录。
"""

import argparse
import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent


def scene_files(source: Path):
    """只选取定义了 Manim 场景的脚本，跳过工具和测试文件。"""
    candidates = [source] if source.is_file() else sorted(source.rglob("*.py"))
    for path in candidates:
        if path.suffix.lower() != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as exc:
            print(f"无法解析 {path}: {exc}", file=sys.stderr)
            raise
        if any(
            isinstance(node, ast.ClassDef)
            and any(isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and member.name == "construct" for member in node.body)
            for node in tree.body
        ):
            yield path


def main(argv=None):
    parser = argparse.ArgumentParser(description="在 AIgo 环境中批量渲染 Manim 视频")
    parser.add_argument("--source", required=True, type=Path, help="动画 Python 文件或代码目录（递归查找）")
    parser.add_argument("--output", required=True, type=Path, help="视频输出目录")
    parser.add_argument("-q", "--quality", choices=("l", "m", "h", "p", "k"), default="m",
                        help="Manim 画质，默认 m（720p/30fps）")
    parser.add_argument("--dry-run", action="store_true", help="仅列出将执行的命令，不渲染")
    args = parser.parse_args(argv)

    source = args.source.resolve()
    output = args.output.resolve()
    if not source.exists() or (source.is_file() and source.suffix.lower() != ".py"):
        parser.error(f"代码目录或 Python 文件不存在：{source}")
    if output == source or (source.is_dir() and source in output.parents):
        parser.error("输出目录不能放在代码目录中；请使用独立的视频目录")

    try:
        files = list(scene_files(source))
    except (OSError, SyntaxError, UnicodeError):
        return 1
    if not files:
        print(f"未找到定义 construct() 的 Manim 场景脚本：{source}", file=sys.stderr)
        return 1

    conda = shutil.which("conda")
    if not conda and not args.dry_run:
        print("找不到 conda 命令，请先安装 Conda 并将其加入 PATH。", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (
        str(PROJECT_ROOT), str(source if source.is_dir() else source.parent),
        env.get("PYTHONPATH"),
    )))
    if not args.dry_run:
        output.mkdir(parents=True, exist_ok=True)

    failures = []
    for number, path in enumerate(files, 1):
        # 保留代码目录中的章节结构；指定单个文件时直接写入输出目录。
        relative_parent = path.parent.relative_to(source) if source.is_dir() else Path()
        media_dir = output / relative_parent
        cmd = [conda or "conda", "run", "--no-capture-output", "-n", "AIgo",
               "python", "-m", "manim", "render", "-c", str(PROJECT_ROOT / "manim.cfg"),
               "--media_dir", str(media_dir), "-q", args.quality, "-a", str(path)]
        print(f"[{number}/{len(files)}] {path}", flush=True)
        if args.dry_run:
            print(subprocess.list2cmdline(cmd))
            continue
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, check=False)
        if result.returncode != 0:
            failures.append(path)
            print(f"渲染失败（退出码 {result.returncode}）：{path}", file=sys.stderr, flush=True)

    if args.dry_run:
        print(f"计划渲染 {len(files)} 个脚本。")
    else:
        print(f"完成：成功 {len(files) - len(failures)}，失败 {len(failures)}。视频目录：{output}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
