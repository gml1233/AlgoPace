"""B-树查找与插入演示使用的 Python 实现。

数组的 0 号关键字位置空置；阶数默认为 3，视频示例使用 4 阶。
"""


class Result:
    def __init__(self, pt, i, tag):
        self.pt = pt
        self.i = i
        self.tag = tag


class BTNode:
    def __init__(self, keynum, parent, order):
        self.keynum = keynum
        self.parent = parent
        self.k = [None] * (order + 1)
        self.ptr = [None] * (order + 1)
        self.recptr = [None] * (order + 1)


class BTree:
    def __init__(self, order=3):
        self.m = order

    def split(self, q, s, ap):
        # 关键字与子树指针移入右侧新结点
        m = self.m
        ap.k[1:m - s + 1] = q.k[s + 1:m + 1]
        ap.ptr[0:m - s + 1] = q.ptr[s:m + 1]
        ap.recptr[1:m - s + 1] = q.recptr[s + 1:m + 1]
        q.keynum = s - 1
        for child in ap.ptr[:ap.keynum + 1]:
            if child is not None:
                child.parent = ap
        return ap

    def insert(self, q, i, x, ap):
        # 在 q.k[i] 与 q.k[i + 1] 之间插入 x
        k = q.keynum
        while k > i:
            q.k[k + 1] = q.k[k]
            q.ptr[k + 1] = q.ptr[k]
            q.recptr[k + 1] = q.recptr[k]
            k -= 1
        q.k[i + 1] = x
        q.ptr[i + 1] = ap
        q.recptr[i + 1] = None
        q.keynum += 1
        if ap is not None:
            ap.parent = q

    def search(self, p, key):
        # 返回最后一个不大于 key 的关键字下标；0 表示在第一个关键字前
        i = 0
        while i < p.keynum and p.k[i + 1] <= key:
            i += 1
        return i

    def new_root(self, t, x, ap):
        q = BTNode(1, None, self.m)
        q.k[1] = x
        q.ptr[0:2] = [t, ap]
        if t is not None:
            t.parent = q
        if ap is not None:
            ap.parent = q
        return q

    def search_btree(self, t, key):
        p = t
        q = None
        found = False
        i = 0
        while p and not found:
            i = self.search(p, key)
            if i > 0 and p.k[i] == key:
                found = True
            else:
                q = p
                p = p.ptr[i]
        if found:
            return Result(p, i, 1)
        return Result(q, i, 0)

    def insert_btree(self, t, key, q, i):
        x = key
        ap = None
        finished = False
        while q and not finished:
            self.insert(q, i, x, ap)
            if q.keynum < self.m:
                finished = True
            else:
                s = (self.m + 1) // 2
                ap = BTNode(self.m - s, q.parent, self.m)
                ap = self.split(q, s, ap)
                x = q.k[s]
                q = q.parent
                if q:
                    i = self.search(q, x)
        if not finished:
            t = self.new_root(t, x, ap)
        return t

    def in_order_traverse_re(self, t):
        if t is not None:
            self.in_order_traverse_re(t.ptr[0])
            for i in range(t.keynum):
                print(t.k[i + 1], end=" ")
                self.in_order_traverse_re(t.ptr[i + 1])

    def create_btree(self, t, n):
        for _ in range(n):
            key = int(input())
            result = self.search_btree(t, key)
            if result.tag == 0:
                t = self.insert_btree(t, key, result.pt, result.i)
        return t


if __name__ == "__main__":
    tree = BTree()
    print("请输入关键字个数：")
    count = int(input())
    print("请输入所有关键字，每输入一个关键字按回车换行")
    root = tree.create_btree(None, count)
    key = int(input("请输入要插入的关键字："))
    result = tree.search_btree(root, key)
    if result.tag == 0:
        root = tree.insert_btree(root, key, result.pt, result.i)
    print("B-树的中序遍历结果为：", end="")
    tree.in_order_traverse_re(root)
