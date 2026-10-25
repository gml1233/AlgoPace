# coding=utf-8
from manim import *

class LinkedListBase(Scene):
    """单链表动画公共基类（带头结点，链表L指向头结点）
    提供统一的链表可视化、遍历指针、节点高亮、插入和删除动画方法等
    """

    # ========== 颜色规范 ==========
    COLOR_DEFAULT = BLUE           # 默认数据节点颜色
    COLOR_HEAD = PURPLE            # 头结点颜色
    COLOR_CURRENT = YELLOW         # 当前遍历指针或节点颜色
    COLOR_TARGET = RED             # 目标节点颜色
    COLOR_INSERT = GREEN           # 新插入的节点颜色
    COLOR_L_PTR = ORANGE           # 头指针 L 的颜色

    # ========== 布局参数 ==========
    NODE_WIDTH = 1.2
    NODE_HEIGHT = 0.8
    NODE_SPACING = 1.6             # 节点中心之间的默认距离
    FONT_SIZE = 32

    def setup(self):
        self.nodes = []            # 存储节点的列表，包含头结点
        self.node_mobjects = VGroup()
        self.arrows = VGroup()

    def create_node(self, value_str, color=COLOR_DEFAULT):
        """创建一个单链表节点（矩形框分两半：左边数据，右边指针）"""
        node_group = VGroup()
        
        # 外框
        rect = Rectangle(width=self.NODE_WIDTH, height=self.NODE_HEIGHT, color=color)
        
        # 数据区和指针区分界线（距左边界3/4的宽度）
        divider_x = self.NODE_WIDTH / 4
        divider = Line(
            start=rect.get_top() + RIGHT * divider_x,
            end=rect.get_bottom() + RIGHT * divider_x,
            color=color
        )
        
        # 数据文字（居中于左边的3/4区域）
        val_text = Text(str(value_str), font_size=self.FONT_SIZE)
        val_text.move_to(rect.get_center() + LEFT * (self.NODE_WIDTH / 8))

        # 指针区域的点，表示 next 指针的起点 (居中于右边的1/4区域)
        dot = Dot(radius=0.04, color=color).move_to(
            rect.get_center() + RIGHT * (self.NODE_WIDTH * 3 / 8)
        )

        node_group.add(rect, divider, val_text, dot)
        node_group.rect = rect
        node_group.divider = divider
        node_group.val_text = val_text
        node_group.dot = dot
        node_group.value = value_str

        return node_group

    def setup_list_data(self, values, start_pos=LEFT*4):
        """初始化一个带头结点的链表"""
        self.nodes = []
        self.node_mobjects = VGroup()
        self.arrows = VGroup()
        
        node_values = [""] + values  # "" 表示头结点没有有效数据
        
        for i, val in enumerate(node_values):
            color = self.COLOR_HEAD if i == 0 else self.COLOR_DEFAULT
            node = self.create_node(val, color=color)
            
            if i == 0:
                node.move_to(start_pos)
            else:
                prev_node = self.nodes[-1]
                node.next_to(prev_node, RIGHT, buff=self.NODE_SPACING - self.NODE_WIDTH)

            self.nodes.append(node)
            self.node_mobjects.add(node)

        # 创建节点之间的箭头
        for i in range(len(self.nodes) - 1):
            arrow = self.create_arrow_between(self.nodes[i], self.nodes[i+1])
            self.arrows.add(arrow)

        # 整体居中调整
        group = VGroup(self.node_mobjects, self.arrows)
        group.center()

        self.play(FadeIn(self.node_mobjects), FadeIn(self.arrows))
        
        # 添加指向头结点的 L 指针
        self.add_pointer_L()
        self.wait(0.5)

    def create_arrow_between(self, node1, node2, color=WHITE):
        """创建从 node1 到 node2 的指针箭头"""
        return Arrow(
            start=node1.dot.get_center(),
            end=node2.get_left(),
            buff=0,
            color=color,
            max_tip_length_to_length_ratio=0.15
        )

    def setup_list_data_instant(self, values, start_pos=LEFT*4):
        """瞬时（无动画）初始化并显示带头结点的链表，含 L 指针。

        用于视频开场（algorithm_intro）场景：完整链表（头结点 + 数据节点 + 箭头 + L
        指针）直接 `self.add()` 到画面上，使视频第一帧即为完整结构。
        不调用任何 `self.play(...)`。
        """
        self.nodes = []
        self.node_mobjects = VGroup()
        self.arrows = VGroup()

        node_values = [""] + list(values)

        for i, val in enumerate(node_values):
            color = self.COLOR_HEAD if i == 0 else self.COLOR_DEFAULT
            node = self.create_node(val, color=color)
            if i == 0:
                node.move_to(start_pos)
            else:
                prev_node = self.nodes[-1]
                node.next_to(prev_node, RIGHT, buff=self.NODE_SPACING - self.NODE_WIDTH)
            self.nodes.append(node)
            self.node_mobjects.add(node)

        for i in range(len(self.nodes) - 1):
            arrow = self.create_arrow_between(self.nodes[i], self.nodes[i + 1])
            self.arrows.add(arrow)

        group = VGroup(self.node_mobjects, self.arrows)
        group.center()

        # 头指针 L
        head_node = self.nodes[0]
        l_text = Text("L", font_size=self.FONT_SIZE, color=self.COLOR_L_PTR)
        l_arrow = Arrow(
            start=head_node.get_top() + UP * 1.5,
            end=head_node.get_top(),
            buff=0.1,
            color=self.COLOR_L_PTR,
        )
        l_text.next_to(l_arrow.get_start(), UP, buff=0.1)
        self.L_pointer = VGroup(l_text, l_arrow)

        self.add(self.node_mobjects, self.arrows, self.L_pointer)

    def add_pointer_L(self):
        """在头结点上方添加指针 L，表示指向头结点"""
        head_node = self.nodes[0]
        l_text = Text("L", font_size=self.FONT_SIZE, color=self.COLOR_L_PTR)
        l_arrow = Arrow(
            start=head_node.get_top() + UP * 1.5,
            end=head_node.get_top(),
            buff=0.1,
            color=self.COLOR_L_PTR
        )
        l_text.next_to(l_arrow.get_start(), UP, buff=0.1)
        
        new_L_pointer = VGroup(l_text, l_arrow)
        if hasattr(self, 'L_pointer'):
            self.play(ReplacementTransform(self.L_pointer, new_L_pointer))
            self.L_pointer = new_L_pointer
        else:
            self.L_pointer = new_L_pointer
            self.play(FadeIn(self.L_pointer))

    def create_pointer(self, node, label_text, color=COLOR_CURRENT, direction=DOWN):
        """创建一个临时遍历指针，如 p 或 q"""
        text = Text(label_text, font_size=self.FONT_SIZE, color=color)
        if direction[1] < 0: # DOWN表示箭头朝上指向节点底部，指针文字在下方
            arrow = Arrow(start=node.get_bottom() + DOWN * 1.0, end=node.get_bottom(), buff=0.1, color=color)
            text.next_to(arrow.get_start(), DOWN, buff=0.1)
        else: # UP
            arrow = Arrow(start=node.get_top() + UP * 1.0, end=node.get_top(), buff=0.1, color=color)
            text.next_to(arrow.get_start(), UP, buff=0.1)
        
        ptr_group = VGroup(text, arrow)
        ptr_group.text_obj = text
        ptr_group.arrow_obj = arrow
        return ptr_group

    def move_pointer(self, ptr_group, new_node, direction=DOWN, run_time=0.5):
        """平滑移动遍历指针到新节点"""
        target_ptr = self.create_pointer(new_node, ptr_group.text_obj.text, ptr_group.text_obj.get_color(), direction)
        self.play(ptr_group.animate.move_to(target_ptr.get_center()), run_time=run_time)

    def highlight_node(self, index, color=COLOR_TARGET, run_time=0.5):
        """高亮整块节点"""
        node = self.nodes[index]
        self.play(
            node.rect.animate.set_color(color),
            node.divider.animate.set_color(color),
            node.dot.animate.set_color(color),
            run_time=run_time
        )
        
    def reset_node_color(self, index, run_time=0.5):
        """重置节点颜色"""
        color = self.COLOR_HEAD if index == 0 else self.COLOR_DEFAULT
        self.highlight_node(index, color, run_time)

    def show_step_text(self, text_str):
        if hasattr(self, 'step_text') and self.step_text in self.mobjects:
            self.remove(self.step_text)
        self.step_text = Text(text_str, font_size=self.FONT_SIZE-6).to_edge(UP, buff=0.5)
        self.play(FadeIn(self.step_text))

    def update_step_text(self, new_str):
        new_text = Text(new_str, font_size=self.FONT_SIZE-6).to_edge(UP, buff=0.5)
        self.play(Transform(self.step_text, new_text))
