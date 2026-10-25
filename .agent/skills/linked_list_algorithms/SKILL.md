---
name: Linked List Algorithms Animation Expert
description: 提供带头结点的单链表(Singly Linked List)可视化的 Manim 动画代码模板和最佳实践，用于生成单链表初始化、取值、查找、插入和删除动画。
---

# 单链表算法动画 SKILL

## 概述

本 SKILL 提供单链表在各种常见操作下（初始化、取值、查找、插入、删除）的 Manim 动画模板。所有模板基于带头结点的单链表数据结构，由指针 `L` 指向头结点。这些模板可直接用于生成高质量的包含解说和动态展示的教学视频。

## 支持的单链表操作

| 编号 | 操作名称 | 文件名 | 描述 | 时间复杂度 |
|------|---------|------|-----------|-----------|
| 1 | 单链表初始化 | `init_linked_list.py` | 链表 L 指向一个空的头结点 | O(1) |
| 2 | 单链表取值 | `get_value.py` | 根据序号从头结点开始向后遍历，找到对应序号的值 | O(n) |
| 3 | 单链表查找 | `find_value.py` | 根据值从头结点开始向后遍历，寻找匹配的结点 | O(n) |
| 4 | 单链表插入 | `insert_node.py` | 在第 i 个位置之前插入新结点 | O(n) |
| 5 | 单链表删除 | `delete_node.py` | 删除第 i 个结点资源并断开指针 | O(n) |

## 公共组件

- `linked_list_base.py`：单链表可视化基类，提供统一的结点创建、指针创建与移动（用于遍历如 `p`、`q`）、颜色高亮和默认列表布置动画。
- `linked_list_base.py`：单链表可视化基类，提供统一的节点创建、指针创建与移动（用于遍历如 `p`、`q`）、颜色高亮和默认列表布置动画。

## 动画设计规范

### 数据结构规定
- **统一双舱结构 (强制规定)**：所有结点（包含头结点和普通数据结点）在视觉呈现上**必须**采用“1个数据域 + 1个指针域”的拼接结构。严禁使用单一的 Rectangle 或 Square 充当链表结点。
  - **建议的通用实现方式**：
    ```python
    def create_list_node(color=WHITE):
        data_box = Rectangle(width=1.1, height=0.8, color=color)
        ptr_box = Rectangle(width=0.4, height=0.8, color=color).next_to(data_box, RIGHT, buff=0)
        ptr_dot = Dot(radius=0.06, color=color).move_to(ptr_box.get_center())
        return VGroup(data_box, ptr_box, ptr_dot)
    ```
  - **指针连线准则**：所有表示 `next` 指针的 Arrow，其起点必须在指针域中心的小圆点处（即结点的 `[2].get_center()`），终点指向下一个结点的左边缘。
- **链表 L**：表示单链表的入口，它是一个指针 `L` 指向链表的 **头结点 (Head)**。
- **头结点**：链表的第一个结点，它不包含具有实际意义的有效数据，只是为了方便操作而保留，但也**必须遵循上述的双舱结构**。
- **数据结点**：单链表的主体结点，包含左侧的数据域和右侧的指针域。

### 颜色规范
- **默认结点**：蓝色 `BLUE`
- **头结点**：紫色 `PURPLE`
- **当前遍历指针/当前到达结点**：黄色 `YELLOW`
- **目标结点**：红色 `RED`
- **插入或找到的结点**：绿色 `GREEN`
- **头指针 L**：橙色 `ORANGE`

### 动画节奏
- 指针平移移动等操作：0.5 秒
- 更新或高亮等待时间：0.5 - 1.0 秒

### 代码讲解规范
- **代码块呈现**：在涉及到有关具体代码讲解时，必须在场景中呈现对应的代码块（例如使用 `Code` 类展示），以便读者直观理解代码逻辑与动画视觉变化的对应关系。

## 使用方式

在 ManimAgent 生成单链表相关动画时：
1. 必定继承 `linked_list_base.py` 中的 `LinkedListBase`。
2. 调用 `self.setup_list_data([数据列表])` 即可自动生成带头结点的链表。
3. 利用 `self.create_pointer(node, "p")` 生成临时指针并通过 `self.move_pointer(ptr, new_node)` 实现遍历效果。
4. 在需要连线或断开的地方，操作 `node.dot` 和 `Arrow` 调整结点的连线。