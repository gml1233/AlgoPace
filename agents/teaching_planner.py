"""Aligned objectives, HTN method alternatives and budgeted lesson planning."""
from uuid import uuid4
from graphlib import CycleError, TopologicalSorter
from itertools import product
from typing import Literal, Optional

from agents.reference_cases import REFERENCE_CASES

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agents.manim_models import SceneAction, ScenePlan


class TeachingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)


class TeachingRequest(TeachingModel):
    goal: str = Field(max_length=1000)
    learner: str = Field(max_length=1000)
    seconds: int = Field(gt=0, le=3600)
    reference_case: Optional[Literal["binary_search_inclusive", "btree_t2_right_borrow"]] = None


class Objective(TeachingModel):
    id: str
    performance: str
    assessment: str
    reasons: list[str] = Field(min_length=1, max_length=6)


class Objectives(TeachingModel):
    objectives: list[Objective] = Field(min_length=1, max_length=6)
    known_prerequisites: list[str]

    @model_validator(mode="after")
    def unique_ids(self):
        if len({o.id for o in self.objectives}) != len(self.objectives):
            raise ValueError("Objective IDs must be unique")
        return self


class TeachingStep(TeachingModel):
    narration: str
    visual: str
    seconds: int = Field(ge=1)
    # States are named snapshots local to one method/example.
    requires_state: str
    produces_state: str
    # Optional summarized transition from the previous state to requires_state.
    bridge: str = Field(default="", min_length=0)
    reasons: list[int]


class Method(TeachingModel):
    name: str
    example: str
    initial_state: str
    requires_knowledge: list[str]
    after: list[str]  # Objective IDs with a hard presentation dependency.
    prefer_after: list[str]  # Soft narrative ordering.
    steps: list[TeachingStep] = Field(min_length=1, max_length=10)
    # Transfer questions are optional; time for them is included in steps.
    transfer_question: str = Field(default="", min_length=0)


class CompoundTask(TeachingModel):
    objective_id: str
    methods: list[Method] = Field(min_length=1, max_length=3)


class TaskNetwork(TeachingModel):
    tasks: list[CompoundTask] = Field(min_length=1, max_length=6)


def _applicable(method, objective, known, snapshots):
    if not set(method.requires_knowledge) <= known:
        return False
    state = method.initial_state
    indices = {name: i for i, name in enumerate(snapshots)}
    if indices and state not in indices:
        return False
    coverage = set()
    for step in method.steps:
        if step.requires_state != state and not step.bridge:
            return False
        if indices:
            if step.requires_state not in indices or step.produces_state not in indices:
                return False
            if not indices[state] <= indices[step.requires_state] <= indices[step.produces_state]:
                return False
        coverage.update(step.reasons)
        state = step.produces_state
    return coverage == set(range(len(objective.reasons)))


def _order(methods):
    deps = {key: set(m.after) for key, m in methods.items()}
    sorter = TopologicalSorter(deps)
    sorter.prepare()
    ordered = []
    while sorter.is_active():
        ready = set(sorter.get_ready())
        while ready:
            key = min(ready, key=lambda k: (len(set(methods[k].prefer_after) - set(ordered)), k))
            ready.remove(key)
            ordered.append(key)
            sorter.done(key)
    return ordered


def plan_lesson(topic, request, design, network, *, estimate_scale=1.0):
    """Enumerate bounded method combinations. Keep complete methods and reason coverage."""
    goals = {o.id: o for o in design.objectives}
    tasks = {t.objective_id: t for t in network.tasks}
    if len(tasks) != len(network.tasks) or tasks.keys() != goals.keys():
        raise ValueError("Task graph must contain exactly one compound task per objective")
    snapshots = REFERENCE_CASES[request.reference_case]() if request.reference_case else {}
    options = []
    for key, task in tasks.items():
        applicable = []
        for method in task.methods:
            if not set(method.after + method.prefer_after) <= goals.keys():
                raise ValueError(f"Unknown dependency in {key}/{method.name}")
            if _applicable(method, goals[key], set(design.known_prerequisites), snapshots):
                applicable.append(method)
        if not applicable:
            raise ValueError(f"No method covers all reasons with valid prerequisites/states: {key}")
        options.append(applicable)
    best = None
    shortest = None
    for choices in product(*options):
        methods = dict(zip(tasks, choices))
        try:
            order = _order(methods)
        except CycleError:
            continue
        seconds = sum(step.seconds for m in choices for step in m.steps)
        shortest = seconds if shortest is None else min(shortest, seconds)
        if seconds * estimate_scale > request.seconds:
            continue
        # Rewards a specified transfer opportunity and satisfied narrative relations.
        # Ties prefer the cheaper complete explanation.
        score = (sum(bool(m.transfer_question) for m in choices),
                 sum(p in order[:i] for i, key in enumerate(order) for p in methods[key].prefer_after),
                 -seconds)
        if best is None or score > best[0]:
            best = score, methods, order
    if best is None:
        if shortest is None:
            raise ValueError("No acyclic teaching plan")
        raise ValueError(f"No plan within {request.seconds}s; shortest estimate {shortest * estimate_scale:.1f}s")
    _, methods, order = best
    actions = []
    for key in order:
        method = methods[key]
        for i, step in enumerate(method.steps):
            actions.append(SceneAction(action_type="teach", element_type="diagram",
                target=f"{key}_{i+1}", description=step.visual, duration=step.seconds,
                parameters={"objective": goals[key].performance, "method": method.name,
                            "criterion": goals[key].assessment, "example": method.example,
                            "reference_case": request.reference_case,
                            "from_snapshot": snapshots.get(step.requires_state),
                            "to_snapshot": snapshots.get(step.produces_state),
                            "narration": step.narration, "from_state": step.requires_state,
                            "to_state": step.produces_state, "bridge": step.bridge,
                            "explain": [goals[key].reasons[j] for j in step.reasons],
                            "transfer_question": method.transfer_question if i == len(method.steps)-1 else ""}))
    return ScenePlan(id="aligned_lesson_" + uuid4().hex[:12], title=topic, sub_concept_id="",
                     description=f"{request.goal} ({request.seconds}s maximum)", actions=actions)

