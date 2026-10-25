# 🛠 修复：manim-lint 静态检查报错（Lint Fix）

**用途**：代码通过了语法，但 `manim-lint` 静态检查报错（无效参数、重叠遮挡等），让模型只修被诊断出的问题。
**输入**：原场景计划 + 报错的代码 + manim-lint 诊断信息。
**输出**：修好的完整 Manim 文件（`<manim>...</manim>`）。

## 怎么用
1. 先在项目里跑静态检查拿到诊断（见文末）。
2. 整段复制下面的提示词。
3. 替换 3 个占位符：
   - `【在此粘贴阶段②的场景计划 JSON】`
   - `【在此粘贴报错的完整代码】`
   - `【在此粘贴 manim-lint 诊断信息】`
4. 类名占位符 `AlgorithmFull` 如与你实际类名不同，自行替换。
5. 模型返回修好的完整文件。

---

## 提示词（整段复制）

```
LANGUAGE DIRECTIVE (HARD - OVERRIDES EVERYTHING ELSE)
- target_language = Chinese
- Every on-screen string you put in `Text(...)`, `Tex(...)`,
  scene titles, step text, annotation text, footer text, labels on
  `SurroundingRectangle` / `Arrow` / `Brace`, and every
  `self.voiceover(text="...")` narration MUST be written in
  Chinese.
- `MathTex(...)` stays as standard LaTeX math (do NOT translate
  operators, variables, or function names).
- `Code(code_string=...)` code stays in its original programming
  language; do NOT translate identifiers, keywords, or comments
  inside code snippets.
- Do NOT reproduce bilingual titles like `"冒泡排序 (Bubble Sort)"`.
  Use pure Chinese, e.g. `"冒泡排序"`. If the skill
  template contains a bilingual title, rewrite it in Chinese
  only.
- When target_language is Chinese: no English letters are allowed
  inside Text/Tex/voiceover strings (numbers, math symbols and
  punctuation are fine).

You are fixing a Manim scene that failed static checks from `manim-lint`.
The lint runs against whichever Manim version is installed in the current environment,
so trust the diagnostics over any prior knowledge about a specific Manim release.

ORIGINAL SCENE PLAN:
【在此粘贴阶段②的场景计划 JSON】

CURRENT CODE (CLASS NAME MUST STAY AlgorithmFull):
<manim>
【在此粘贴报错的完整代码】
</manim>

LINT DIAGNOSTICS (errors that MUST be resolved):
【在此粘贴 manim-lint 诊断信息】

RULES:
- Fix ONLY the reported issues; do not redesign the scene.
- Preserve class name, overall structure, and existing variable names used as `target`s.
- Keep VoiceoverScene structure valid:
  * class must inherit from VoiceoverScene
  * must keep self.set_speech_service(...) in construct before voiceover calls
  * keep with self.voiceover(... ) as tracker blocks executable
- Common fixes:
  * ML1xx (invalid kwarg / bad signature) → remove or rename the argument to match the
    API reported by the linter. Never silence ML1xx with an ignore comment.
  * ML3xx (overlap / occlusion):
      - If the overlap is a BUG: reposition with `.next_to(..., buff>=0.5)`, shift, or
        FadeOut the earlier element before introducing the new one.
      - If the overlap is DELIBERATE (e.g. text centered on a shape), add a narrow
        suppression comment on that specific line:
            # manim-lint: ignore-overlap(<obj_a>, <obj_b>)
        Use this only for the exact mobject pair involved.
- Output the full corrected file inside <manim>...</manim> tags. No commentary.
```

---

## 怎么拿到 manim-lint 诊断
项目里自带静态检查工具 [tools/manim_linter.py](../tools/manim_linter.py)，可在 Python 里调用：

```python
from tools.manim_linter import lint_manim_code

with open("你的文件.py", encoding="utf-8") as f:
    code = f.read()
diagnostics = lint_manim_code(code)   # 把返回内容粘进提示词占位符
print(diagnostics)
```

---

## 备注
- 源码出处：[agents/manim_agent.py](../agents/manim_agent.py) `LINT_FIX_PROMPT`。
- 诊断码：`ML1xx` 是无效参数/签名错误（必须改调用，不能用 ignore 注释掩盖）；`ML3xx` 是元素重叠遮挡。
