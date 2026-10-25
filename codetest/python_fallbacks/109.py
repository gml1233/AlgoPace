"""3 阶 B-树插入（由算法 ID 109 的 C++ 逻辑改写）。"""

from bisect import bisect_left
from dataclasses import dataclass, field


ORDER = 3  # 最多 3 个子树、2 个关键字；第 3 个关键字触发分裂


@dataclass
class BTreeNode:
    keys: list[int] = field(default_factory=list)
    children: list["BTreeNode"] = field(default_factory=list)


def insert_btree(root: BTreeNode | None, key: int) -> tuple[BTreeNode, bool]:
    """插入关键字，返回 (新根结点, 是否插入成功)；重复值不插入。"""
    if root is None:
        return BTreeNode([key]), True

    def insert_into(node: BTreeNode):
        index = bisect_left(node.keys, key)
        if index < len(node.keys) and node.keys[index] == key:
            return False, None

        if node.children:
            inserted, promoted = insert_into(node.children[index])
            if not inserted:
                return False, None
            if promoted is not None:
                middle, right = promoted
                node.keys.insert(index, middle)
                node.children.insert(index + 1, right)
        else:
            node.keys.insert(index, key)

        if len(node.keys) < ORDER:
            return True, None

        # 结点溢出：中间关键字上移，左右两部分各保留一个结点。
        split_at = len(node.keys) // 2
        middle = node.keys[split_at]
        right = BTreeNode(node.keys[split_at + 1:],
                          node.children[split_at + 1:] if node.children else [])
        node.keys = node.keys[:split_at]
        if node.children:
            node.children = node.children[:split_at + 1]
        return True, (middle, right)

    inserted, promoted = insert_into(root)
    if promoted is not None:
        middle, right = promoted
        root = BTreeNode([middle], [root, right])
    return root, inserted
