"""AlgoT2V 消融实验驱动脚本（论文 4.5 节 Table 4.5 复现入口）

对每个消融模式（none / no_skills / no_multi_agent / no_vlm_review /
no_code_repair）与每个测试概念组合，依次运行 Pipeline.run，记录：

    Success@0  渲染流水线一次成功率（全部场景都未走 Tier1/2/3 修复即成功）
    Success@3  允许最多 3 次外部重试后的成功率（每次失败重新跑 pipeline）
    VQS        对成功视频调用 eval.VideoEvaluator 得到的 overall_score
    Time       每个 concept 的平均墙钟耗时（分钟）
    Token      每个 concept 的平均总 token 消耗（K）

用法示例：
    # 默认 5 个概念 × 5 个模式 × 1 个 trial
    python eval/ablation_runner.py

    # 指定概念清单 + 多次试验
    python eval/ablation_runner.py --concepts 冒泡排序 二分查找 二叉树遍历 --trials 3

    # 仅复现某几个模式
    python eval/ablation_runner.py --modes none no_skills

    # 跳过 VQS 评估（节省 Gemini 多模态 token）
    python eval/ablation_runner.py --skip-vqs

输出：eval/ablation_results/ 下落盘 raw_runs.jsonl 与 summary.md。
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings  # noqa: E402

logger = logging.getLogger("AblationRunner")

DEFAULT_CONCEPTS = [
    "冒泡排序算法",
    "快速排序算法",
    "二分查找算法",
    "二叉树前序遍历",
    "广度优先搜索",
]

DEFAULT_MODES = [
    "none",
    "no_skills",
    "no_multi_agent",
    "no_vlm_review",
    "no_code_repair",
]


@dataclass
class TrialRecord:
    mode: str
    concept: str
    trial_index: int
    pipeline_status: str
    success_at_0: bool
    success_at_3: bool
    retries_used: int
    elapsed_sec: float
    total_tokens: int
    final_video_path: Optional[str] = None
    vqs_overall: Optional[float] = None
    vqs_breakdown: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    metadata_path: Optional[str] = None


def _scene_success_at_zero(meta: Dict[str, Any]) -> bool:
    """判断本次运行是否属于"未经任何修复即成功"。

    使用 metadata.steps_completed 与 animation_stats.scenes_rendered/scenes_planned
    两条信号：当全部场景一次过且 video_composition 成功时计为 success@0。
    若 render_results 中任何一条出现 tier1/tier2/fallback_stub 前缀的 error_message，
    说明触发了修复链，则视为非一次过。
    """
    if meta.get("pipeline_status") != "success":
        return False
    anim_stats = meta.get("animation_stats") or {}
    if anim_stats.get("scenes_planned") != anim_stats.get("scenes_rendered"):
        return False
    if not meta.get("video_stats"):
        return False
    # 检测修复痕迹（tier1_fix / tier2_regen / fallback_stub 任意一个出现都视为非一次过）
    render_results = meta.get("render_results") or []
    for r in render_results:
        msg = (r.get("error_message") or "").lower()
        if any(tag in msg for tag in ("fallback_stub", "tier2_regen", "tier1_fix")):
            return False
    return True


def _sum_tokens(usage: Dict[str, Any]) -> int:
    total = 0
    for v in (usage or {}).values():
        if isinstance(v, dict):
            total += int(v.get("total_tokens", 0) or 0)
    return total


def _run_single_pipeline(concept: str) -> Dict[str, Any]:
    """在当前的 ablation_mode 下跑一次完整 pipeline，返回扁平化的 metadata 字典。"""
    from pipeline import Pipeline

    pipe = Pipeline()
    started = time.time()
    raw = pipe.run(concept=concept, target_language="Chinese")
    elapsed = time.time() - started

    meta = raw.get("metadata") or {}
    animation_result = raw.get("animation_result") or {}
    video_result = raw.get("video_result") or {}

    return {
        "pipeline_status": raw.get("status"),
        "error": raw.get("error"),
        "final_video_path": (video_result or {}).get("output_path") if video_result else None,
        "steps_completed": meta.get("steps_completed", []),
        "total_duration": meta.get("total_duration", elapsed),
        "elapsed_sec": elapsed,
        "token_usage": meta.get("token_usage") or {},
        "animation_stats": meta.get("animation_stats"),
        "video_stats": meta.get("video_stats"),
        "ablation": meta.get("ablation"),
        "render_results": (animation_result or {}).get("render_results") or [],
    }


def _evaluate_vqs(video_path: str, knowledge_point: str) -> Dict[str, float]:
    """用 eval/eval_AES.py 的 VideoEvaluator 跑 VQS 评估。"""
    sys.path.insert(0, str(PROJECT_ROOT / "eval"))
    try:
        from eval_AES import VideoEvaluator  # type: ignore
        from gpt_request import request_gemini_with_video  # type: ignore
    finally:
        eval_dir = str(PROJECT_ROOT / "eval")
        if eval_dir in sys.path:
            sys.path.remove(eval_dir)

    evaluator = VideoEvaluator(request_gemini_with_video)
    result = evaluator.evaluate_video(video_path=video_path, knowledge_point=knowledge_point)
    return {
        "overall": float(result.overall_score),
        "element_layout": float(result.element_layout),
        "attractiveness": float(result.attractiveness),
        "logic_flow": float(result.logic_flow),
        "accuracy_depth": float(result.accuracy_depth),
        "visual_consistency": float(result.visual_consistency),
    }


def _run_with_retries(
    concept: str,
    mode: str,
    trial_index: int,
    max_retries: int,
    skip_vqs: bool,
    out_dir: Path,
) -> TrialRecord:
    settings.ablation_mode = mode
    logger.info(
        "[Trial %d] mode=%s concept=%s (ablation switches reloaded)",
        trial_index, mode, concept,
    )

    attempt_metas: List[Dict[str, Any]] = []
    success_meta: Optional[Dict[str, Any]] = None
    total_elapsed = 0.0
    total_tokens = 0

    for attempt in range(max_retries + 1):
        try:
            meta = _run_single_pipeline(concept)
        except Exception as exc:  # noqa: BLE001
            meta = {
                "pipeline_status": "error",
                "error": f"pipeline crash: {exc}",
                "elapsed_sec": 0.0,
                "token_usage": {},
            }
        attempt_metas.append(meta)
        total_elapsed += float(meta.get("elapsed_sec") or 0.0)
        total_tokens += _sum_tokens(meta.get("token_usage") or {})
        if meta.get("pipeline_status") == "success" and meta.get("final_video_path"):
            success_meta = meta
            break

    success_at_0 = bool(attempt_metas[0].get("pipeline_status") == "success" and _scene_success_at_zero(attempt_metas[0]))
    success_at_3 = success_meta is not None

    vqs_breakdown: Dict[str, float] = {}
    vqs_overall: Optional[float] = None
    if success_meta and not skip_vqs and success_meta.get("final_video_path"):
        try:
            vqs_breakdown = _evaluate_vqs(
                video_path=success_meta["final_video_path"],
                knowledge_point=concept,
            )
            vqs_overall = vqs_breakdown.get("overall")
        except Exception as exc:  # noqa: BLE001
            logger.warning("VQS evaluation failed for %s: %s", concept, exc)

    meta_path = out_dir / f"trial_{mode}_{trial_index}_{int(time.time())}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "mode": mode,
                "concept": concept,
                "trial_index": trial_index,
                "attempts": attempt_metas,
                "success_at_0": success_at_0,
                "success_at_3": success_at_3,
                "elapsed_sec": total_elapsed,
                "total_tokens": total_tokens,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return TrialRecord(
        mode=mode,
        concept=concept,
        trial_index=trial_index,
        pipeline_status=(success_meta or attempt_metas[-1]).get("pipeline_status", "error"),
        success_at_0=success_at_0,
        success_at_3=success_at_3,
        retries_used=len(attempt_metas) - 1,
        elapsed_sec=total_elapsed,
        total_tokens=total_tokens,
        final_video_path=(success_meta or {}).get("final_video_path"),
        vqs_overall=vqs_overall,
        vqs_breakdown=vqs_breakdown,
        error=(success_meta or attempt_metas[-1]).get("error"),
        metadata_path=str(meta_path),
    )


def _aggregate(records: List[TrialRecord]) -> List[Dict[str, Any]]:
    """对同一 mode 的所有 trial 求平均，输出符合 Table 4.5 的 5 列。"""
    by_mode: Dict[str, List[TrialRecord]] = {}
    for r in records:
        by_mode.setdefault(r.mode, []).append(r)
    summary = []
    for mode, items in by_mode.items():
        n = len(items)
        if n == 0:
            continue
        s0 = 100.0 * sum(1 for x in items if x.success_at_0) / n
        s3 = 100.0 * sum(1 for x in items if x.success_at_3) / n
        vqs_vals = [x.vqs_overall for x in items if x.vqs_overall is not None]
        vqs = sum(vqs_vals) / len(vqs_vals) if vqs_vals else None
        time_min = sum(x.elapsed_sec for x in items) / n / 60.0
        tokens_k = sum(x.total_tokens for x in items) / n / 1000.0
        summary.append(
            {
                "mode": mode,
                "trials": n,
                "success_at_0": round(s0, 1),
                "success_at_3": round(s3, 1),
                "vqs": round(vqs, 1) if vqs is not None else None,
                "time_min": round(time_min, 1),
                "token_k": round(tokens_k, 1),
            }
        )
    order_index = {m: i for i, m in enumerate(DEFAULT_MODES)}
    summary.sort(key=lambda r: order_index.get(r["mode"], 99))
    return summary


def _write_summary(summary: List[Dict[str, Any]], out_dir: Path) -> Path:
    md_path = out_dir / "summary.md"
    label_map = {
        "none": "AlgoT2V",
        "no_skills": "w/o Skills",
        "no_multi_agent": "w/o Multi-Agent",
        "no_vlm_review": "w/o VLM Review",
        "no_code_repair": "w/o Code Repair",
    }
    lines = [
        "# AlgoT2V Ablation Study (Table 4.5)",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| 方法 | Success@0 | Success@3 | VQS | Time/min | Token/K |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in summary:
        lines.append(
            "| {label} | {s0} | {s3} | {vqs} | {tmin} | {tok} |".format(
                label=label_map.get(row["mode"], row["mode"]),
                s0=row["success_at_0"],
                s3=row["success_at_3"],
                vqs=row["vqs"] if row["vqs"] is not None else "-",
                tmin=row["time_min"],
                tok=row["token_k"],
            )
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="AlgoT2V Table 4.5 ablation runner")
    parser.add_argument(
        "--concepts",
        nargs="+",
        default=DEFAULT_CONCEPTS,
        help="测试概念列表（默认 5 个常见算法）",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        default=DEFAULT_MODES,
        choices=DEFAULT_MODES,
        help="要复现的消融模式（默认 5 个全跑）",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=1,
        help="每个 (mode, concept) 重复次数，建议 >=2 以稳定 Success 率",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="计算 Success@k 时允许的外部重试次数（默认 3，对应 Success@3）",
    )
    parser.add_argument(
        "--skip-vqs",
        action="store_true",
        help="跳过 VQS 评估，仅记录 Success / Time / Token",
    )
    parser.add_argument(
        "--out-dir",
        default=str(PROJECT_ROOT / "eval" / "ablation_results"),
        help="结果输出目录",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw_runs.jsonl"
    raw_path.touch(exist_ok=True)

    records: List[TrialRecord] = []
    for mode in args.modes:
        for concept in args.concepts:
            for trial_index in range(args.trials):
                record = _run_with_retries(
                    concept=concept,
                    mode=mode,
                    trial_index=trial_index,
                    max_retries=args.max_retries,
                    skip_vqs=args.skip_vqs,
                    out_dir=out_dir,
                )
                records.append(record)
                with open(raw_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
                logger.info(
                    "[Done] mode=%s concept=%s trial=%d → S@0=%s S@3=%s VQS=%s tokens=%d time=%.1fs",
                    mode,
                    concept,
                    trial_index,
                    record.success_at_0,
                    record.success_at_3,
                    record.vqs_overall,
                    record.total_tokens,
                    record.elapsed_sec,
                )

    summary = _aggregate(records)
    summary_path = _write_summary(summary, out_dir)
    logger.info("Ablation summary written to %s", summary_path)
    print("\n=== Ablation Summary ===")
    for row in summary:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
