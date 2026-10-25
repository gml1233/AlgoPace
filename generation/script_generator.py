import logging
import time
import re
import json
import tempfile
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import requests

from pydantic import BaseModel, Field


class SRTSubtitle(BaseModel):
    """Single subtitle entry in SRT format"""
    sequence: int
    start_time: str  # Format: HH:MM:SS,mmm
    end_time: str    # Format: HH:MM:SS,mmm
    text: str


class ScriptResult(BaseModel):
    """Result of script generation"""
    success: bool
    script_path: Optional[str] = None
    srt_content: Optional[str] = None
    subtitles: List[SRTSubtitle] = Field(default_factory=list)
    total_duration: Optional[float] = None
    error_message: Optional[str] = None

    # Metadata
    generation_time: Optional[float] = None
    video_duration: Optional[float] = None
    model_used: str = "gemini-3.1-pro-preview"


class ScriptGenerator:
    """
    Script Generator: Analyzes silent animations and generates timestamped narration scripts
    using Gemini 2.5 Flash for multimodal video understanding.
    """

    def __init__(
        self,
        api_key: str,
        output_dir: Path,
        model: str = "gemini-3-pro-preview",
        temperature: float = 0.8,
        max_tokens: int = 4096,
        top_p: Optional[float] = None,
        max_retries: int = 3,
        timeout: int = 1800
    ):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.max_retries = max_retries
        self.timeout = timeout
        self.openrouter_url = "https://api.jiekou.ai/openai/chat/completions"

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)

    SCRIPT_GENERATION_PROMPT = """
You are an Educational Script Generator for STEM animations.

**TASK**: Watch the provided silent animation video and create a synchronized narration script in SRT (SubRip) format.

**TARGET LANGUAGE**: {target_language}

**VIDEO DURATION**: {video_duration_minutes:.1f}:{video_duration_seconds:05.2f} (minutes:seconds)

---

## PRIMARY OBJECTIVE
Write a **succinct, student-friendly narration** that explains the concept clearly and naturally. Speak to **why** things happen, **what to notice**, and the **reasoning that connects steps**, so the narration feels complete, not merely descriptive.

---

## FOCUS & BREVITY RULES (STRICT)
- **Only narrate when it adds understanding.** If a visual is self-explanatory or decorative, **omit** it.
- **One idea per subtitle**, **one sentence** per subtitle.
- **Word cap:** Prefer **10–14 words**, never exceed **18 words** in any subtitle.
- **Define a term once**, then use it consistently without re-defining.
- **Prefer “why/what to notice”** over “what moves where.”
- **Use causal links** (“because,” “so,” “therefore,” “which means”) to bridge steps.
- **Name roles, not looks.** Use function-driven labels (“velocity vector,” “spring constant k”), not colors/shapes—**unless color encodes meaning**, then state the meaning.
- **Avoid**: listing colors/shapes, camera moves, minor transitions, or stating the obvious.

---

## WORKFLOW BEFORE WRITING
1) **Skim once** to identify the learning objective and main phases.
2) **List key beats** where understanding could fail (definition, setup, transformation, result, takeaway).
3) **Write to those beats only**, using the brevity rules and causal connectors.
4) **Prune** any line that merely narrates motion without adding meaning.
5) **Completeness check**: Do you cover objective → setup/assumptions → core relation → transformation → result → concise takeaway?

---

## WHAT TO SAY (CONTENT PRIORITIES)
- **Introduction**: Start with a single, clear sentence introducing the concept and goal.
- **Definitions & symbols**: Introduce each new symbol/term once; explain its role or unit.
- **Assumptions**: State critical conditions briefly (e.g., “no friction,” “mass is constant”).
- **Relations**: Express the governing idea (e.g., “force causes acceleration,” “slope is rise over run”).
- **Transformations**: When the visual changes, say **why** it changes and **what that implies**.
- **Numbers & expressions**: Explain what a number/expression represents; avoid reading it verbatim unless essential.
- **Misconceptions**: Anticipate a likely confusion and clarify it in one short line, if timing allows.
- **Final takeaway**: End with a compact conclusion that reinforces the core idea.

---

## SRT FORMAT (MANDATORY)
- **TIMESTAMP FORMAT**: exactly `HH:MM:SS,mmm` with a **comma** before milliseconds.
- **Each subtitle** is a complete sentence, 1 line, **3–6 seconds** long.
- **Pause** between subtitles: **0,5–1,0 seconds**.
- **Sequence numbers** start at 1 and increment by 1.

**CRITICAL: ALWAYS USE COMMA (,) NOT PERIOD (.) BETWEEN SECONDS AND MILLISECONDS**
- ✅ 00:00:03,500
- ❌ 00:00:03.500

**COMMON MISTAKES TO AVOID**
- Missing leading zeros (✅ 00:00:03,500)
- Not 3 digits of milliseconds (✅ 00:00:03,500)
- Durations shorter than 3 seconds
- Describing everything on screen
- Multiple sentences in one subtitle

---

## TIMING GUIDELINES
- Begin narration **slightly early**: start 0,5–1,0 s before the first key visual.
- **First subtitle must be an introduction sentence to the concept**, beginning at **00:00:00,000**.
- Keep each subtitle **3–6 s**; end slightly **before** a visual transition.
- Maintain a natural rhythm; use simple syntax and active voice.
- You always have to start with something from **00:00:00,000**.

---

## STYLE
- **Clear, conversational, {target_language}**, present tense, active voice.
- Prefer concrete verbs and simple syntax.
- Use gentle signposts sparingly (“First…”, “Now…”, “So…”).
- When numbers/symbols appear, explain **their role or meaning**, not their appearance.

---

## OUTPUT REQUIREMENTS
- Output **ONLY** the SRT content wrapped in `<srt>` tags.
- No commentary outside the `<srt>` block.

---

## MINI EXAMPLE (brevity-focused)
<srt>
1
00:00:00,000 --> 00:00:04,000
We’re exploring how slope measures a line’s steepness.

2
00:00:04,800 --> 00:00:09,200
Slope equals rise over run: vertical change divided by horizontal change.

3
00:00:09,900 --> 00:00:13,500
Notice the rise marks how far the line increases vertically.

4
00:00:14,200 --> 00:00:18,200
The run shows the horizontal distance you move to compare points.

5
00:00:18,900 --> 00:00:23,000
Because the ratio stays constant, slope is identical anywhere on the line.
</srt>
"""

    def execute(self, video_path: str, target_language: str = "English", knowledge_content: str = None) -> ScriptResult:
        """
        Generate narration script for a silent animation video

        Args:
            video_path: Path to the silent animation video file
            target_language: Target language for narration (English, Chinese, Spanish, Vietnamese)
            knowledge_content: Optional knowledge document content to use as reference for script generation

        Returns:
            ScriptResult with generated SRT content and metadata
        """
        start_time = time.time()
        self.logger.info(f"Starting script generation for: {video_path}")
        if knowledge_content:
            self.logger.info(f"Using knowledge document ({len(knowledge_content)} characters)")

        try:
            # Validate video file
            video_file = Path(video_path)
            if not video_file.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            # Get video duration for context
            video_duration = self._get_video_duration(video_file)
            self.logger.info(f"Video duration: {video_duration:.2f} seconds")

            # Generate script using Gemini
            srt_content = self._generate_script_with_gemini(video_file, target_language, video_duration, knowledge_content)

            if srt_content:
                # Parse and validate SRT content
                subtitles = self._parse_srt_content(srt_content)
                script_duration = self._calculate_script_duration(subtitles)

                # Save script to file
                script_path = self._save_script(srt_content, video_file.stem)

                generation_time = time.time() - start_time
                self.logger.info(f"Script generation completed in {generation_time:.2f}s")
                self.logger.info(f"Generated {len(subtitles)} subtitles")
                self.logger.info(f"Script duration: {script_duration:.2f}s")

                return ScriptResult(
                    success=True,
                    script_path=str(script_path),
                    srt_content=srt_content,
                    subtitles=subtitles,
                    total_duration=script_duration,
                    generation_time=generation_time,
                    video_duration=video_duration,
                    model_used=self.model
                )
            else:
                raise ValueError("Failed to generate script content")

        except Exception as e:
            self.logger.error(f"Script generation failed: {e}")
            return ScriptResult(
                success=False,
                error_message=str(e),
                generation_time=time.time() - start_time,
                model_used=self.model
            )

    def _generate_script_with_gemini(self, video_file: Path, target_language: str = "English", video_duration: float = 0.0, knowledge_content: str = None) -> Optional[str]:
        """Generate script using OpenRouter's Gemini API"""

        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Processing video with OpenRouter (attempt {attempt + 1})")

                # Read video file and convert to base64
                self.logger.info("Reading video file...")
                with open(video_file, "rb") as f:
                    video_data = f.read()
                    video_base64 = base64.b64encode(video_data).decode('utf-8')

                # Get MIME type based on file extension
                video_mime_type = self._get_mime_type(video_file)

                self.logger.info(f"Video file read successfully: {video_file.name}")

                # Generate script with OpenRouter
                self.logger.info(f"Generating script with {self.model} in {target_language}")
                video_duration_minutes = int(video_duration // 60)
                video_duration_seconds = video_duration % 60
                prompt = self.SCRIPT_GENERATION_PROMPT.format(
                    target_language=target_language,
                    video_duration=video_duration,
                    video_duration_minutes=video_duration_minutes,
                    video_duration_seconds=video_duration_seconds
                )

                # If knowledge document is provided, append it to the prompt
                if knowledge_content:
                    knowledge_prompt = f"""

---

## KNOWLEDGE DOCUMENT (PRIMARY REFERENCE)
The following is a detailed knowledge document about this concept. You MUST base your narration strictly on this document:

{knowledge_content}

## IMPORTANT INSTRUCTIONS FOR USING KNOWLEDGE DOCUMENT:
1. Your narration must follow the logical flow and steps described in the knowledge document.
2. Use the exact terminology, explanations, and examples from the document.
3. Cover all key points mentioned in the document without adding unrelated content.
4. The narration should sound like a teacher explaining the content from this document.
5. Prioritize clarity and accuracy based on the document over creative interpretation.
"""
                    prompt = prompt + knowledge_prompt
                    self.logger.info("Knowledge document appended to prompt")

                # Prepare OpenRouter API request
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{video_mime_type};base64,{video_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
                if self.top_p is not None:
                    payload["top_p"] = self.top_p

                # Make API request (optionally via Langfuse OpenAI wrapper for tracing)
                self.logger.info("Sending request to OpenRouter...")
                use_langfuse = False
                try:
                    from config import settings
                    use_langfuse = getattr(settings, "langfuse_enabled", False) and settings.langfuse_enabled
                except Exception:
                    pass

                if use_langfuse:
                    try:
                        from langfuse.openai import OpenAI
                        base_url = self.openrouter_url.replace("/chat/completions", "").rstrip("/")
                        client = OpenAI(base_url=base_url, api_key=self.api_key)
                        create_kw = {
                            "model": self.model,
                            "messages": payload["messages"],
                            "temperature": self.temperature,
                            "max_tokens": self.max_tokens,
                            "timeout": float(self.timeout),
                        }
                        if self.top_p is not None:
                            create_kw["top_p"] = self.top_p
                        response = client.chat.completions.create(**create_kw)
                        script_content = (response.choices[0].message.content or "").strip()
                        self.logger.info("Received script content from OpenRouter (via Langfuse)")
                    except ImportError:
                        use_langfuse = False
                    except Exception as e:
                        self.logger.warning(f"Langfuse OpenAI call failed, falling back to requests: {e}")
                        use_langfuse = False

                if not use_langfuse:
                    response = requests.post(
                        self.openrouter_url,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    if response.status_code != 200:
                        error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                        self.logger.error(error_msg)
                        raise ValueError(error_msg)
                    response_data = response.json()
                    script_content = response_data["choices"][0]["message"]["content"]

                if not use_langfuse:
                    self.logger.info("Received script content from OpenRouter")

                # Extract SRT content from <srt> tags
                srt_content = self._extract_srt_from_response(script_content)

                if srt_content:
                    return srt_content
                else:
                    self.logger.warning(f"No SRT content found in response (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        continue
                    else:
                        raise ValueError("Could not extract SRT content from OpenRouter response")

            except Exception as e:
                self.logger.warning(f"OpenRouter API call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

        return None

    def _get_mime_type(self, video_file: Path) -> str:
        """Get MIME type based on file extension"""
        extension = video_file.suffix.lower()
        mime_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
            '.wmv': 'video/x-ms-wmv',
            '.mpeg': 'video/mpeg',
            '.mpg': 'video/mpeg'
        }
        return mime_types.get(extension, 'video/mp4')

    def _extract_srt_from_response(self, response: str) -> Optional[str]:
        """Extract SRT content from response wrapped in <srt> tags"""

        # Method 1: Extract from <srt>...</srt> tags
        srt_pattern = r'<srt>(.*?)</srt>'
        matches = re.findall(srt_pattern, response, re.DOTALL | re.IGNORECASE)

        if matches:
            srt_content = matches[0].strip()
            self.logger.info("Extracted SRT content from <srt> tags")
            return srt_content

        # Method 2: Look for SRT-like content without tags
        srt_lines = []
        lines = response.strip().split('\n')

        current_subtitle = []
        for line in lines:
            line = line.strip()
            if not line:
                if current_subtitle:
                    srt_lines.extend(current_subtitle)
                    srt_lines.append("")  # Empty line between subtitles
                    current_subtitle = []
                continue

            # Check if line looks like SRT content
            if (line.isdigit() or  # Sequence number
                '-->' in line or    # Timestamp
                any(char in line for char in '.!?')):  # Text content
                current_subtitle.append(line)

        if current_subtitle:
            srt_lines.extend(current_subtitle)

        if srt_lines:
            srt_content = '\n'.join(srt_lines).strip()
            self.logger.info("Extracted SRT content without tags")
            return srt_content

        self.logger.warning("No SRT content found in response")
        return None

    def _parse_srt_content(self, srt_content: str) -> List[SRTSubtitle]:
        """Parse SRT content into structured subtitles"""

        subtitles = []
        lines = srt_content.strip().split('\n')

        i = 0
        while i < len(lines):
            try:
                # Skip empty lines
                if not lines[i].strip():
                    i += 1
                    continue

                # Parse sequence number (handle "12. timestamp" or just "12")
                sequence_line = lines[i].strip()
                
                # Check if sequence and timestamp are on same line (e.g., "12. 00:00:00,000 --> 00:00:05,000")
                if '-->' in sequence_line:
                    parts = sequence_line.split('.')
                    if len(parts) >= 2 and parts[0].strip().isdigit():
                        sequence = int(parts[0].strip())
                        timestamp_line = '.'.join(parts[1:]).strip()
                        
                        try:
                            start_time, end_time = [t.strip() for t in timestamp_line.split('-->')]
                        except ValueError:
                            self.logger.warning(f"Invalid timestamp format: {timestamp_line}")
                            i += 1
                            continue
                        
                        i += 1
                        
                        # Parse text lines
                        text_lines = []
                        while i < len(lines) and lines[i].strip() and not lines[i].strip().split('.')[0].isdigit() and '-->' not in lines[i]:
                            text_lines.append(lines[i].strip())
                            i += 1
                        
                        if text_lines:
                            text = ' '.join(text_lines)
                            subtitle = SRTSubtitle(
                                sequence=sequence,
                                start_time=start_time,
                                end_time=end_time,
                                text=text
                            )
                            subtitles.append(subtitle)
                        continue
                
                # Normal parsing: sequence on its own line
                if not sequence_line.isdigit():
                    self.logger.warning(f"Expected sequence number, got: {sequence_line}")
                    i += 1
                    continue

                sequence = int(sequence_line)
                i += 1

                # Parse timestamp line
                if i >= len(lines):
                    break

                timestamp_line = lines[i].strip()
                if '-->' not in timestamp_line:
                    self.logger.warning(f"Expected timestamp line, got: {timestamp_line}")
                    i += 1
                    continue

                try:
                    start_time, end_time = [t.strip() for t in timestamp_line.split('-->')]
                except ValueError:
                    self.logger.warning(f"Invalid timestamp format: {timestamp_line}")
                    i += 1
                    continue

                i += 1

                # Parse text lines (until empty line or next sequence)
                text_lines = []
                while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
                    text_lines.append(lines[i].strip())
                    i += 1

                if text_lines:
                    text = ' '.join(text_lines)

                    subtitle = SRTSubtitle(
                        sequence=sequence,
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    )
                    subtitles.append(subtitle)

            except Exception as e:
                self.logger.warning(f"Error parsing subtitle at line {i}: {e}")
                i += 1

        self.logger.info(f"Parsed {len(subtitles)} subtitles from SRT content")
        return subtitles

    def _normalize_timestamp(self, timestamp: str) -> str:
        """Normalize malformed timestamps to proper HH:MM:SS,mmm format"""
        
        timestamp = timestamp.strip()
        timestamp = timestamp.replace('.', ',').replace(':', ',')
        parts = timestamp.split(',')
        
        if len(parts) == 3:
            minutes, seconds, milliseconds = parts
            hours = "00"
        elif len(parts) == 4:
            hours, minutes, seconds, milliseconds = parts
        else:
            raise ValueError(f"Cannot parse timestamp: {timestamp}")
        
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
        milliseconds = int(milliseconds)
        
        if minutes >= 60:
            hours += minutes // 60
            minutes = minutes % 60
        
        if seconds >= 60:
            minutes += seconds // 60
            seconds = seconds % 60
        
        if milliseconds >= 1000:
            seconds += milliseconds // 1000
            milliseconds = milliseconds % 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def _calculate_script_duration(self, subtitles: List[SRTSubtitle]) -> float:
        """Calculate total duration of the script in seconds"""

        if not subtitles:
            return 0.0

        try:
            # Parse the end time of the last subtitle
            last_subtitle = max(subtitles, key=lambda s: s.sequence)
            end_time_str = self._normalize_timestamp(last_subtitle.end_time)

            # Convert HH:MM:SS,mmm to seconds
            time_parts = end_time_str.replace(',', ':').split(':')
            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds = int(time_parts[2])
            milliseconds = int(time_parts[3]) if len(time_parts) > 3 else 0

            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            return total_seconds

        except Exception as e:
            self.logger.warning(f"Error calculating script duration: {e}")
            return 0.0

    def _save_script(self, srt_content: str, video_stem: str) -> Path:
        """Save SRT script to file with normalized timestamps"""

        normalized_content = self._normalize_srt_timestamps(srt_content)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{video_stem}_script_{timestamp}.srt"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(normalized_content)

        self.logger.info(f"Script saved to: {filepath}")
        return filepath

    def _normalize_srt_timestamps(self, srt_content: str) -> str:
        """Normalize all timestamps in SRT content"""
        
        lines = srt_content.split('\n')
        normalized_lines = []
        
        for line in lines:
            if '-->' in line:
                try:
                    parts = line.split('-->')
                    if len(parts) == 2:
                        start = self._normalize_timestamp(parts[0])
                        end = self._normalize_timestamp(parts[1])
                        normalized_lines.append(f"{start} --> {end}")
                    else:
                        normalized_lines.append(line)
                except Exception as e:
                    self.logger.warning(f"Could not normalize timestamp line: {line} - {e}")
                    normalized_lines.append(line)
            else:
                normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)

    def _get_video_duration(self, video_file: Path) -> float:
        """Get video duration using ffprobe or return default"""

        try:
            import subprocess

            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "default=nokey=1:noprint_wrappers=1",
                "-show_entries", "format=duration",
                str(video_file)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )

            if result.returncode == 0:
                duration_str = result.stdout.strip()
                return float(duration_str)
            else:
                self.logger.warning(f"ffprobe failed: {result.stderr}")
                return 120.0  # Default duration

        except Exception as e:
            self.logger.warning(f"Could not get video duration: {e}")
            return 120.0  # Default duration

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about script generation performance"""
        return {
            "model_used": self.model,
            "temperature": self.temperature,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "output_dir": str(self.output_dir)
        }