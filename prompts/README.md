# 提示词手动工作流（网页对话版）

把项目里写死在代码中的提示词抽离出来，让你可以**直接复制粘贴到任意网页大模型对话框**（ChatGPT / Claude / Gemini / DeepSeek 等），手动跑完整条「算法 → Manim 代码」流水线，然后**自行渲染**。

## 流水线总览

代码里的自动流水线分 3 个核心 LLM 阶段（外加一个可选的前置整理步骤），本目录把每个阶段的提示词单独抽成一个文件：

| 阶段 | 文件 | 输入 | 输出 |
|------|------|------|------|
| ⓪ 知识文档整理（可选） | [00-知识文档整理-Knowledge.md](00-知识文档整理-Knowledge.md) | 教材式原始材料（标题/步骤/代码/分析） | 知识文档 JSON / Markdown |
| ① 概念解析 | [01-概念解析-Concept.md](01-概念解析-Concept.md) | 算法/概念名称（或阶段⓪的知识文档） | 结构化 JSON（概念分析） |
| ② 分镜规划 | [02-分镜规划-Planning.md](02-分镜规划-Planning.md) | 阶段①的 JSON | 场景计划 JSON（scene plan） |
| ③ 代码生成 | [03-代码生成-CodeGen.md](03-代码生成-CodeGen.md) | 阶段②的 JSON + 技能基类 | Manim 代码（`<manim>...</manim>`） |
| 🛠 渲染报错修复 | [04-修复-渲染报错.md](04-修复-渲染报错.md) | 报错的代码 + 运行时报错 | 修好的 Manim 代码 |
| 🛠 Lint 报错修复 | [05-修复-Lint报错.md](05-修复-Lint报错.md) | 报错的代码 + manim-lint 诊断 | 修好的 Manim 代码 |

> 阶段⓪是**可选**的：素材是从教材/题解扒下来的完整程序时，先过一遍它把材料整理干净；如果已有清晰的算法说明，直接从阶段①开始。

## 怎么用

### 阶段 ⓪：知识文档整理（可选）
1. 打开 [00-知识文档整理-Knowledge.md](00-知识文档整理-Knowledge.md)，复制【系统提示词】+【用户消息】。
2. 把用户消息里的 4 段占位符替换成你的原始材料（标题 / 步骤 / 代码 / 分析）。
3. 模型返回知识文档 JSON（可再渲染成 Markdown），用它作为阶段①的输入。

### 阶段 ①：概念解析
1. 打开 [01-概念解析-Concept.md](01-概念解析-Concept.md)，把里面**系统提示词**整段复制进网页对话框。
2. 另起一行（或下一条消息）写上你要做的算法，例如 `冒泡排序`。
3. 模型返回一段 JSON —— 这就是「概念分析」，复制保存。

### 阶段 ②：分镜规划
1. 打开 [02-分镜规划-Planning.md](02-分镜规划-Planning.md)，复制整段提示词。
2. 把提示词里的占位符 `【在此粘贴阶段①的概念分析 JSON】` 替换成阶段①的输出。
3. 模型返回「场景计划 JSON」（单场景，含 `actions` 时间线），复制保存。

### 阶段 ③：代码生成
1. 打开 [03-代码生成-CodeGen.md](03-代码生成-CodeGen.md)。
2. 按文件里的说明，依次填入：
   - 阶段②的场景计划 JSON
   - 类名、目标时长
   - **对应算法家族的技能基类代码 + 一个示例模板**（从 `.agent/skills/<家族>/examples/` 里取，文件路径见该文件内的对照表）
3. 模型返回 `<manim>...</manim>` 包裹的代码。

### 自行渲染
把阶段③输出的代码（去掉 `<manim>` 标签）存成 `.py` 文件，放进项目目录，然后：

```powershell
manim -ql 你的文件.py 类名
```

> 生成的代码默认带语音旁白（`VoiceoverScene` + Edge TTS），渲染前确认已安装 `manim_voiceover`，且 `generation/tts/edge_service.py` 可被 import。
> 代码默认继承技能基类（如 `SortingBase`/`TreeBase`），所以渲染时务必把文件放在项目内、能 import 到 `.agent/skills/...` 下的基类，或把基类代码一并贴进文件顶部。

如果渲染报错 → 用 [04-修复-渲染报错.md](04-修复-渲染报错.md)。
如果想先做静态检查 → 项目里有 `tools/manim_linter.py`，报错后用 [05-修复-Lint报错.md](05-修复-Lint报错.md)。

## 几个重要约定（提示词里硬性要求，渲染前留意）

- **单场景模式**：整条流水线只产出**一个** Manim 类，把开场→初始化→主流程→收尾→复杂度全部塞进一个 `construct()`。
- **语言**：所有提示词已把 `target_language` 设为 **Chinese（中文）**。要换语言，把每个文件开头「语言指令」里的 `Chinese` 改掉即可。
- **TTS**：已按项目 `.env` 里的 `TTS_PROVIDER=edge` 填好（`zh-CN-YunxiNeural` 音色）。换 TTS 见阶段③文件末尾的备选片段。
- **技能基类**：阶段③要求继承 `SortingBase`/`TreeBase`/`LinkedListBase`/`StackBase`/`SeqListBase` 等基类，并强制用基类的 `self.show_array` / `self.setup_default_tree` 等方法绘制数据结构，禁止手搓 `Circle`/`Square`。

## 提示词出处（源码位置）

- 阶段⓪ ：[agents/knowledge_curator.py](../agents/knowledge_curator.py) `SYSTEM_PROMPT`
- 阶段① ：[agents/concept_interpreter.py](../agents/concept_interpreter.py) `SYSTEM_PROMPT`
- 阶段② ：[agents/manim_agent.py](../agents/manim_agent.py) `SCENE_PLANNING_PROMPT`
- 阶段③ ：[agents/manim_agent.py](../agents/manim_agent.py) `CODE_GENERATION_PROMPT` + `_build_skill_prompt_section()`
- 修复 ：[agents/manim_agent.py](../agents/manim_agent.py) `RENDER_FIX_PROMPT` / `LINT_FIX_PROMPT`
