"""
Edit pipeline: applies user edit instructions to existing Manim and SRT content.
Separate from the generation pipeline (pipeline.py). Uses EditAgent only.
"""
import logging
import time
from contextlib import nullcontext
from typing import Optional, Dict, Any, List, Iterator

from agents.edit_agent import EditAgent
from agents.manim_models import EditResult
from config import settings

try:
    from langfuse import get_client as get_langfuse_client, propagate_attributes
    _LANGFUSE_AVAILABLE = True
except ImportError:
    get_langfuse_client = None  # type: ignore[assignment]
    propagate_attributes = None  # type: ignore[assignment]
    _LANGFUSE_AVAILABLE = False


def _scrub_edit_output(result: EditResult) -> Dict[str, Any]:
    """Return a safe, compact representation of EditResult for Langfuse (no full code)."""
    return {
        "success": result.success,
        "error_message": result.error_message,
    }


class EditPipeline:
    """
    Pipeline for editing existing Manim code and SRT content by user instruction.
    Holds EditAgent; does not depend on the generation pipeline.
    """

    def __init__(self):
        self.config = settings
        self.logger = logging.getLogger("EditPipeline")
        self._ensure_logging_handlers()

        model = self.config.edit_model or self.config.reasoning_model
        api_key = self.config.edit_openrouter_api_key or self.config.openrouter_api_key
        base_url = self.config.edit_openrouter_base_url or self.config.openrouter_base_url
        self.edit_agent = EditAgent(
            api_key=api_key,
            base_url=base_url,
            model=model,
            reasoning_tokens=self.config.edit_reasoning_tokens,
            reasoning_effort=self.config.edit_reasoning_effort,
            max_tokens=self.config.edit_max_tokens,
            temperature=self.config.edit_temperature,
        )
        self.logger.info("EditPipeline initialized")

    def _ensure_logging_handlers(self) -> None:
        """Ensure EditPipeline logs propagate to the same pipeline.log as main Pipeline (root logger)."""
        if self.logger.level == logging.NOTSET:
            self.logger.setLevel(logging.INFO)

    @staticmethod
    def _resolve_session_id(
        langfuse_user_id: Optional[str],
        langfuse_session_id: Optional[str],
    ) -> Optional[str]:
        """Resolve a stable session id for edit tracing."""
        session = (langfuse_session_id or "").strip()
        if session:
            return session
        user_id = (langfuse_user_id or "").strip()
        if user_id:
            return f"edit-user-{user_id}"
        return None

    def _build_langfuse_contexts(
        self,
        instruction_preview: str,
        history_messages: int,
        max_history_rounds: Optional[int],
        langfuse_user_id: Optional[str],
        langfuse_session_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Build Langfuse contexts shared by edit() and edit_stream().
        Returns dict with keys: enabled, langfuse, attr_ctx, obs_input.
        """
        obs_input = {
            "instruction_preview": instruction_preview,
            "history_messages": history_messages,
            "max_history_rounds": (
                max_history_rounds
                if max_history_rounds is not None
                else getattr(self.config, "edit_chat_history_rounds", 8)
            ),
        }
        if not (self.config.langfuse_enabled and _LANGFUSE_AVAILABLE):
            return {"enabled": False, "langfuse": None, "attr_ctx": None, "obs_input": obs_input}

        langfuse = get_langfuse_client() if get_langfuse_client is not None else None
        if not langfuse:
            return {"enabled": False, "langfuse": None, "attr_ctx": None, "obs_input": obs_input}

        attr_ctx = None
        if propagate_attributes is not None:
            attr_kwargs: Dict[str, Any] = {}
            user_id = (langfuse_user_id or "").strip()
            if user_id:
                attr_kwargs["user_id"] = user_id
            session_id = self._resolve_session_id(langfuse_user_id, langfuse_session_id)
            if session_id:
                attr_kwargs["session_id"] = session_id
            if attr_kwargs:
                attr_ctx = propagate_attributes(**attr_kwargs)

        return {"enabled": True, "langfuse": langfuse, "attr_ctx": attr_ctx, "obs_input": obs_input}

    def edit(
        self,
        manim_code: str,
        srt_content: str,
        user_instruction: str,
        langfuse_user_id: Optional[str] = None,
        langfuse_session_id: Optional[str] = None,
        scene_durations: Optional[Dict[str, float]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_history_rounds: Optional[int] = None,
    ) -> EditResult:
        if manim_code:
            manim_code = manim_code.replace('\xa0', ' ')
        if srt_content:
            srt_content = srt_content.replace('\xa0', ' ')
        """
        Apply user edit instruction to the given Manim code and SRT content.
        Returns EditResult with modified manim_code and srt_content (or original on error).
        """
        start_time = time.time()
        instruction = user_instruction or ""
        instruction_preview = instruction[:200] + ("..." if len(instruction) > 200 else "")

        self.logger.info("Starting edit pipeline, instruction_preview=%s", instruction_preview or "(empty)")
        self.logger.info("Step: EditAgent.execute (manim_len=%d, srt_len=%d)", len(manim_code), len(srt_content))

        def _run_edit() -> EditResult:
            effective_rounds = (
                max_history_rounds
                if max_history_rounds is not None
                else getattr(self.config, "edit_chat_history_rounds", 8)
            )
            return self.edit_agent.execute(
                manim_code=manim_code,
                srt_content=srt_content,
                user_instruction=instruction,
                scene_durations=scene_durations,
                conversation_history=conversation_history,
                max_history_rounds=effective_rounds,
            )

        tracing = self._build_langfuse_contexts(
            instruction_preview=instruction_preview,
            history_messages=len(conversation_history or []),
            max_history_rounds=max_history_rounds,
            langfuse_user_id=langfuse_user_id,
            langfuse_session_id=langfuse_session_id,
        )

        if not tracing["enabled"]:
            self.logger.info("Langfuse disabled or unavailable, running edit without tracing")
            result = _run_edit()
            duration = time.time() - start_time
            self.logger.info("EditAgent.execute finished: success=%s", result.success)
            self.logger.info("Edit pipeline completed in %.2fs", duration)
            return result

        langfuse = tracing["langfuse"]
        attr_ctx = tracing["attr_ctx"]
        obs_input = tracing["obs_input"]
        try:
            with (attr_ctx or nullcontext()):
                with langfuse.start_as_current_observation(
                    as_type="span",
                    name="edit-pipeline",
                    input=obs_input,
                ) as obs:
                    result = _run_edit()
                    obs.update(input=obs_input)
                    obs.update(output=_scrub_edit_output(result))
            duration = time.time() - start_time
            self.logger.info("EditAgent.execute finished: success=%s", result.success)
            self.logger.info("Edit pipeline completed successfully in %.2fs", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error("Edit pipeline failed: %s", e)
            raise
        finally:
            if langfuse is not None:
                try:
                    langfuse.flush()
                except Exception:
                    self.logger.warning("Langfuse flush failed in edit()", exc_info=True)

    def edit_stream(
        self,
        manim_code: str,
        srt_content: str,
        user_instruction: str,
        langfuse_user_id: Optional[str] = None,
        langfuse_session_id: Optional[str] = None,
        scene_durations: Optional[Dict[str, float]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_history_rounds: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream events from EditAgent and end with final_result event."""
        start_time = time.time()
        instruction = user_instruction or ""
        instruction_preview = instruction[:200] + ("..." if len(instruction) > 200 else "")
        self.logger.info("Starting edit stream pipeline, instruction_preview=%s", instruction_preview or "(empty)")

        effective_rounds = (
            max_history_rounds
            if max_history_rounds is not None
            else getattr(self.config, "edit_chat_history_rounds", 8)
        )

        tracing = self._build_langfuse_contexts(
            instruction_preview=instruction_preview,
            history_messages=len(conversation_history or []),
            max_history_rounds=max_history_rounds,
            langfuse_user_id=langfuse_user_id,
            langfuse_session_id=langfuse_session_id,
        )
        langfuse = tracing["langfuse"]
        attr_ctx = tracing["attr_ctx"]
        obs_input = tracing["obs_input"]
        stream_result: Optional[EditResult] = None
        stream_error: Optional[str] = None
        buffered_events: List[Dict[str, Any]] = []

        try:
            if tracing["enabled"] and langfuse is not None:
                metadata: Dict[str, Any] = {}
                user_id = (langfuse_user_id or "").strip()
                if user_id:
                    metadata["user_id"] = user_id
                session_id = self._resolve_session_id(langfuse_user_id, langfuse_session_id)
                if session_id:
                    metadata["session_id"] = session_id

                # Consume the whole edit stream inside Langfuse "current observation"
                # context so that all nested LLM spans are linked to the same trace.
                # After the context is closed, we yield buffered events to Gradio.
                with (attr_ctx or nullcontext()):
                    with langfuse.start_as_current_observation(
                        as_type="span",
                        name="edit-pipeline",
                        input=obs_input,
                        metadata=metadata or None,
                    ) as obs:
                        stream = self.edit_agent.execute_stream(
                            manim_code=manim_code,
                            srt_content=srt_content,
                            user_instruction=instruction,
                            scene_durations=scene_durations,
                            conversation_history=conversation_history,
                            max_history_rounds=effective_rounds,
                        )
                        for event in stream:
                            buffered_events.append(event)
                            if event.get("type") == "final_result":
                                result = event.get("result")
                                if isinstance(result, EditResult):
                                    stream_result = result

                        obs.update(input=obs_input)
                        if stream_result is not None:
                            obs.update(output=_scrub_edit_output(stream_result))
                        elif stream_error:
                            obs.update(output={"success": False, "error_message": stream_error})
                        else:
                            obs.update(
                                output={"success": False, "error_message": "stream ended without final_result"}
                            )
            else:
                stream = self.edit_agent.execute_stream(
                    manim_code=manim_code,
                    srt_content=srt_content,
                    user_instruction=instruction,
                    scene_durations=scene_durations,
                    conversation_history=conversation_history,
                    max_history_rounds=effective_rounds,
                )
                for event in stream:
                    buffered_events.append(event)
                    if event.get("type") == "final_result":
                        result = event.get("result")
                        if isinstance(result, EditResult):
                            stream_result = result
        except Exception as e:
            stream_error = str(e)
            raise
        finally:
            duration = time.time() - start_time
            self.logger.info("Edit stream pipeline finished in %.2fs", duration)
            if langfuse is not None:
                try:
                    langfuse.flush()
                except Exception:
                    self.logger.warning("Langfuse flush failed in edit_stream()", exc_info=True)

        for event in buffered_events:
            yield event
