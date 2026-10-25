"""VLM 布局审查模块（论文 4.5 节 VLM Review 机制实现）

对渲染产物（无声动画或单场景视频）调用 Gemini 多模态模型，
检查画面是否存在元素遮挡、字幕越界、图形拥挤、视觉层次不清晰等问题。
默认走 Gemini（与 eval/gpt_request.py 共用配置），保持依赖最小。
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("VLMLayoutReviewer")

_REVIEW_PROMPT = """You are a strict visual layout reviewer for an algorithm
animation video. Inspect the provided video clip and look for any of the
following visual defects:

- Overlapping text, labels covering other elements
- Subtitles cut off, going off the safe zone at the bottom
- Crowded graphics, objects spilling outside the visible frame
- Inconsistent visual hierarchy (unreadable font sizes / colors)
- Missing or unfinished animations (blank periods, frozen frames)

Reply with a STRICT JSON object on a single line. Schema:
{"pass": true|false, "issues": ["short bullet ...", ...], "severity": "low"|"medium"|"high"}

Set "pass": true ONLY when no significant defect is visible.
"""


@dataclass
class VLMReviewResult:
    passed: bool
    severity: str = "low"
    issues: List[str] = field(default_factory=list)
    raw_response: str = ""
    error: Optional[str] = None

    def summary(self) -> str:
        if self.error:
            return f"VLM review error: {self.error}"
        if self.passed:
            return "VLM review PASS"
        return (
            f"VLM review FAIL (severity={self.severity}): "
            + "; ".join(self.issues[:5])
        )


class VLMLayoutReviewer:
    """对单段视频做一次布局审查。"""

    def __init__(self, provider: str = "gemini") -> None:
        self.provider = (provider or "gemini").strip().lower()

    def review(self, video_path: str | Path, max_tokens: int = 1024) -> VLMReviewResult:
        path = Path(video_path)
        if not path.exists():
            return VLMReviewResult(passed=False, error=f"video not found: {path}")

        try:
            response = self._call_provider(str(path), max_tokens=max_tokens)
        except Exception as exc:  # noqa: BLE001
            logger.warning("VLM review request failed for %s: %s", path.name, exc)
            return VLMReviewResult(passed=False, error=str(exc))

        return self._parse_response(response)

    def _call_provider(self, video_path: str, max_tokens: int) -> str:
        if self.provider == "gemini":
            # 复用 eval/gpt_request 里的 Gemini 多模态视频请求逻辑
            import sys
            eval_dir = Path(__file__).parent.parent / "eval"
            sys.path.insert(0, str(eval_dir))
            try:
                from gpt_request import request_gemini_with_video  # type: ignore
            finally:
                if str(eval_dir) in sys.path:
                    sys.path.remove(str(eval_dir))
            return request_gemini_with_video(
                prompt=_REVIEW_PROMPT,
                video_path=video_path,
                max_tokens=max_tokens,
                max_retries=2,
                temperature=0.2,
            )
        raise ValueError(f"Unsupported VLM review provider: {self.provider}")

    @staticmethod
    def _parse_response(response: str) -> VLMReviewResult:
        raw = (response or "").strip()
        if not raw:
            return VLMReviewResult(passed=False, error="empty response", raw_response=raw)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return VLMReviewResult(
                passed=False, error="no json in response", raw_response=raw
            )
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            return VLMReviewResult(
                passed=False, error=f"json parse: {exc}", raw_response=raw
            )
        passed = bool(data.get("pass", False))
        severity = str(data.get("severity", "low")).lower()
        issues_raw = data.get("issues", []) or []
        issues = [str(x).strip() for x in issues_raw if str(x).strip()]
        return VLMReviewResult(
            passed=passed,
            severity=severity if severity in {"low", "medium", "high"} else "low",
            issues=issues,
            raw_response=raw,
        )
