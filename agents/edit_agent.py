"""
EditAgent: a coding-agent that modifies Manim scene files and SRT subtitles
via OpenAI-compatible function calling (tool use).

The merged Manim code is split into a virtual file system where each scene
becomes a separate .py file, and the SRT content becomes subtitles.srt.
The LLM is given tools (list_files, read_file, edit_file, create_file,
delete_file) and iterates autonomously until the edit is complete.
"""
import json
import logging
import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple, Callable, Iterator

from agents.base import BaseAgent
from agents.manim_models import EditResult


# ---------------------------------------------------------------------------
# Virtual file system
# ---------------------------------------------------------------------------

class VirtualFileSystem:
    """In-memory file system that holds scene .py files and subtitles.srt."""
    SCENE_ORDER_FILE = "scene_order"

    SCENE_HEADER_RE = re.compile(
        r"^# ==========\s*场景\s*\d+:\s*(\S+)\s*\(ID:\s*(\S+)\)\s*==========\s*$"
    )
    COMMENT_SKIP_PREFIXES = (
        "# ========== AlgoT2V",
        "# 您可以在此编辑",
        "# 每个 Scene 类",
        "# 注意：请确保",
    )

    def __init__(self) -> None:
        self.files: OrderedDict[str, str] = OrderedDict()
        self._scene_meta: OrderedDict[str, Dict] = OrderedDict()

    # ---- construction ----

    def parse(self, manim_code: str, srt_content: str) -> None:
        """Parse combined manim code + SRT into virtual files."""
        self.files.clear()
        self._scene_meta.clear()

        if manim_code and manim_code.strip():
            self._parse_manim(manim_code)

        if srt_content and srt_content.strip():
            self.files["subtitles.srt"] = srt_content
        self._refresh_scene_order_file()

    def _parse_manim(self, code: str) -> None:
        lines = code.splitlines()
        current_id: Optional[str] = None
        current_name: Optional[str] = None
        buf: List[str] = []

        def _flush():
            nonlocal current_id, current_name, buf
            if current_id is not None:
                filename = f"{current_id}.py"
                self.files[filename] = "\n".join(buf).strip() + "\n"
                self._scene_meta[filename] = {
                    "scene_name": current_name,
                    "scene_id": current_id,
                }
            current_id = None
            current_name = None
            buf = []

        for line in lines:
            if any(line.startswith(p) for p in self.COMMENT_SKIP_PREFIXES):
                continue

            m = self.SCENE_HEADER_RE.match(line)
            if m:
                _flush()
                current_name = m.group(1)
                current_id = m.group(2)
                continue

            if current_id is not None:
                buf.append(line)
            else:
                buf.append(line)

        _flush()

        if not self.files and code.strip():
            self.files["scene.py"] = code.strip() + "\n"

    # ---- tool operations ----

    def list_files(self) -> str:
        if not self.files:
            return "(empty workspace)"
        parts: List[str] = []
        for name, content in self.files.items():
            line_count = content.count("\n")
            if not content.endswith("\n"):
                line_count += 1
            meta = self._scene_meta.get(name)
            suffix = f"  (scene: {meta['scene_name']})" if meta else ""
            parts.append(f"{name}  ({line_count} lines){suffix}")
        return "\n".join(parts)

    def read_file(self, file_path: str, start_line: Optional[int] = None,
                  end_line: Optional[int] = None) -> str:
        if file_path not in self.files:
            return f"Error: file '{file_path}' not found. Use list_files to see available files."
        content = self.files[file_path]
        lines = content.splitlines()

        if start_line is not None or end_line is not None:
            s = max((start_line or 1) - 1, 0)
            e = min(end_line or len(lines), len(lines))
            lines = lines[s:e]
            offset = s
        else:
            offset = 0

        numbered = [f"{offset + i + 1:>4}|{line}" for i, line in enumerate(lines)]
        return "\n".join(numbered)

    def edit_file(self, file_path: str, old_string: str, new_string: str) -> str:
        if file_path not in self.files:
            return f"Error: file '{file_path}' not found."
        content = self.files[file_path]
        count = content.count(old_string)
        if count == 0:
            return (
                f"Error: old_string not found in '{file_path}'. "
                "Make sure it matches the file content exactly (including whitespace and indentation). "
                "Use read_file to verify the current content."
            )
        if count > 1:
            return (
                f"Error: old_string matches {count} locations in '{file_path}'. "
                "Provide more surrounding context to make the match unique."
            )
        self.files[file_path] = content.replace(old_string, new_string, 1)
        return "OK"

    def create_file(self, file_path: str, content: str) -> str:
        if file_path in self.files:
            return f"Error: file '{file_path}' already exists. Use edit_file to modify it."
        self.files[file_path] = content
        if file_path.endswith(".py"):
            scene_id = file_path.removesuffix(".py")
            class_match = re.search(r"class\s+(\w+)\s*\(", content)
            scene_name = class_match.group(1) if class_match else scene_id
            self._scene_meta[file_path] = {
                "scene_name": scene_name,
                "scene_id": scene_id,
            }
            self._refresh_scene_order_file()
        return "OK"

    def delete_file(self, file_path: str) -> str:
        if file_path not in self.files:
            return f"Error: file '{file_path}' not found."
        if file_path == self.SCENE_ORDER_FILE:
            return f"Error: '{self.SCENE_ORDER_FILE}' is a reserved workspace file and cannot be deleted."
        removed_py = file_path.endswith(".py")
        del self.files[file_path]
        self._scene_meta.pop(file_path, None)
        if removed_py:
            self._refresh_scene_order_file()
        return "OK"

    # ---- reconstruction ----

    def rebuild_manim_code(self) -> str:
        parts: List[str] = []
        parts.append("# ========== AlgoT2V 生成的 Manim 动画源代码 ==========")
        parts.append("# 您可以在此编辑代码，然后点击「重新渲染」按钮生成新视频")
        parts.append("# 每个 Scene 类对应一个动画场景，按顺序拼接")
        parts.append("# 注意：请确保每个 Scene 类名唯一且正确")
        parts.append("")

        scene_idx = 0
        for filename in self._resolve_scene_order():
            content = self.files.get(filename, "")
            scene_idx += 1
            meta = self._scene_meta.get(filename, {})
            scene_name = meta.get("scene_name", filename.removesuffix(".py"))
            scene_id = meta.get("scene_id", filename.removesuffix(".py"))
            parts.append(
                f"# ========== 场景 {scene_idx}: {scene_name} (ID: {scene_id}) =========="
            )
            parts.append(content.rstrip())
            parts.append("")

        return "\n".join(parts)

    def get_srt_content(self) -> str:
        return self.files.get("subtitles.srt", "")

    def iter_scene_files(self) -> List[Tuple[str, Dict]]:
        """Ordered (filename, meta) for each .py scene file. meta has scene_id, scene_name."""
        out: List[Tuple[str, Dict]] = []
        for filename in self._resolve_scene_order():
            meta = dict(self._scene_meta.get(filename, {}))
            meta.setdefault("scene_id", filename.removesuffix(".py"))
            meta.setdefault("scene_name", meta["scene_id"])
            out.append((filename, meta))
        return out

    def _refresh_scene_order_file(self) -> None:
        """Regenerate scene_order file from current .py files order."""
        scene_files = [
            filename for filename in self.files.keys()
            if filename.endswith(".py")
        ]
        content = "\n".join(scene_files)
        if content:
            content += "\n"
        self.files[self.SCENE_ORDER_FILE] = content

    def _resolve_scene_order(self) -> List[str]:
        """Resolve final scene order from scene_order; append missing .py files at tail."""
        current_scene_files = [
            filename for filename in self.files.keys()
            if filename.endswith(".py")
        ]
        ordered: List[str] = []
        seen = set()

        raw_order = self.files.get(self.SCENE_ORDER_FILE, "")
        for raw_line in raw_order.splitlines():
            name = raw_line.strip()
            if not name.endswith(".py"):
                continue
            if name not in self.files:
                continue
            if name in seen:
                continue
            ordered.append(name)
            seen.add(name)

        for filename in current_scene_files:
            if filename in seen:
                continue
            ordered.append(filename)
            seen.add(filename)
        return ordered


def _format_time(seconds: float) -> str:
    """Format seconds into M:SS or H:MM:SS for human-friendly display."""
    total = int(round(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _build_workspace_overview_with_durations(
    vfs: VirtualFileSystem,
    scene_durations: Optional[Dict[str, float]],
) -> str:
    """
    Build the Workspace overview string.

    - 若未提供 scene_durations: 退化为 VirtualFileSystem.list_files() 的当前行为。
    - 若提供: 在每个 .py 场景文件后追加带时长的场景名称
      (scene: FooScene, durations: 0:00~1:23)
    """
    # 无时长信息时，保持现有 list_files 行为，保证兼容性。
    if not scene_durations:
        return vfs.list_files()

    # 先按场景顺序计算每个文件的起止时间（秒）
    offsets_by_file: Dict[str, Tuple[float, float]] = {}
    current_offset = 0.0
    for filename, meta in vfs.iter_scene_files():
        sid = meta.get("scene_id") or ""
        sname = meta.get("scene_name") or ""
        dur = None
        if sid and sid in scene_durations:
            dur = scene_durations[sid]
        elif sname and sname in scene_durations:
            dur = scene_durations[sname]
        if dur is None:
            # 未知时长：只展示 scene 名称，不推进 offset
            continue
        try:
            d = float(dur)
        except (TypeError, ValueError):
            continue
        if d <= 0:
            continue
        start = current_offset
        end = start + d
        current_offset = end
        offsets_by_file[filename] = (start, end)

    # 然后构造最终的 Workspace overview 文本
    parts: List[str] = []
    for name, content in vfs.files.items():
        line_count = content.count("\n")
        if not content.endswith("\n"):
            line_count += 1

        meta = vfs._scene_meta.get(name)
        suffix = ""
        if meta:
            scene_name = meta.get("scene_name")
            base = f"(scene: {scene_name})"
            if name in offsets_by_file:
                start, end = offsets_by_file[name]
                start_str = _format_time(start)
                end_str = _format_time(end)
                base = f"(scene: {scene_name}, durations: {start_str}~{end_str})"
            suffix = f"  {base}"

        parts.append(f"{name}  ({line_count} lines){suffix}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Tool JSON schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------

EDIT_TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in the workspace with their line counts.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the content of a file. Returns numbered lines. "
                "Optionally specify start_line / end_line to read a range."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file to read, e.g. 'variable_initialization.py' or 'subtitles.srt'.",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "First line number to read (1-based, inclusive). Omit to start from beginning.",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Last line number to read (1-based, inclusive). Omit to read to end.",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Edit a file by replacing an exact substring. "
                "old_string must appear exactly once in the file. "
                "Provide enough surrounding context (3-5 lines) to uniquely identify the location."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file to edit.",
                    },
                    "old_string": {
                        "type": "string",
                        "description": "The exact substring to find and replace. Must match exactly once.",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "The replacement string.",
                    },
                },
                "required": ["file_path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file with the given content. Use for adding new scenes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path for the new file, e.g. 'new_scene.py'.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full content of the new file.",
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file from the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file to delete.",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

EDIT_SYSTEM_PROMPT = """\
You are an expert Manim animation code editor. You have a virtual workspace that \
contains Python scene files (.py), a subtitle file (subtitles.srt), and a special \
order file (scene_order).

Each .py file corresponds to one animation scene (a Manim Scene subclass). \
The subtitles.srt file contains SRT-format subtitles synchronized with the animation.
The scene_order file controls scene concatenation order: one .py filename per line.
If some existing scene files are missing from scene_order, they are appended automatically at the end.

When available, the user message will also include **per-scene rendered durations** \
in seconds. Use these durations as a reference when adjusting animation pacing, \
scene complexity, or subtitle timing, but prefer consistency with the existing \
SRT timing unless the user explicitly asks to change it.

## Available Tools

- **list_files** — see all files and their line counts.
- **read_file** — read a file's content (with line numbers). You can specify a line range.
- **edit_file** — replace an exact substring in a file. The `old_string` must match \
exactly once. Include enough context (3-5 lines around the change) to make it unique.
- **create_file** — add a new scene file or other file.
- **delete_file** — remove a file.

## Workflow

1. Start by calling **list_files** to understand the workspace structure.
2. Use **read_file** to inspect the files you need to modify.
3. Use **edit_file** to make precise, targeted changes. You can call it multiple times.
4. After all edits are done, reply with a brief summary of what you changed.

## Important Rules

- Do NOT output the entire file content in edit_file's old_string/new_string unless \
absolutely necessary. Make small, surgical edits.
- Preserve existing indentation and code style.
- If you need to modify multiple parts of the same file, make separate edit_file calls.
- If edit_file returns an error (not found / ambiguous), read the file again and retry \
with more context.
- When editing subtitles.srt, keep the SRT numbering and timestamp format intact.
- You can change scene output order by editing scene_order (one .py filename per line).
- Always verify your understanding of the code before editing — read first, edit second.
"""


# ---------------------------------------------------------------------------
# EditAgent
# ---------------------------------------------------------------------------

class EditAgent(BaseAgent):
    """Coding-agent that edits Manim scenes and SRT subtitles via tool use."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        reasoning_tokens: Optional[float] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.3,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            reasoning_tokens=reasoning_tokens,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )
        self.temperature = temperature

    # ------------------------------------------------------------------

    @staticmethod
    def _prepare_conversation_history(
        conversation_history: Optional[List[Dict[str, Any]]],
        max_history_rounds: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Sanitize and trim history messages by recent user rounds."""
        if not conversation_history:
            return []

        allowed_roles = {"user", "assistant", "tool"}
        sanitized: List[Dict[str, Any]] = []
        for msg in conversation_history:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            if role not in allowed_roles:
                continue
            sanitized.append(msg)

        if not sanitized:
            return []

        rounds = int(max_history_rounds or 0)
        if rounds <= 0:
            return sanitized

        user_indexes = [idx for idx, m in enumerate(sanitized) if m.get("role") == "user"]
        if len(user_indexes) <= rounds:
            return sanitized

        start_idx = user_indexes[-rounds]
        return sanitized[start_idx:]

    def _build_context(
        self,
        manim_code: str,
        srt_content: str,
        user_instruction: str,
        scene_durations: Optional[Dict[str, float]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_history_rounds: Optional[int] = None,
    ) -> Tuple[VirtualFileSystem, List[Dict[str, Any]], str]:
        if not user_instruction or not user_instruction.strip():
            return VirtualFileSystem(), [], ""

        vfs = VirtualFileSystem()
        vfs.parse(manim_code, srt_content)

        file_overview = _build_workspace_overview_with_durations(vfs, scene_durations)

        user_message = (
            f"## Workspace overview\n```\n{file_overview}\n```\n\n"
            f"## User instruction\n{user_instruction}"
        )

        history_messages = self._prepare_conversation_history(
            conversation_history=conversation_history,
            max_history_rounds=max_history_rounds,
        )
        messages: List[Dict] = [{"role": "system", "content": EDIT_SYSTEM_PROMPT}]
        messages.extend(history_messages)
        messages.append({"role": "user", "content": user_message})
        return vfs, messages, user_instruction

    def _run_execute_core(
        self,
        manim_code: str,
        srt_content: str,
        user_instruction: str,
        scene_durations: Optional[Dict[str, float]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_history_rounds: Optional[int] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> EditResult:
        if not user_instruction or not user_instruction.strip():
            return EditResult(
                success=True,
                manim_code=manim_code,
                srt_content=srt_content,
                error_message=None,
                raw_llm_output=json.dumps(conversation_history or [], ensure_ascii=False, indent=2),
            )

        vfs, messages, _ = self._build_context(
            manim_code=manim_code,
            srt_content=srt_content,
            user_instruction=user_instruction,
            scene_durations=scene_durations,
            conversation_history=conversation_history,
            max_history_rounds=max_history_rounds,
        )

        def _tool_executor(name: str, args: dict) -> str:
            if name == "list_files":
                return vfs.list_files()
            if name == "read_file":
                return vfs.read_file(
                    args["file_path"],
                    start_line=args.get("start_line"),
                    end_line=args.get("end_line"),
                )
            if name == "edit_file":
                return vfs.edit_file(
                    args["file_path"], args["old_string"], args["new_string"]
                )
            if name == "create_file":
                return vfs.create_file(args["file_path"], args["content"])
            if name == "delete_file":
                return vfs.delete_file(args["file_path"])
            return f"Error: unknown tool '{name}'"

        try:
            final_text, full_messages = self._call_llm_with_tools(
                messages=messages,
                tools=EDIT_TOOLS,
                tool_executor=_tool_executor,
                temperature=self.temperature,
                max_iterations=15,
                on_event=on_event,
            )
        except Exception as e:
            self.logger.exception("EditAgent tool-use loop failed")
            return EditResult(
                success=False,
                manim_code=manim_code,
                srt_content=srt_content,
                error_message=str(e),
            )

        new_manim = vfs.rebuild_manim_code()
        new_srt = vfs.get_srt_content() or srt_content

        manim_changed = new_manim.strip() != manim_code.strip()
        srt_changed = new_srt.strip() != srt_content.strip()
        self.logger.info(
            "EditAgent result: manim_changed=%s, srt_changed=%s",
            manim_changed, srt_changed,
        )

        edit_summary = self._build_edit_summary(full_messages)

        return EditResult(
            success=True,
            manim_code=new_manim,
            srt_content=new_srt,
            error_message=None,
            raw_llm_output=json.dumps(full_messages, ensure_ascii=False, indent=2),
            manim_diff_preview=edit_summary if manim_changed else "(本次未对 MANIM 内容进行修改)",
            srt_diff_preview=final_text if srt_changed else "(本次未对 SRT 内容进行修改)",
        )

    def execute(
        self,
        manim_code: str,
        srt_content: str,
        user_instruction: str,
        scene_durations: Optional[Dict[str, float]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_history_rounds: Optional[int] = None,
    ) -> EditResult:
        return self._run_execute_core(
            manim_code=manim_code,
            srt_content=srt_content,
            user_instruction=user_instruction,
            scene_durations=scene_durations,
            conversation_history=conversation_history,
            max_history_rounds=max_history_rounds,
            on_event=None,
        )

    def execute_stream(
        self,
        manim_code: str,
        srt_content: str,
        user_instruction: str,
        scene_durations: Optional[Dict[str, float]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_history_rounds: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream edit events and finally yield {"type":"final_result","result":EditResult}."""
        buffered_events: List[Dict[str, Any]] = []

        def _on_event(event: Dict[str, Any]) -> None:
            buffered_events.append(event)

        result = self._run_execute_core(
            manim_code=manim_code,
            srt_content=srt_content,
            user_instruction=user_instruction,
            scene_durations=scene_durations,
            conversation_history=conversation_history,
            max_history_rounds=max_history_rounds,
            on_event=_on_event,
        )

        for event in buffered_events:
            yield event
        yield {"type": "final_result", "result": result}

    # ------------------------------------------------------------------

    @staticmethod
    def _build_edit_summary(messages: List[Dict]) -> str:
        """Extract a human-readable summary of all edit_file/create_file/delete_file calls."""
        edits: List[str] = []
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    fn = tc["function"]
                    name = fn["name"]
                    if name in ("edit_file", "create_file", "delete_file"):
                        try:
                            args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
                        except (json.JSONDecodeError, TypeError):
                            args = {}
                        fp = args.get("file_path", "?")
                        if name == "edit_file":
                            edits.append(f"edit: {fp}")
                        elif name == "create_file":
                            edits.append(f"create: {fp}")
                        elif name == "delete_file":
                            edits.append(f"delete: {fp}")

        final_reply = ""
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                final_reply = msg["content"]
                break

        parts: List[str] = []
        if edits:
            parts.append("Tool calls: " + ", ".join(edits))
        if final_reply:
            parts.append(final_reply)
        return "\n\n".join(parts) if parts else "(no edits)"
