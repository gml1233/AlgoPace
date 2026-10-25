# coding=utf-8
"""
按算法 id 拉取制作视频所需的素材：
  - Python 代码       （getCodeByAlgorithmId）
  - 算法步骤、算法分析  （getQuestionByAlgorithmId，只取这两条，其余忽略）

用法：
    .venv/bin/python fetch_algo.py 139            # 打印到屏幕
    .venv/bin/python fetch_algo.py 139 -o 139.md  # 同时存成 markdown

只依赖标准库（urllib），不需要装额外包。
"""
import sys
import json
import argparse
import urllib.request
from pathlib import Path

BASE = "https://dancing.zksys.cn/api/algorithm"
CODE_URL = BASE + "/getCodeByAlgorithmId/{id}"
QUES_URL = BASE + "/getQuestionByAlgorithmId/{id}"


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "AlgoT2V/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode("utf-8"))
    if payload.get("status") != 200:
        raise RuntimeError("接口返回异常：%s" % payload.get("msg"))
    return payload.get("data", [])


def fetch_python(algo_id):
    """从代码接口里挑出 Python 实现，统一换行符。"""
    for item in _get(CODE_URL.format(id=algo_id)):
        if (item.get("code_type") or "").strip().lower() in ("python", "python3", "py"):
            return item["code"].replace("\r\n", "\n").replace("\r", "\n")
    return None


def fetch_steps_and_analysis(algo_id):
    """只取『算法步骤』和『算法分析』两条，返回 (steps, analysis) 文本。"""
    steps = analysis = None
    for item in _get(QUES_URL.format(id=algo_id)):
        title = item.get("title", "")
        ans = (item.get("ans") or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if title.endswith("算法步骤"):
            steps = ans
        elif title.endswith("算法分析"):
            analysis = ans
    return steps, analysis


def build_report(algo_id):
    python_code = fetch_python(algo_id)
    fallback = False
    if python_code is None and str(algo_id) in ("87", "109"):
        # 这两个算法的接口只有 C++；保留来源说明，不能冒充接口原始 Python 代码。
        python_code = (Path(__file__).resolve().parent / "python_fallbacks" / f"{algo_id}.py").read_text(encoding="utf-8")
        fallback = True
    steps, analysis = fetch_steps_and_analysis(algo_id)

    out = []
    out.append("# 算法 id=%s 制作素材\n" % algo_id)

    out.append("## 算法步骤\n")
    out.append((steps or "（接口未返回算法步骤）") + "\n")

    out.append("## 算法分析\n")
    out.append((analysis or "（接口未返回算法分析）") + "\n")

    out.append("## Python 代码\n")
    if python_code:
        if fallback:
            out.append("注：接口未提供 Python 代码；以下为根据该算法的 C++ 代码改写的 Python 实现。\n")
        out.append("```python\n" + python_code.strip() + "\n```\n")
    else:
        out.append("（接口未返回 Python 代码）\n")

    return "\n".join(out)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="按算法 id 拉取 Python 代码 + 算法步骤 + 算法分析")
    ap.add_argument("id", help="算法 id，例如 139")
    ap.add_argument("-o", "--output", help="可选：把结果写入该 markdown 文件")
    args = ap.parse_args()

    try:
        report = build_report(args.id)
    except Exception as e:
        print("拉取失败：%s" % e, file=sys.stderr)
        sys.exit(1)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print("\n已写入：%s" % args.output, file=sys.stderr)
    print(report)


if __name__ == "__main__":
    main()
