"""查找讲解的布局回归检查。使用安装了 Manim 的项目 Python 运行。"""
import ast
import importlib.util
from pathlib import Path
import unittest

import numpy as np
from manim import RED, tempconfig


SOURCE = Path(__file__).parent / "06_查找" / "B-树的插入.py"


def load_scene():
    spec = importlib.util.spec_from_file_location("btree_insertion_feedback", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BTreeInsertionVideo


def example_states():
    """Read the scene's actual examples, including overflow and split states."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
    construct = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "construct")
    assignments = []
    for statement in construct.body:
        if isinstance(statement, ast.Assign):
            target = statement.targets[0]
            base = target.value if isinstance(target, ast.Subscript) else target
            if isinstance(base, ast.Name) and base.id.startswith(("pos_", "spec_")):
                assignments.append(statement)
    namespace = {"np": np, "RED": RED}
    exec(compile(ast.Module(body=assignments, type_ignores=[]), str(SOURCE), "exec"), namespace)
    for state, positions in [("a0", "a"), ("a1", "a"), ("b0", "b0"), ("b1", "b1"), ("b2", "b2")]:
        yield state, namespace["spec_" + state], namespace["pos_" + positions]


class SearchLayoutTests(unittest.TestCase):
    def test_all_insertion_states_have_clear_leaf_gaps_and_connected_edges(self):
        with tempconfig({"dry_run": True}):
            scene = load_scene()()
            for name, spec, positions in example_states():
                with self.subTest(state=name):
                    tree, nodes = scene.build_tree_visual(spec, positions)
                    self.assertGreaterEqual(tree.get_left()[0], -6.76)
                    self.assertLessEqual(tree.get_right()[0], 0.36)
                    leaves = [nodes[k] for k, v in spec.items() if not any(v.get("children", []))]
                    leaves.sort(key=lambda n: n.get_center()[0])
                    for left, right in zip(leaves, leaves[1:]):
                        self.assertGreaterEqual(right.get_left()[0] - left.get_right()[0], 0.3)
                    for node in nodes.values():
                        for rect, label in zip(node.cells, node.texts):
                            np.testing.assert_allclose(rect.get_center(), label.get_center(), atol=1e-6)
                    edge_index = 0
                    for node_id, info in spec.items():
                        for pointer, child in enumerate(info.get("children", [])):
                            if child is not None:
                                edge = tree[0][edge_index]
                                np.testing.assert_allclose(edge.get_start(), nodes[node_id].ptrs[pointer], atol=1e-6)
                                np.testing.assert_allclose(edge.get_end(), nodes[child].get_top(), atol=1e-6)
                                edge_index += 1


if __name__ == "__main__":
    unittest.main()
