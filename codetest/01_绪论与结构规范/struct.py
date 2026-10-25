# coding=utf-8
from manim import *

"""
Data Structure Visual Definitions for Manim
此文件用于统一管理并在未来的开发中复用四种核心数据结构（链栈、链队、顺序栈、循环队列）在 Manim 动画中的视觉呈现规范。
"""

# ==========================================
# 1. 链栈 (Linked Stack) - 垂直排布的双舱结构
# ==========================================
def build_linked_stack_node(val_str="", is_tail=False):
    """
    构造链栈结点：包含数据域和指针域。
    链栈的视觉排布为垂直方向（栈顶在上，栈底在下），结点间使用 Arrow 连接。
    
    返回的 VGroup 结构: 
    [0]: 数据域 (Rectangle)
    [1]: 数据文本 (Text)
    [2]: 指针域 (Rectangle)
    [3]: 指针原点 (Dot)
    """
    data_box = Rectangle(width=0.8, height=0.6, color=BLUE)
    data_text = Text(val_str, font_size=24, font="Arial").move_to(data_box.get_center()) if val_str else VGroup()
    next_box = Rectangle(width=0.4, height=0.6, color=BLUE).next_to(data_box, RIGHT, buff=0)
    dot = Dot(radius=0.05, color=WHITE).move_to(next_box.get_center())
    tail_marker = Text("^", font_size=24, color=WHITE).move_to(next_box.get_center())
    
    if is_tail:
        dot.set_opacity(0)
        tail_marker.set_opacity(1)
    else:
        dot.set_opacity(1)
        tail_marker.set_opacity(0)

    node = VGroup(data_box, data_text, next_box, dot, tail_marker)
    node.dot = dot
    node.tail_marker = tail_marker
    return node


# ==========================================
# 2. 链队 (Linked Queue) - 水平排布的双舱结构
# ==========================================
def build_linked_queue_node(val_str, is_head=False, is_tail=False):
    """
    构造链队结点：头结点无有效数据，使用紫色标识。数据结点使用蓝色。
    链队的视觉排布为水平方向（队头在左，队尾在右），使用 Arrow 连接。
    
    返回的 VGroup 结构: 
    [0]: 数据域 (Rectangle)
    [1]: 数据文本 (Text)
    [2]: 指针域 (Rectangle)
    [3]: 指针原点 (Dot)
    """
    color = PURPLE if is_head else BLUE
    data_box = Rectangle(width=1.1, height=0.8, color=color)
    ptr_box = Rectangle(width=0.4, height=0.8, color=color).next_to(data_box, RIGHT, buff=0)
    dot = Dot(radius=0.06, color=color).move_to(ptr_box.get_center())
    data_text = Text(val_str, font_size=24, font="Arial", color=WHITE).move_to(data_box.get_center())
    tail_marker = Text("^", font_size=24, color=color).move_to(ptr_box.get_center())
    
    if is_tail:
        dot.set_opacity(0)
        tail_marker.set_opacity(1)
    else:
        dot.set_opacity(1)
        tail_marker.set_opacity(0)

    node = VGroup(data_box, data_text, ptr_box, dot, tail_marker)
    node.dot = dot
    node.tail_marker = tail_marker
    return node


# ==========================================
# 2.5 双向链表 (Double Linked List) - 三舱结构
# ==========================================
def build_dl_node(val_str, is_head=False, prior_is_null=False, next_is_null=False):
    """
    构造双向链表结点：包含左侧指针域(prior)、中间数据域(data)、右侧指针域(next)。
    """
    color = PURPLE if is_head else BLUE
    
    data_box = Rectangle(width=1.1, height=0.8, color=color)
    prior_box = Rectangle(width=0.4, height=0.8, color=color).next_to(data_box, LEFT, buff=0)
    next_box = Rectangle(width=0.4, height=0.8, color=color).next_to(data_box, RIGHT, buff=0)
    
    data_text = Text(val_str, font_size=24, font="Arial", color=WHITE).move_to(data_box.get_center())
    
    prior_dot = Dot(radius=0.06, color=color).move_to(prior_box.get_center())
    next_dot = Dot(radius=0.06, color=color).move_to(next_box.get_center())
    
    prior_tail_marker = Text("^", font_size=24, color=color).move_to(prior_box.get_center())
    next_tail_marker = Text("^", font_size=24, color=color).move_to(next_box.get_center())
    
    if prior_is_null:
        prior_dot.set_opacity(0)
        prior_tail_marker.set_opacity(1)
    else:
        prior_dot.set_opacity(1)
        prior_tail_marker.set_opacity(0)
        
    if next_is_null:
        next_dot.set_opacity(0)
        next_tail_marker.set_opacity(1)
    else:
        next_dot.set_opacity(1)
        next_tail_marker.set_opacity(0)
        
    node = VGroup(prior_box, data_box, next_box, data_text, prior_dot, next_dot, prior_tail_marker, next_tail_marker)
    node.prior_box = prior_box
    node.data_box = data_box
    node.next_box = next_box
    node.prior_dot = prior_dot
    node.next_dot = next_dot
    node.prior_tail_marker = prior_tail_marker
    node.next_tail_marker = next_tail_marker
    
    return node


# ==========================================
# 3. 顺序栈 (Sequential Stack) - 垂直排布的连续数组
# ==========================================
def build_seq_stack_boxes(max_size=3):
    """
    构造顺序栈内存空间：连续垂直排列的 Square。
    底部为栈底 (S.base)，随着元素的压入，栈顶指针 (S.top) 向上移动。
    """
    return VGroup(*[Square(side_length=0.8, color=BLUE) for _ in range(max_size)]).arrange(UP, buff=0)


# ==========================================
# 4. 循环队列 (Circular Queue) - 水平排布的连续数组
# ==========================================
def build_circular_queue_boxes(max_size=6):
    """
    构造循环队列内存空间：连续水平排列的 Square。
    包含上方位置编号(从1开始) 和下方索引编号(从0开始)。
    使用 front 和 rear 两个游标指针进行遍历。
    """
    box_side = 0.8
    boxes = VGroup(*[Square(side_length=box_side, color=BLUE) for _ in range(max_size)]).arrange(RIGHT, buff=0)
    
    indices = VGroup()
    positions = VGroup()
    for i, box in enumerate(boxes):
        idx_txt = Text(str(i), font_size=20, color=GRAY).next_to(box, DOWN, buff=0.2)
        indices.add(idx_txt)
        pos_txt = Text(str(i + 1), font_size=20, color=GRAY).next_to(box, UP, buff=0.2)
        positions.add(pos_txt)
        
    return VGroup(boxes, indices, positions)


# ==========================================
# 5. 通用标记指针生成器 (Pointer Generator)
# ==========================================
def get_ptr(label, target_mobj, color=GREEN, direction=UP):
    """
    根据给定的方向生成一个带文本标签的箭头指针，用于标识 top, base, front, rear 等游标。
    direction 决定箭头位于目标物体的哪个方位并指向它。
    例如 direction=UP，则指针出现在目标物体上方，箭头朝下指向物体的 get_top()。
    """
    if np.array_equal(direction, UP):
        arrow = Arrow(start=target_mobj.get_top() + UP * 0.8, end=target_mobj.get_top(), buff=0.1, color=color)
        txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, UP, buff=0.1)
    elif np.array_equal(direction, DOWN):
        arrow = Arrow(start=target_mobj.get_bottom() + DOWN * 0.8, end=target_mobj.get_bottom(), buff=0.1, color=color)
        txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, DOWN, buff=0.1)
    elif np.array_equal(direction, LEFT):
        arrow = Arrow(start=target_mobj.get_left() + LEFT * 0.8, end=target_mobj.get_left(), buff=0.1, color=color)
        txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, LEFT, buff=0.1)
    else: # RIGHT
        arrow = Arrow(start=target_mobj.get_right() + RIGHT * 0.8, end=target_mobj.get_right(), buff=0.1, color=color)
        txt = Text(label, font_size=20, font="Arial", color=color).next_to(arrow, RIGHT, buff=0.1)
        
    return VGroup(arrow, txt)

# ==========================================
# 6. 统一展示面板 (用于直接渲染查看效果)
# ==========================================
class StructShowcase(Scene):
    def construct(self):
        title = Text("四大核心数据结构 - 视觉规范一览", font_size=36, font="Microsoft YaHei", weight=BOLD).to_edge(UP)
        self.add(title)

        # 1. 链栈展示 (左侧偏上)
        ls_label = Text("链栈 (Linked Stack)", font_size=24, font="Microsoft YaHei").move_to(LEFT * 4.5 + UP * 2)
        ls_node1 = build_linked_stack_node("10").next_to(ls_label, DOWN, buff=0.5)
        ls_node2 = build_linked_stack_node("20").next_to(ls_node1, DOWN, buff=0.5)
        ls_arrow = Arrow(start=ls_node1[3].get_center(), end=ls_node2[2].get_top(), buff=0.1, color=WHITE)
        ls_ptr = get_ptr("S", ls_node1, ORANGE, direction=LEFT)
        self.add(ls_label, ls_node1, ls_node2, ls_arrow, ls_ptr)

        # 2. 链队展示 (左侧偏下)
        lq_label = Text("链队 (Linked Queue)", font_size=24, font="Microsoft YaHei").move_to(LEFT * 4.5 + DOWN * 1)
        lq_head = build_linked_queue_node("", is_head=True).next_to(lq_label, DOWN, buff=0.5).shift(LEFT * 1)
        lq_node = build_linked_queue_node("10").next_to(lq_head, RIGHT, buff=0.5)
        lq_arrow = Arrow(start=lq_head[3].get_center(), end=lq_node.get_left(), buff=0.1, color=WHITE)
        lq_front = get_ptr("front", lq_head, ORANGE, direction=UP)
        lq_rear = get_ptr("rear", lq_node, ORANGE, direction=DOWN)
        self.add(lq_label, lq_head, lq_node, lq_arrow, lq_front, lq_rear)

        # 3. 顺序栈展示 (右侧偏上)
        ss_label = Text("顺序栈 (Sequential Stack)", font_size=24, font="Microsoft YaHei").move_to(RIGHT * 3.5 + UP * 2)
        ss_boxes = build_seq_stack_boxes(3).next_to(ss_label, DOWN, buff=0.5)
        ss_val = Text("10", font_size=24, font="Arial").move_to(ss_boxes[0].get_center())
        ss_base = get_ptr("S.base", ss_boxes[0], ORANGE, direction=RIGHT)
        ss_top = get_ptr("S.top", ss_boxes[1], GREEN, direction=RIGHT)
        self.add(ss_label, ss_boxes, ss_val, ss_base, ss_top)

        # 4. 循环队列展示 (右侧偏下)
        cq_label = Text("循环队列 (Circular Queue)", font_size=24, font="Microsoft YaHei").move_to(RIGHT * 3.5 + DOWN * 1)
        cq_boxes = build_circular_queue_boxes(4).next_to(cq_label, DOWN, buff=0.8).shift(LEFT * 1)
        cq_val = Text("10", font_size=24, font="Arial").move_to(cq_boxes[0][0].get_center())
        cq_front = get_ptr("front", cq_boxes[0][0], ORANGE, direction=DOWN)
        cq_rear = get_ptr("rear", cq_boxes[0][1], ORANGE, direction=UP)
        self.add(cq_label, cq_boxes, cq_val, cq_front, cq_rear)

        self.wait(2)
