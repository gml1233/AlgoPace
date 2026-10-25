import subprocess
import tempfile
import logging
import time
import re
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import json


@dataclass
class RenderResult:
    """Result of a Manim render operation"""
    success: bool
    video_path: Optional[str] = None
    error_message: Optional[str] = None
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    render_time: Optional[float] = None
    subtitle_path: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class ManimRenderer:
    """
    Safe Manim code execution via subprocess with comprehensive error handling
    """

    def __init__(
        self,
        output_dir: Path,
        quality: str = "1080p60",
        background_color: str = "#0f0f0f",
        timeout: int = 300,  # 5 minutes default timeout
        max_retries: int = 2,
        preview_fps: int = 0
    ):
        self.output_dir = Path(output_dir)
        self.quality = quality
        self.background_color = background_color
        self.timeout = timeout
        self.max_retries = max_retries
        # Frame rate for the fast-preview preset ("l"); 0 keeps Manim's own 15fps.
        self.preview_fps = preview_fps
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Quality mapping to Manim parameters (new format for v0.19+)
        self.quality_map = {
            "l": {"resolution": "854x480", "frame_rate": 15, "name": "low"},
            "m": {"resolution": "1280x720", "frame_rate": 30, "name": "medium"},
            "h": {"resolution": "1920x1080", "frame_rate": 30, "name": "high"},
            "p": {"resolution": "1920x1080", "frame_rate": 60, "name": "production"},
            "k": {"resolution": "2560x1440", "frame_rate": 60, "name": "4k"},
        }

        # Map old quality names to new format
        self.old_to_new_quality = {
            "480p15": "l",
            "720p30": "m",
            "1080p30": "h",
            "1080p60": "p",
            "1440p60": "k",
            "4k60": "k"
        }

    def render(
        self,
        manim_code: str,
        scene_name: str,
        output_filename: Optional[str] = None,
        quality: Optional[str] = None
    ) -> RenderResult:
        """
        Render Manim code and return video file path

        Args:
            manim_code: Complete Manim Python code as string
            scene_name: Name of the scene class to render
            output_filename: Optional custom filename for output video
            quality: Optional per-call quality override (e.g. "l" for a fast
                low-quality re-render preview). Defaults to ``self.quality``.
                Passed explicitly instead of mutating the shared instance so
                concurrent renders never clobber each other's quality.

        Returns:
            RenderResult with success status and video path or error details
        """

        start_time = time.time()

        # Per-call quality (re-render preview can request "l"); falls back to the
        # renderer's configured quality when not overridden.
        effective_quality = quality or self.quality

        # Purge stale artifacts in output_dir that share this scene_name. Without
        # this, the fallback branch in _find_output_artifacts can return an
        # unrelated mp4 from a previous run (which has stale audio or no audio
        # at all), silently poisoning the concat step. See issue log 2026-04-22.
        self._purge_stale_artifacts(scene_name, output_filename)

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Rendering Manim scene '{scene_name}' (attempt {attempt + 1}/{self.max_retries + 1})")

                # Record the exact subprocess launch time so _find_output_artifacts
                # can reject any mp4 older than this (i.e. files left by previous
                # runs that happen to share the scene class name).
                attempt_start_time = time.time()

                # Clean invalid UTF-8 characters from Manim code
                cleaned_code = self._clean_invalid_utf8(manim_code)

                # Create temporary file for Manim code.
                # NOTE: a RANDOM temp name (not a stable per-scene name) is
                # intentional. A stable script stem would let Manim reuse its
                # partial-movie-file cache across re-renders, but Manim's frame
                # cache is incompatible with manim-voiceover: a cached animation
                # sets renderer.skip_animations=True, and Scene.add_sound() early-
                # returns under that flag, so the voiceover audio of every cached
                # block is dropped -> silent video. Caching is therefore disabled
                # project-wide via manim.cfg (disable_caching = True); the random
                # name is a second line of defense so a render never reuses stale
                # cached frames without their audio.
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                    # Appended, never prepended: a prologue would shift every line
                    # number in the scene code and make render-failure tracebacks
                    # (which the auto-fix prompt asks the LLM to trust) point at the
                    # wrong lines. Manim imports the whole module before it builds
                    # the Scene, so a trailing import still patches in time.
                    # Every patch inside is opt-in and off unless the env vars below
                    # are set, so this line is inert on the publish path.
                    temp_file.write(cleaned_code + "\nimport rendering.manim_speedups  # noqa: E402\n")
                    temp_file_path = temp_file.name

                try:
                    # Prepare Manim command
                    cmd = self._build_manim_command(temp_file_path, scene_name, output_filename, quality=effective_quality)
                    env = os.environ.copy()
                    project_root = str(Path.cwd())
                    existing_pythonpath = env.get("PYTHONPATH", "")
                    # os.pathsep, not ":". On Windows the separator is ";" — joining
                    # with ":" produced one unusable entry, which broke every import
                    # from the project root (including the speedups module below)
                    # for anyone who had PYTHONPATH set.
                    env["PYTHONPATH"] = (
                        f"{project_root}{os.pathsep}{existing_pythonpath}"
                        if existing_pythonpath else project_root
                    )

                    # Fast-preview only: enable the Manim-internal speedups
                    # (rendering/manim_speedups.py). Measured -11.77s on a 260s
                    # scene. The publish presets deliberately keep stock Manim.
                    # effective_quality may still be in the legacy "480p15" form,
                    # so normalise it the same way _build_manim_command does before
                    # comparing — otherwise "l" never matches and "1080p60" might.
                    normalized_quality = self.old_to_new_quality.get(
                        effective_quality, effective_quality
                    )
                    if normalized_quality == "l":
                        env["ALGOT2V_MANIM_AACMF"] = "1"
                        env["ALGOT2V_MANIM_FRAMEREUSE"] = "1"
                        env["ALGOT2V_MANIM_ULTRAFAST"] = "1"

                    # Execute Manim (run from project root, not output_dir)
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=self.timeout,
                        cwd=Path.cwd(),
                        env=env,
                    )

                    # Parse output and find render artifacts
                    if result.returncode == 0:
                        video_path, subtitle_path = self._find_output_artifacts(
                            result.stdout,
                            scene_name,
                            output_filename,
                            min_mtime=attempt_start_time,
                        )
                        if video_path:
                            # Hard audio-stream guard: manim-voiceover must have
                            # produced an audio track. If the mp4 is silent we
                            # treat it as a failed render (prevents concat from
                            # falling back to anullsrc silence for real scenes).
                            if not self._video_has_audio_stream(video_path):
                                error_msg = (
                                    f"Rendered video has no audio stream: {video_path}. "
                                    "The scene code is missing/failed voiceover playback."
                                )
                                self.logger.error(error_msg)
                                # Delete the bad output so the next attempt /
                                # fallback cannot re-pick this file.
                                try:
                                    Path(video_path).unlink(missing_ok=True)
                                except OSError:
                                    pass
                                if subtitle_path:
                                    try:
                                        Path(subtitle_path).unlink(missing_ok=True)
                                    except OSError:
                                        pass
                                if attempt < self.max_retries:
                                    continue
                                return RenderResult(
                                    success=False,
                                    error_message=error_msg,
                                    stdout=result.stdout,
                                    stderr=result.stderr,
                                )

                            # Extract metadata
                            duration = self._extract_video_duration(video_path)
                            resolution = self._get_quality_resolution(effective_quality)
                            render_time = time.time() - start_time

                            self.logger.info(f"Successfully rendered {scene_name} in {render_time:.2f}s")

                            return RenderResult(
                                success=True,
                                video_path=str(video_path),
                                subtitle_path=str(subtitle_path) if subtitle_path else None,
                                duration=duration,
                                resolution=resolution,
                                render_time=render_time,
                                stdout=result.stdout,
                                stderr=result.stderr
                            )
                        else:
                            error_msg = "Manim completed but no output video found"
                            self.logger.error(error_msg)
                            if attempt < self.max_retries:
                                continue
                            return RenderResult(
                                success=False,
                                error_message=error_msg,
                                stdout=result.stdout,
                                stderr=result.stderr
                            )
                    else:
                        # Manim failed, analyze error
                        error_analysis = self._analyze_manim_error(result.stderr, result.stdout)
                        self.logger.warning(f"Manim render failed: {error_analysis}")
                        self.logger.warning(f"STDERR: {result.stderr[-500:]}")
                        self.logger.warning(f"STDOUT: {result.stdout[-500:]}")

                        if attempt < self.max_retries and self._is_retryable_error(error_analysis):
                            # Try with simplified code on retry
                            simplified_code = self._simplify_manim_code(manim_code)
                            if simplified_code != manim_code:
                                manim_code = simplified_code
                                continue

                        return RenderResult(
                            success=False,
                            error_message=error_analysis,
                            stdout=result.stdout,
                            stderr=result.stderr
                        )

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                    except OSError:
                        pass

            except subprocess.TimeoutExpired:
                error_msg = f"Manim render timed out after {self.timeout} seconds"
                self.logger.error(error_msg)
                if attempt < self.max_retries:
                    continue
                return RenderResult(success=False, error_message=error_msg)

            except Exception as e:
                error_msg = f"Unexpected error during Manim render: {str(e)}"
                self.logger.error(error_msg)
                if attempt < self.max_retries:
                    continue
                return RenderResult(success=False, error_message=error_msg)

        # All retries exhausted
        return RenderResult(
            success=False,
            error_message=f"Failed after {self.max_retries + 1} attempts"
        )

    def _build_manim_command(
        self,
        script_path: str,
        scene_name: str,
        output_filename: Optional[str] = None,
        quality: Optional[str] = None
    ) -> list:
        """Build Manim command line arguments"""

        # Convert quality to new format if needed (per-call override or default)
        quality = self.old_to_new_quality.get(quality or self.quality, quality or self.quality)

        cmd = [
            "manim", "render",
            script_path,
            scene_name,
            f"-q{quality}"
        ]

        # Fast preview: -q l only drops the resolution to 854x480, the frame
        # rate stays at 15. A voiceover scene's length is pinned to the
        # narration, so most of its frames are static waits that still get
        # rasterised and encoded one by one — the frame COUNT, not the pixel
        # count, is what the preview has left to save. --fps overrides the
        # quality preset's rate (verified: "-ql --fps 10" -> frame_rate=10.0,
        # resolution unchanged). Publish presets are untouched.
        if quality == "l" and self.preview_fps:
            cmd.extend(["--fps", str(self.preview_fps)])

        # Add custom output filename if specified
        if output_filename:
            cmd.extend(["-o", str(output_filename)])

        return cmd

    def _copy_subtitle_sidecar(self, source_video: Path, target_video: Path) -> Optional[Path]:
        """Copy Manim-generated sibling .srt (if present) beside output video."""
        source_srt = source_video.with_suffix(".srt")
        if not source_srt.exists():
            return None

        target_srt = target_video.with_suffix(".srt")
        import shutil

        shutil.copy2(source_srt, target_srt)
        self.logger.info(f"Copied subtitle from {source_srt} to {target_srt}")
        return target_srt

    def _purge_stale_artifacts(
        self, scene_name: str, output_filename: Optional[str] = None
    ) -> None:
        """Delete any pre-existing mp4/srt in output_dir that share this scene name.

        Prevents the fallback branch of ``_find_output_artifacts`` from
        surfacing a file produced by a previous run (which can easily contain
        stale audio or no audio at all).
        """
        candidates: list[Path] = []
        if output_filename:
            p = self.output_dir / output_filename
            candidates.append(p)
            candidates.append(p.with_suffix(".srt"))

        # Exact + fuzzy matches for the class name.
        for pattern in (f"{scene_name}.mp4", f"*{scene_name}*.mp4"):
            candidates.extend(self.output_dir.glob(pattern))
        for pattern in (f"{scene_name}.srt", f"*{scene_name}*.srt"):
            candidates.extend(self.output_dir.glob(pattern))

        seen: set[Path] = set()
        for path in candidates:
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.exists() and resolved.is_file():
                try:
                    resolved.unlink()
                    self.logger.debug(
                        "Purged stale artifact before rendering %s: %s",
                        scene_name,
                        resolved,
                    )
                except OSError as exc:
                    self.logger.warning(
                        "Failed to purge stale artifact %s: %s", resolved, exc
                    )

    def _video_has_audio_stream(self, video_path: Path | str) -> bool:
        """Return True iff the mp4 exposes at least one audio stream."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "a",
                    "-show_entries", "stream=index",
                    "-of", "csv=p=0",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            if result.returncode != 0:
                return False
            return bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            # If ffprobe is missing we can't verify; be conservative and assume
            # audio is present so we don't break working pipelines.
            return True

    def _find_output_artifacts(
        self,
        manim_output: str,
        scene_name: str,
        output_filename: Optional[str] = None,
        min_mtime: float = 0.0,
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """Find/copy rendered video and sibling .srt sidecar.

        Args:
            min_mtime: Reject any candidate file whose mtime is earlier than
                this UNIX timestamp. Used to avoid picking up leftovers from
                previous runs that happen to share the scene class name.
        """

        def _is_fresh(p: Path) -> bool:
            if min_mtime <= 0:
                return True
            try:
                return p.stat().st_mtime >= min_mtime - 1.0  # 1s slack for FS clock skew
            except OSError:
                return False

        # First try custom filename if specified
        if output_filename:
            custom_path = self.output_dir / output_filename
            if custom_path.exists() and _is_fresh(custom_path):
                subtitle_path = custom_path.with_suffix(".srt") if custom_path.with_suffix(".srt").exists() else None
                return custom_path, subtitle_path

        # Parse Manim output for file path
        patterns = [
            r"File ready at (.+?\.mp4)",
            r"Output written to (.+?\.mp4)",
            r"Saved animation to (.+?\.mp4)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, manim_output)
            if matches:
                source_video = Path(matches[-1].strip())
                if source_video.exists() and _is_fresh(source_video):
                    if output_filename:
                        target_video = self.output_dir / output_filename
                    else:
                        target_video = self.output_dir / f"{scene_name}.mp4"
                    import shutil

                    shutil.copy2(source_video, target_video)
                    self.logger.info(f"Copied video from {source_video} to {target_video}")
                    subtitle_path = self._copy_subtitle_sidecar(source_video, target_video)
                    return target_video, subtitle_path

        # New Manim (v0.19+) stores files in media/videos directory
        media_dir = Path.cwd() / "media" / "videos"
        if media_dir.exists():
            video_files = [
                v
                for v in media_dir.rglob("*.mp4")
                if "partial_movie_files" not in str(v) and _is_fresh(v)
            ]
            # Require that the filename actually contains the scene class name.
            # The previous code fell back to "newest mp4 in media/videos" when
            # no name match was found, which would silently return an unrelated
            # scene's video for the current scene (e.g. scene B's mp4 returned
            # as scene A's output). That's always wrong.
            scene_videos = [v for v in video_files if scene_name in v.name]
            if scene_videos:
                source_video = max(scene_videos, key=lambda x: x.stat().st_mtime)
                if source_video.exists():
                    if output_filename:
                        target_video = self.output_dir / output_filename
                    else:
                        target_video = self.output_dir / f"{scene_name}.mp4"
                    import shutil

                    shutil.copy2(source_video, target_video)
                    self.logger.info(f"Copied video from {source_video} to {target_video}")
                    subtitle_path = self._copy_subtitle_sidecar(source_video, target_video)
                    return target_video, subtitle_path

        # Fallback: search for video files with scene name in output directory.
        # CRITICAL: still apply the freshness gate so we never return an ancient
        # mp4 from a previous run (which is exactly the 2026-03-06 regression
        # that this whole freshness-check pipeline was introduced to prevent).
        search_patterns = [f"{scene_name}.mp4", f"*{scene_name}*.mp4"]
        for pattern in search_patterns:
            videos = [v for v in self.output_dir.glob(pattern) if v.is_file() and _is_fresh(v)]
            if videos:
                video_path = max(videos, key=lambda x: x.stat().st_mtime)
                self.logger.info(f"Found video via fallback: {video_path}")
                subtitle_path = video_path.with_suffix(".srt") if video_path.with_suffix(".srt").exists() else None
                return video_path, subtitle_path

        self.logger.error(f"Could not find output video for scene: {scene_name}")
        self.logger.error(f"Searched in: {self.output_dir}")
        self.logger.error(f"Available files: {list(self.output_dir.glob('*.mp4'))}")
        if min_mtime > 0:
            self.logger.error(
                "Note: freshness filter active (min_mtime=%s); stale files older "
                "than this are ignored by design.",
                min_mtime,
            )
        return None, None

    def _find_output_video(
        self,
        manim_output: str,
        scene_name: str,
        output_filename: Optional[str] = None,
    ) -> Optional[Path]:
        """Backward-compatible shim: return only video path."""
        video_path, _ = self._find_output_artifacts(manim_output, scene_name, output_filename)
        return video_path

    def _analyze_manim_error(self, stderr: str, stdout: str) -> str:
        """Analyze Manim error output and provide helpful error messages"""

        # Handle None values
        stderr = stderr or ""
        stdout = stdout or ""

        output = stderr + stdout

        # Common error patterns
        error_patterns = {
            r"No such file or directory: 'latex'": "LaTeX not installed - install LaTeX (brew install --cask mactex)",
            r"SyntaxError": "Syntax error in Manim code - invalid Python syntax",
            r"IndentationError": "Indentation error - check code spacing and alignment",
            r"NameError.*not defined": "Variable or function not defined - check for typos",
            r"AttributeError.*has no attribute": "Attribute error - method or property doesn't exist",
            r"TypeError": "Type error - incorrect data types being used",
            r"ValueError": "Value error - invalid argument values",
            r"ZeroDivisionError": "Division by zero error in mathematical calculations",
            r"IndexError": "Index error - list or array index out of range",
            r"KeyError": "Key error - dictionary key not found",
            r"ImportError": "Import error - required module not available",
            r"ModuleNotFoundError": "Module not found - check import statements",
            r"No scene named": f"Scene class not found - ensure scene name matches class definition",
            r"OpenGL is not supported": "OpenGL rendering not supported - falling back to software rendering",
            r"ffmpeg.*not found": "FFmpeg not found - ensure FFmpeg is installed and in PATH",
            r"Permission denied": "Permission error - unable to write to output directory",
            r"Disk full": "Disk full - insufficient storage space for rendering",
            r"Memory.*error": "Memory error - insufficient RAM for complex animation",
            r"Timeout": "Rendering timeout - animation too complex or taking too long"
        }

        for pattern, message in error_patterns.items():
            if re.search(pattern, output, re.IGNORECASE):
                return message

        # If no specific pattern matches, return a generic message with useful context
        if "Traceback" in output:
            # Extract the last line of the traceback for more specific error
            lines = output.strip().split('\n')
            for line in reversed(lines):
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    return f"Manim render failed: {line.strip()}"

        return f"Manim render failed with unknown error. Check logs for details."

    def _is_retryable_error(self, error_message: str) -> bool:
        """Determine if an error is likely to be fixed by retrying with simplified code"""

        retryable_patterns = [
            r"Memory.*error",
            r"Timeout",
            r"OpenGL.*not supported",
            r"Complex.*animation",
            r"Too.*many.*objects"
        ]

        for pattern in retryable_patterns:
            if re.search(pattern, error_message, re.IGNORECASE):
                return True

        return False

    def _simplify_manim_code(self, code: str) -> str:
        """Attempt to simplify Manim code to avoid common rendering issues"""

        # Basic simplifications that might help with complex scenes
        simplifications = [
            # Reduce animation quality settings within code
            (r"frame_rate\s*=\s*\d+", "frame_rate = 15"),

            # Reduce particle counts or complex object counts
            (r"n_points\s*=\s*\d+", "n_points = 20"),
            (r"num_elements\s*=\s*\d+", "num_elements = 10"),

            # Simplify colors to basic ones
            (r"#[0-9a-fA-F]{6}", "#FFFFFF"),

            # Reduce animation durations
            (r"run_time\s*=\s*\d+\.?\d*", "run_time = 1.0"),
        ]

        simplified_code = code
        for pattern, replacement in simplifications:
            simplified_code = re.sub(pattern, replacement, simplified_code)

        return simplified_code

    def _extract_video_duration(self, video_path: Path) -> Optional[float]:
        """Extract video duration using FFmpeg"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
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
                if duration_str:
                    return float(duration_str)

        except (subprocess.TimeoutExpired, ValueError, subprocess.SubprocessError):
            pass

        return None

    def _get_quality_resolution(self, quality: Optional[str] = None) -> Optional[Tuple[int, int]]:
        """Get resolution tuple for the given (or current) quality setting"""
        q = quality or self.quality
        # Normalize old-format names (e.g. "1080p60") so metadata is non-None
        # regardless of which form the quality was configured in.
        q = self.old_to_new_quality.get(q, q)
        quality_info = self.quality_map.get(q)
        if quality_info and "resolution" in quality_info:
            width, height = map(int, quality_info["resolution"].split('x'))
            return (width, height)
        return None

    def _clean_invalid_utf8(self, text: str) -> str:
        """Clean invalid UTF-8 characters from text"""
        try:
            # Encode and decode to catch and replace invalid characters
            return text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        except Exception:
            # If that fails, try character by character
            cleaned_chars = []
            for char in text:
                try:
                    char.encode('utf-8')
                    cleaned_chars.append(char)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    # Replace invalid character with a safe alternative
                    cleaned_chars.append('?')
            return ''.join(cleaned_chars)

    def get_supported_qualities(self) -> list:
        """Return list of supported quality presets"""
        return list(self.quality_map.keys())

    def validate_manim_installation(self) -> bool:
        """Check if Manim is properly installed and accessible"""
        try:
            result = subprocess.run(
                ["manim", "--version"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False