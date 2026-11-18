import unittest

from agents.teaching_planner import Method, Objectives, TaskNetwork, TeachingRequest, plan_lesson
from eval.teaching_benchmark import Rating, cases


def fixtures():
    design = Objectives.model_validate({"known_prerequisites": ["sorted"],
        "objectives": [{"id": "exclude", "performance": "Explain exclusion",
                        "assessment": "Identify the safe half on new input", "reasons": ["sorted prefix"]}]})
    base = Method.model_validate({"name": "single example", "example": "search for 21",
        "initial_state": "s0", "after": [], "prefer_after": [], "requires_knowledge": ["sorted"],
        "steps": [{"seconds": 8, "reasons": [0], "narration": "Values up to 12 are too small.",
                   "visual": "Shade the excluded prefix", "requires_state": "s0",
                   "produces_state": "s1"}]})
    rich = base.model_copy(deep=True)
    rich.name = "predict with feedback"
    rich.transfer_question = "Which half would remain for 17?"
    rich.steps[0].seconds = 16
    graph = TaskNetwork.model_validate({"tasks": [{"objective_id": "exclude", "methods": [base, rich]}]})
    request = TeachingRequest(goal="Explain exclusion", learner="Knows sorted arrays",
                              seconds=20, reference_case="binary_search_inclusive")
    return request, design, graph


class PlannerTests(unittest.TestCase):
    def test_budget_and_measured_replanning(self):
        req, design, graph = fixtures()
        for scale, expected in [(1, "predict with feedback"), (2, "single example")]:
            scene = plan_lesson("binary search", req, design, graph, estimate_scale=scale)
            self.assertEqual(TaskNetwork.model_validate(graph.model_dump()), graph)
            params = scene.actions[0].parameters
            self.assertEqual(params["method"], expected)
            self.assertEqual(params["from_snapshot"]["value"], 12)
            self.assertEqual(params["to_snapshot"]["value"], 21)
        with self.assertRaisesRegex(ValueError, "shortest estimate"):
            plan_lesson("binary search", req, design, graph, estimate_scale=3)

    def test_invalid_methods(self):
        for defect in ("cycle", "unknown edge", "missing reason", "missing state", "missing prerequisite"):
            req, design, graph = fixtures()
            for method in graph.tasks[0].methods:
                if defect == "cycle":
                    method.after = ["exclude"]
                elif defect == "unknown edge":
                    method.after = ["undefined"]
                elif defect == "missing reason":
                    method.steps[0].reasons = []
                elif defect == "missing state":
                    method.steps[0].produces_state = "invented"
                else:
                    method.requires_knowledge = ["unprovided"]
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                plan_lesson("binary search", req, design, graph)

    def test_ratings(self):
        self.assertEqual(len(list(cases())), 24)
        r = Rating(rendered=True, duration=91, critical_error=False, reasons=[1, 2], budget=90)
        self.assertEqual(r.scores()["coverage"], .75)
        self.assertEqual(r.scores()["primary"], 0)
