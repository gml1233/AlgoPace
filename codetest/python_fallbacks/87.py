"""B-树查找（由算法 ID 87 的 C++ 逻辑改写，索引改用 Python 的 0 起始）。"""

from bisect import bisect_left
from dataclasses import dataclass, field


@dataclass
class BTreeNode:
    keys: list[int] = field(default_factory=list)
    children: list["BTreeNode"] = field(default_factory=list)


@dataclass
class SearchResult:
    node: BTreeNode | None
    index: int
    found: bool


def search_btree(root: BTreeNode | None, key: int) -> SearchResult:
    """返回所在结点和索引；未找到时返回应插入的叶结点及位置。"""
    node = root
    parent = None
    index = 0
    while node is not None:
        index = bisect_left(node.keys, key)
        if index < len(node.keys) and node.keys[index] == key:
            return SearchResult(node, index, True)
        parent = node
        if not node.children:
            break
        node = node.children[index]
    return SearchResult(parent, index, False)
