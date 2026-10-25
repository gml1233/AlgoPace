---
name: Stack Algorithms Animation Expert
description: 提供顺序栈(Sequential Stack)可视化的 Manim 动画代码模板和最佳实践，用于生成顺序栈初始化、入栈、出栈和取栈顶元素等动画。
---

# 顺序栈算法动画 SKILL

## 概述

本 SKILL 提供顺序栈在各种常见操作下（初始化、入栈、出栈、取栈顶元素）的 Manim 动画模板。所有模板基于经典的顺序栈数据结构（`base` 指向栈底，`top` 指向栈顶元素的下一位置）。栈以**自底向上垂直堆叠**的方式可视化，符合"栈"在直观上"压入/弹出"的语义，便于读者理解 LIFO（Last-In-First-Out）特性。

## 支持的顺序栈操作

| 编号 | 操作名称 | 文件名 | 描述 | 时间复杂度 |
|------|---------|------|-----------|-----------|
| 1 | 顺序栈初始化 | `init_stack.py` | 分配数组空间，`top = base`，栈空 | O(1) |
| 2 | 入栈 (Push) | `push_stack.py` | 把元素压入栈顶位置，`top++` | O(1) |
| 3 | 出栈 (Pop) | `pop_stack.py` | `top--`，取出原栈顶元素 | O(1) |
| 4 | 取栈顶元素 (GetTop) | `get_top.py` | 只读取 `top - 1` 位置元素，不改变栈状态 | O(1) |

## 公共组件

- `stack_base.py`：顺序栈可视化基类，提供统一的栈格创建、`base` / `top` 指针布置与移动、入栈/出栈动画、元素高亮与文字更新等方法。

## 动画设计规范

### 数据结构规定
- **顺序栈 S**：包含三个域
  - `S.base`：指向栈底的指针（橙色箭头）
  - `S.top`：指向**栈顶元素的下一位置**的指针（黄色箭头）
  - `S.stacksize`：栈容量（最大可容纳元素数）
- **栈空条件**：`S.top == S.base`
- **栈满条件**：`S.top - S.base == S.stacksize`
- **栈元素布局**：从下往上垂直堆叠，最底部的索引为 0，最上方索引为 stacksize-1

### 颜色规范
- **默认栈元素**：蓝色 `BLUE`
- **空栈格**：深灰 `DARK_GRAY`
- **栈顶高亮 / 当前指针**：黄色 `YELLOW`
- **入栈新元素**：绿色 `GREEN`
- **出栈/即将弹出元素**：红色 `RED`
- **base 指针**：橙色 `ORANGE`
- **top 指针**：黄色 `YELLOW`

### 动画节奏
- 入栈/出栈动画：0.5 - 0.8 秒
- top 指针移动：0.5 秒
- 高亮、解说停顿：0.5 - 1.0 秒

### 代码讲解规范
- **代码块呈现**：在涉及到有关具体代码讲解时，必须在场景中呈现对应的代码块（例如使用 `Code` 类展示），以便读者直观理解代码逻辑与动画视觉变化的对应关系。

## 使用方式

在 ManimAgent 生成顺序栈相关动画时：
1. 继承 `stack_base.py` 中的 `StackBase`。
2. 调用 `self.setup_stack_data([初始数据], maxsize=...)`（或 `setup_stack_data_instant`）即可自动生成完整顺序栈（栈格 + base/top 指针 + stacksize 文本）。
3. 使用 `self.push_element(val)` 与 `self.pop_element()` 实现入栈/出栈完整动画（含 top 指针移动）。
4. 使用 `self.highlight_box(index)` / `self.set_value(index, val)` 进行手动微调；步骤文字使用 `self.show_step_text` / `self.update_step_text`。
