from abc import ABC, abstractmethod
import requests
import logging
import time
import json
import re
from typing import Optional, Dict, Any, List, Tuple, Callable

# Langfuse 可选：仅在配置启用时使用 langfuse.openai 包装器记录 LLM 调用
def _langfuse_openai_client(base_url: str, api_key: str):
    from langfuse.openai import OpenAI
    return OpenAI(base_url=base_url, api_key=api_key)


class BaseAgent(ABC):
    """Base class for all AI agents using OpenRouter"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        reasoning_tokens: Optional[float] = None,
        reasoning_effort: Optional[str] = None,
        max_tokens: int = 8192,
        top_p: Optional[float] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.reasoning_tokens = reasoning_tokens
        self.reasoning_effort = reasoning_effort
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.logger = logging.getLogger(self.__class__.__name__)
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def _call_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 1.0,
        max_retries: int = 3,
        json_mode: bool = False,
    ) -> str:
        """Call LLM with retry logic and error handling using HTTPS API.
        When Langfuse is enabled (config), uses langfuse.openai OpenAI client for automatic tracing.
        """
        use_langfuse = False
        try:
            from config import settings
            use_langfuse = getattr(settings, "langfuse_enabled", False) and settings.langfuse_enabled
        except Exception:
            pass

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        for attempt in range(max_retries):
            try:
                if use_langfuse:
                    try:
                        client = _langfuse_openai_client(self.base_url, self.api_key)
                        kwargs = {
                            "model": self.model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": self.max_tokens,
                            "timeout": 300.0,
                        }
                        if self.top_p is not None:
                            kwargs["top_p"] = self.top_p
                        extra = {}
                        if self.reasoning_tokens is not None or self.reasoning_effort is not None:
                            extra["reasoning"] = {"enabled": True}
                            if self.reasoning_tokens is not None:
                                extra["reasoning"]["max_tokens"] = int(self.reasoning_tokens)
                            if self.reasoning_effort is not None:
                                extra["reasoning"]["effort"] = self.reasoning_effort
                            # When thinking is enabled, force temperature to 1.0 to avoid 400 Bad Request
                            kwargs["temperature"] = 1.0
                        if json_mode:
                            extra["response_format"] = {"type": "json_object"}
                        if extra:
                            kwargs["extra_body"] = extra
                        response = client.chat.completions.create(**kwargs)
                        content = response.choices[0].message.content or ""
                        if getattr(response, "usage", None):
                            u = response.usage
                            self.prompt_tokens += getattr(u, "prompt_tokens", 0) or 0
                            self.completion_tokens += getattr(u, "completion_tokens", 0) or 0
                            self.total_tokens += getattr(u, "total_tokens", 0) or 0
                        self.logger.info(f"LLM call successful (attempt {attempt + 1})")
                        return content
                    except ImportError:
                        use_langfuse = False
                        # fall through to requests path

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": self.max_tokens,
                }
                if self.top_p is not None:
                    payload["top_p"] = self.top_p
                
                if self.reasoning_tokens is not None or self.reasoning_effort is not None:
                    payload["reasoning"] = {"enabled": True}
                    if self.reasoning_tokens is not None:
                        payload["reasoning"]["max_tokens"] = int(self.reasoning_tokens)
                    if self.reasoning_effort is not None:
                        payload["reasoning"]["effort"] = self.reasoning_effort
                    # When thinking is enabled, force temperature to 1.0 to avoid 400 Bad Request
                    payload["temperature"] = 1.0
                    
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}

                url = f"{self.base_url}/chat/completions"
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=300  # 5 minutes for thinking models
                )
                response.raise_for_status()
                response_data = response.json()

                if "usage" in response_data:
                    self.prompt_tokens += response_data["usage"].get("prompt_tokens", 0)
                    self.completion_tokens += response_data["usage"].get("completion_tokens", 0)
                    self.total_tokens += response_data["usage"].get("total_tokens", 0)

                content = response_data["choices"][0]["message"]["content"]
                self.logger.info(f"LLM call successful (attempt {attempt + 1})")
                return content

            except Exception as e:
                self.logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 2)
                    self.logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise Exception(
                        f"LLM call failed after {max_retries} attempts: {e}"
                    )

    def _call_llm_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_executor: Callable[[str, dict], str],
        temperature: float = 1.0,
        max_iterations: int = 15,
        max_retries_per_call: int = 3,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Run a full agent loop: call LLM with tools, execute tool_calls, repeat.

        Args:
            messages: Initial message list (mutated in-place with each turn).
            tools: OpenAI function-calling tool definitions.
            tool_executor: ``(name, arguments_dict) -> result_string`` callback.
            temperature: Sampling temperature.
            max_iterations: Safety cap on LLM round-trips.
            max_retries_per_call: Retries for a single HTTP/SDK call on transient errors.

        Returns:
            ``(final_text, messages)`` where *final_text* is the assistant's last
            text reply and *messages* is the full conversation history.
        """
        use_langfuse = False
        try:
            from config import settings
            use_langfuse = getattr(settings, "langfuse_enabled", False) and settings.langfuse_enabled
        except Exception:
            pass

        client = None
        if use_langfuse:
            try:
                client = _langfuse_openai_client(self.base_url, self.api_key)
            except ImportError:
                use_langfuse = False

        final_text = ""

        for iteration in range(max_iterations):
            self.logger.info(f"Agent loop iteration {iteration + 1}/{max_iterations}")

            assistant_msg = self._do_tool_llm_call(
                messages, tools, temperature, max_retries_per_call,
                use_langfuse, client, on_event=on_event,
            )

            messages.append(assistant_msg)
            if on_event is not None:
                on_event({"type": "assistant_message", "message": assistant_msg})

            tool_calls = assistant_msg.get("tool_calls")
            if not tool_calls:
                final_text = assistant_msg.get("content") or ""
                self.logger.info("Agent loop finished (text reply received)")
                break

            for tc in tool_calls:
                fn = tc["function"]
                fn_name = fn["name"]
                try:
                    fn_args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
                except (json.JSONDecodeError, TypeError):
                    fn_args = {}

                self.logger.info(f"Executing tool: {fn_name}")
                try:
                    result_str = tool_executor(fn_name, fn_args)
                except Exception as exc:
                    result_str = f"Error executing {fn_name}: {exc}"
                    self.logger.warning(result_str)

                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str,
                }
                messages.append(tool_msg)
                if on_event is not None:
                    on_event(
                        {
                            "type": "tool_result",
                            "tool_call_id": tc["id"],
                            "tool_name": fn_name,
                            "content": result_str,
                            "message": tool_msg,
                        }
                    )
        else:
            self.logger.warning("Agent loop reached max iterations, stopping")

        return final_text, messages

    # ------------------------------------------------------------------
    # Internal helper: single LLM call with tools (supports both paths)
    # ------------------------------------------------------------------
    def _do_tool_llm_call(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float,
        max_retries: int,
        use_langfuse: bool,
        client: Any,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Make one chat-completion call and return the assistant message dict."""

        for attempt in range(max_retries):
            try:
                if use_langfuse and client is not None:
                    return self._tool_call_via_sdk(
                        client, messages, tools, temperature, on_event=on_event
                    )
                return self._tool_call_via_requests(
                    messages, tools, temperature, on_event=on_event
                )
            except Exception as e:
                self.logger.warning(f"Tool LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 2)
                    self.logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise

    def _tool_call_via_sdk(
        self, client, messages, tools, temperature, on_event: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Call LLM via langfuse-wrapped OpenAI SDK."""
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "timeout": 300.0,
        }
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p

        # 使用流式，统一解析 reasoning/content/tool_calls 增量。
        kwargs["stream"] = True
        stream = client.chat.completions.create(**kwargs)
        assistant_msg = self._consume_stream(
            stream=stream,
            on_event=on_event,
            usage_from_chunk=True,
        )
        return assistant_msg

    def _tool_call_via_requests(
        self, messages, tools, temperature, on_event: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Call LLM via raw HTTP requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        if self.reasoning_tokens is not None or self.reasoning_effort is not None:
            payload["reasoning"] = {"enabled": True}
            if self.reasoning_tokens is not None:
                payload["reasoning"]["max_tokens"] = int(self.reasoning_tokens)
            if self.reasoning_effort is not None:
                payload["reasoning"]["effort"] = self.reasoning_effort
            payload["temperature"] = 1.0

        url = f"{self.base_url}/chat/completions"
        resp = requests.post(url, headers=headers, json=payload, timeout=300, stream=True)
        resp.raise_for_status()
        try:
            assistant_msg = self._consume_sse_stream(resp.iter_lines(decode_unicode=True), on_event=on_event)
        finally:
            resp.close()
        return assistant_msg

    @staticmethod
    def _to_plain_dict(obj: Any) -> Dict[str, Any]:
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
        return {}

    @staticmethod
    def _append_if_text(chunks: List[str], value: Any) -> None:
        if isinstance(value, str) and value:
            chunks.append(value)

    @staticmethod
    def _extract_think_segments(text: str) -> Tuple[str, str]:
        if not text:
            return "", ""
        think_blocks = re.findall(r"<think>(.*?)</think>", text, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        reasoning = "\n".join(block.strip() for block in think_blocks if block and block.strip()).strip()
        return cleaned.strip(), reasoning

    def _accumulate_delta(
        self,
        state: Dict[str, Any],
        delta: Dict[str, Any],
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        content_delta = delta.get("content")
        if isinstance(content_delta, str) and content_delta:
            state["content_parts"].append(content_delta)
            if on_event is not None:
                on_event({"type": "assistant_content_delta", "delta": content_delta})

        for key in ("reasoning", "reasoning_content", "thinking", "reasoning_text"):
            rv = delta.get(key)
            if isinstance(rv, str) and rv:
                state["reasoning_parts"].append(rv)
                if on_event is not None:
                    on_event({"type": "reasoning_delta", "delta": rv, "source": key})

        tool_calls = delta.get("tool_calls") or []
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    tc = self._to_plain_dict(tc)
                index = tc.get("index")
                if index is None:
                    index = len(state["tool_calls"])
                try:
                    index = int(index)
                except (TypeError, ValueError):
                    index = len(state["tool_calls"])
                while len(state["tool_calls"]) <= index:
                    state["tool_calls"].append(
                        {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                    )
                slot = state["tool_calls"][index]

                tc_id = tc.get("id")
                if isinstance(tc_id, str) and tc_id:
                    slot["id"] = tc_id
                tc_type = tc.get("type")
                if isinstance(tc_type, str) and tc_type:
                    slot["type"] = tc_type

                fn = tc.get("function") or {}
                if not isinstance(fn, dict):
                    fn = self._to_plain_dict(fn)
                fn_name = fn.get("name")
                if isinstance(fn_name, str) and fn_name:
                    slot["function"]["name"] = fn_name
                fn_args_delta = fn.get("arguments")
                if isinstance(fn_args_delta, str) and fn_args_delta:
                    slot["function"]["arguments"] = slot["function"].get("arguments", "") + fn_args_delta
                    if on_event is not None:
                        on_event(
                            {
                                "type": "tool_call_delta",
                                "index": index,
                                "tool_call_id": slot.get("id"),
                                "tool_name": slot["function"].get("name"),
                                "arguments_delta": fn_args_delta,
                                "arguments": slot["function"].get("arguments", ""),
                            }
                        )

    def _finalize_stream_state(self, state: Dict[str, Any], on_event: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        content = "".join(state["content_parts"])
        reasoning = "".join(state["reasoning_parts"]).strip()
        cleaned_content, think_reasoning = self._extract_think_segments(content)
        if think_reasoning:
            reasoning = (reasoning + "\n\n" + think_reasoning).strip() if reasoning else think_reasoning

        assistant_msg: Dict[str, Any] = {"role": "assistant", "content": cleaned_content}
        finalized_tool_calls = []
        for tc in state["tool_calls"]:
            fn = tc.get("function", {})
            if not isinstance(fn, dict):
                continue
            if not fn.get("name") and not fn.get("arguments"):
                continue
            if not tc.get("id"):
                tc["id"] = f"tool_call_{len(finalized_tool_calls)}"
            finalized_tool_calls.append(tc)
        if finalized_tool_calls:
            assistant_msg["tool_calls"] = finalized_tool_calls
        if reasoning:
            assistant_msg["reasoning_content"] = reasoning
        if on_event is not None:
            on_event({"type": "assistant_message_final", "message": assistant_msg})
        return assistant_msg

    def _consume_stream(
        self,
        stream: Any,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
        usage_from_chunk: bool = False,
    ) -> Dict[str, Any]:
        state: Dict[str, Any] = {"content_parts": [], "reasoning_parts": [], "tool_calls": []}
        for chunk in stream:
            chunk_dict = self._to_plain_dict(chunk)
            if usage_from_chunk:
                usage = chunk_dict.get("usage")
                if isinstance(usage, dict):
                    self.prompt_tokens += usage.get("prompt_tokens", 0) or 0
                    self.completion_tokens += usage.get("completion_tokens", 0) or 0
                    self.total_tokens += usage.get("total_tokens", 0) or 0
            choices = chunk_dict.get("choices") or []
            if not choices:
                continue
            choice = choices[0] or {}
            if not isinstance(choice, dict):
                choice = self._to_plain_dict(choice)
            delta = choice.get("delta") or {}
            if not isinstance(delta, dict):
                delta = self._to_plain_dict(delta)
            self._accumulate_delta(state, delta, on_event=on_event)

            finish_reason = choice.get("finish_reason")
            if finish_reason and on_event is not None:
                on_event({"type": "assistant_finish", "finish_reason": finish_reason})
        return self._finalize_stream_state(state, on_event=on_event)

    def _consume_sse_stream(
        self,
        lines: Any,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        state: Dict[str, Any] = {"content_parts": [], "reasoning_parts": [], "tool_calls": []}
        for raw_line in lines:
            if raw_line is None:
                continue
            line = raw_line.strip()
            if not line or not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                payload = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            usage = payload.get("usage")
            if isinstance(usage, dict):
                self.prompt_tokens += usage.get("prompt_tokens", 0) or 0
                self.completion_tokens += usage.get("completion_tokens", 0) or 0
                self.total_tokens += usage.get("total_tokens", 0) or 0

            choices = payload.get("choices") or []
            if not choices:
                continue
            choice = choices[0] or {}
            delta = choice.get("delta") or {}
            self._accumulate_delta(state, delta, on_event=on_event)

            finish_reason = choice.get("finish_reason")
            if finish_reason and on_event is not None:
                on_event({"type": "assistant_finish", "finish_reason": finish_reason})

        return self._finalize_stream_state(state, on_event=on_event)

    # ------------------------------------------------------------------
    # Helpers to normalise SDK / raw response into a plain dict
    # ------------------------------------------------------------------
    def _track_usage_from_sdk(self, response) -> None:
        if getattr(response, "usage", None):
            u = response.usage
            self.prompt_tokens += getattr(u, "prompt_tokens", 0) or 0
            self.completion_tokens += getattr(u, "completion_tokens", 0) or 0
            self.total_tokens += getattr(u, "total_tokens", 0) or 0

    @staticmethod
    def _sdk_message_to_dict(msg) -> Dict[str, Any]:
        """Convert an OpenAI SDK ChatCompletionMessage to a plain dict."""
        d: Dict[str, Any] = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            d["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        return d

    @staticmethod
    def _raw_message_to_dict(msg: dict) -> Dict[str, Any]:
        """Normalise a raw JSON message dict from the API response."""
        d: Dict[str, Any] = {"role": "assistant", "content": msg.get("content")}
        if msg.get("tool_calls"):
            d["tool_calls"] = msg["tool_calls"]
        return d

    def _call_llm_structured(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 1.0,
        max_retries: int = 3,
    ) -> Dict[Any, Any]:
        """Call LLM and return parsed JSON response"""

        response = self._call_llm(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            max_retries=max_retries,
            json_mode=True,
        )

        # Sanitize JSON output before parsing
        sanitized_response = self._sanitize_json_output(response)

        try:
            import json_repair
            return json_repair.loads(sanitized_response)
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response with json_repair: {e}")
            raise ValueError(f"Invalid JSON response from LLM (even after repair): {response[:200]}...")

    def get_token_usage(self) -> Dict[str, int]:
        """Return token usage statistics"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

    def _sanitize_json_output(self, text: str) -> str:
        """Remove ```json ``` code blocks and fix invalid escape sequences from LLM output"""
        # First try to extract JSON from complete ```json ... ``` code blocks
        json_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        match = re.search(json_block_pattern, text, flags=re.IGNORECASE)
        if match:
            sanitized = match.group(1).strip()
        else:
            # No complete code block found, try to remove just the opening ```json
            sanitized = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE)
            # Also remove trailing ``` if present
            sanitized = re.sub(r'```\s*$', '', sanitized)
        
        # Fix invalid escape sequences
        # Replace invalid backslash escapes with double backslash
        # Valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
        def fix_invalid_escapes(match):
            char = match.group(1)
            if char in '"\\/bfnrtu':
                return match.group(0)  # Valid escape, keep as is
            else:
                return '\\' + char  # Invalid escape, escape the backslash
        
        # Match backslash followed by any character
        sanitized = re.sub(r'\\(.)', fix_invalid_escapes, sanitized)
        
        # Additional cleanup: remove any remaining problematic characters
        # Remove control characters except \n, \r, \t
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        return sanitized.strip()

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the agent's main task - to be implemented by subclasses"""
        pass
