"""Run python -m eval.teaching_benchmark cases, or score <completed-ratings.json>."""
import argparse
import json
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


GOALS = {
    "B 树删除": ("判断借位或合并的条件", "解释为什么借位时要调整父分隔键"),
    "二分查找": ("根据比较结果更新闭区间", "解释有序性为什么保证排除区间不漏解"),
    "KMP": ("按前缀表计算失配后的模式位置", "解释重用匹配前后缀为什么不会漏解"),
    "快速排序划分": ("手算一次 Lomuto 划分", "解释已划分区间的不变量"),
    "并查集路径压缩": ("确定查找后哪些父指针改变", "解释压缩为什么保持集合归属"),
    "非递归中序遍历": ("手算栈和输出序列", "解释为何弹栈时左子树已遍历"),
}


def cases():
    for topic, goals in GOALS.items():
        for goal in goals:
            for seconds in (90, 180):
                yield {"topic": topic, "goal": goal, "seconds": seconds,
                       "learner": "已掌握该数据结构的基本操作，正在学习目标算法"}


class Rating(BaseModel):
    rendered: bool
    duration: float = Field(ge=0, allow_inf_nan=False)
    critical_error: bool
    reasons: list[int] = Field(min_length=1)
    budget: int = Field(gt=0)

    @model_validator(mode="after")
    def valid_ratings(self):
        if any(v not in (0, 1, 2) for v in self.reasons):
            raise ValueError("Each required reason is rated 0, 1 or 2")
        if self.rendered and self.duration <= 0:
            raise ValueError("A rendered film requires a positive measured duration")
        return self

    def scores(self):
        coverage = sum(self.reasons) / (2 * len(self.reasons))
        within = self.rendered and self.duration <= self.budget
        return {"coverage": coverage, "within_budget": within,
                "overrun_seconds": max(0, self.duration-self.budget),
                "primary": coverage if within and not self.critical_error else 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("cases")
    commands.add_parser("score").add_argument("ratings", type=Path)
    args = parser.parse_args()
    if args.command == "cases":
        result = list(cases())
    else:
        rows = json.loads(args.ratings.read_text(encoding="utf-8-sig"))
        if not rows:
            parser.error("Supply at least one rating")
        scores = [Rating.model_validate(row).scores() for row in rows]
        result = {"samples": scores, "mean_primary": sum(r["primary"] for r in scores)/len(scores)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
