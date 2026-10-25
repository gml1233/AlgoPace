"""
Video Compositor Module

Combines animations (with or without embedded audio) and subtitles into final MP4 videos.
Uses FFmpeg for robust video processing and quality optimization.
"""

import logging
import os
import shutil
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import ffmpeg

from pydantic import BaseModel, Field


_FAST_AAC_ENCODER: Optional[str] = None


def _fast_aac_encoder(default: str, ffmpeg_cmd: str = "ffmpeg") -> str:
    """Fastest available AAC encoder for the ffmpeg CLI, probed once per process.

    The fused single-pass burn has to re-encode audio (it applies the apad
    chain), and libav's native "aac" is ~4x slower than Windows
    MediaFoundation's "aac_mf" on a 260s track — enough to wipe out everything
    fusing the passes saves. Probes the CLI encoder list, which is the right
    question here because this module invokes the ffmpeg binary.
    """
    global _FAST_AAC_ENCODER
    if _FAST_AAC_ENCODER is not None:
        return _FAST_AAC_ENCODER

    _FAST_AAC_ENCODER = default
    try:
        probe = subprocess.run(
            [ffmpeg_cmd, "-hide_banner", "-encoders"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=20,
        )
        if probe.returncode == 0 and " aac_mf " in probe.stdout:
            _FAST_AAC_ENCODER = "aac_mf"
    except (OSError, subprocess.SubprocessError):
        pass
    return _FAST_AAC_ENCODER

try:
    from config import settings
except Exception:  # 保底：测试环境下 config 可能不可导入
    settings = None  # type: ignore


class VideoCompositionResult(BaseModel):
    """Result of video composition operation"""
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    input_video_path: Optional[str] = None
    input_audio_path: Optional[str] = None
    input_subtitle_path: Optional[str] = None
    output_duration: Optional[float] = None
    file_size_mb: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    generation_time: Optional[float] = None
    ffmpeg_command: Optional[str] = None


class VideoCompositor:
    """
    Video composition and processing using FFmpeg

    Handles merging of animations, optional external audio tracks, and subtitles
    into polished final MP4 videos with optimal quality settings.
    """

    def __init__(
        self,
        output_dir: Path,
        video_codec: str = "libx264",
        video_preset: str = "medium",
        subtitle_burn_preset: Optional[str] = None,
        video_crf: int = 23,
        audio_codec: str = "aac",
        audio_bitrate: str = "128k",
        subtitle_burn_in: bool = True,
        subtitle_font_size: int = 24,
        subtitle_font_color: str = "white",
        subtitle_background: bool = True,
        subtitle_background_opacity: float = 0.5,
        subtitle_position: str = "bottom",
        subtitle_safe_zone_ratio: float = 0.083,
        max_retries: int = 3,
        timeout: int = 600
    ):
        """
        Initialize Video Compositor

        Args:
            output_dir: Directory for output videos
            video_codec: Video codec (default: libx264)
            video_preset: Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
            video_crf: Constant Rate Factor (0-51, lower = higher quality, 23 is default)
            audio_codec: Audio codec (default: aac)
            audio_bitrate: Audio bitrate (default: 128k)
            subtitle_burn_in: Whether to burn subtitles into video (hard subs)
            subtitle_font_size: Font size for subtitles
            subtitle_font_color: Color for subtitle text
            subtitle_background: Whether to add background to subtitles
            subtitle_background_opacity: Opacity of subtitle background (0.0-1.0)
            subtitle_position: Position of subtitles (top, center, bottom)
            subtitle_safe_zone_ratio: Bottom safe zone height as a fraction of video height (for MarginV)
            max_retries: Maximum retry attempts for failed operations
            timeout: Timeout in seconds for FFmpeg operations
        """
        self.output_dir = Path(output_dir)
        self.video_codec = video_codec
        self.video_preset = video_preset
        # Preset for the subtitle-burn pass specifically; falls back to
        # video_preset when the caller does not override it.
        self.subtitle_burn_preset = subtitle_burn_preset or video_preset
        self.video_crf = video_crf
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.subtitle_burn_in = subtitle_burn_in
        self.subtitle_font_size = subtitle_font_size
        self.subtitle_font_color = subtitle_font_color
        self.subtitle_background = subtitle_background
        self.subtitle_background_opacity = subtitle_background_opacity
        self.subtitle_position = subtitle_position
        self.subtitle_safe_zone_ratio = subtitle_safe_zone_ratio
        self.max_retries = max_retries
        self.timeout = timeout
        self.ffmpeg_cmd = self._resolve_ffmpeg_command(require_subtitles=self.subtitle_burn_in)
        self.ffprobe_cmd = self._paired_ffprobe_command(self.ffmpeg_cmd)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger("VideoCompositor")

        # Validate FFmpeg availability
        self._validate_ffmpeg()

    @staticmethod
    def _paired_ffprobe_command(ffmpeg_cmd: str) -> str:
        """Return ffprobe next to the selected ffmpeg binary when available."""
        resolved = shutil.which(ffmpeg_cmd) or ffmpeg_cmd
        exe = Path(resolved)
        ffprobe_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
        sibling = exe.with_name(ffprobe_name)
        if sibling.exists():
            return str(sibling)
        return "ffprobe"

    @staticmethod
    def _ffmpeg_supports_subtitles(command: str) -> bool:
        """Return whether an FFmpeg executable includes the libass subtitles filter."""
        try:
            result = subprocess.run(
                [command, "-hide_banner", "-filters"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        if result.returncode != 0:
            return False
        return any(" subtitles " in f" {line} " for line in result.stdout.splitlines())

    @staticmethod
    def _path_exists(path: Path) -> bool:
        try:
            return path.exists()
        except OSError:
            return False

    @classmethod
    def _resolve_ffmpeg_command(cls, require_subtitles: bool = False) -> str:
        """Prefer an FFmpeg build that can burn subtitles on Windows."""
        candidates: List[str] = []

        for env_name in ("ALGOT2V_FFMPEG", "FFMPEG_BINARY"):
            configured = os.environ.get(env_name)
            if configured:
                candidates.append(configured)

        path_command = shutil.which("ffmpeg")
        if path_command:
            candidates.append(path_command)
        candidates.append("ffmpeg")

        if os.name == "nt":
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                winget_root = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
                if cls._path_exists(winget_root):
                    try:
                        candidates.extend(str(p) for p in winget_root.glob("Gyan.FFmpeg.Shared_*/*/bin/ffmpeg.exe"))
                        candidates.extend(str(p) for p in winget_root.glob("Gyan.FFmpeg.Essentials_*/*/bin/ffmpeg.exe"))
                        candidates.extend(str(p) for p in winget_root.glob("Gyan.FFmpeg.Full_*/*/bin/ffmpeg.exe"))
                    except OSError:
                        pass
            candidates.extend([
                r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe",
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            ])

        seen = set()
        existing_candidates: List[str] = []
        for candidate in candidates:
            resolved = shutil.which(candidate) or candidate
            key = str(resolved).lower()
            if key in seen:
                continue
            seen.add(key)
            if candidate == "ffmpeg" or cls._path_exists(Path(resolved)):
                existing_candidates.append(str(resolved))

        if require_subtitles:
            for candidate in existing_candidates:
                if cls._ffmpeg_supports_subtitles(candidate):
                    return candidate
            fallback = existing_candidates[0] if existing_candidates else "ffmpeg"
            raise RuntimeError(
                "No FFmpeg executable with the 'subtitles' filter was found. "
                "Install a full FFmpeg build with libass support, or set ALGOT2V_FFMPEG."
            )

        return existing_candidates[0] if existing_candidates else "ffmpeg"

    def _validate_ffmpeg(self):
        """Validate that FFmpeg is available and working"""
        try:
            # Check FFmpeg availability
            result = subprocess.run(
                [self.ffmpeg_cmd, '-version'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )

            if result.returncode != 0:
                raise RuntimeError("FFmpeg not found or not working")

            self.logger.info(f"FFmpeg validation successful: {self.ffmpeg_cmd}")

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise RuntimeError(f"FFmpeg validation failed: {e}")

    @staticmethod
    def _hex_to_ass_color(hex_color: str) -> str:
        """Convert HTML hex color (#RRGGBB or #AARRGGBB) to ASS PrimaryColour &HAABBGGRR& (BGR order)."""
        s = (hex_color or "").strip().lstrip("#")
        if len(s) == 6:
            r, g, b = s[0:2], s[2:4], s[4:6]
            return f"&H00{b}{g}{r}&"
        if len(s) == 8:
            a, r, g, b = s[0:2], s[2:4], s[4:6], s[6:8]
            return f"&H{a}{b}{g}{r}&"
        return "&H00FFFFFF&"

    @staticmethod
    def _build_force_style(overrides: Dict[str, Any]) -> str:
        """Build FFmpeg force_style string from subtitle_style_overrides (ASS format)."""
        parts = []
        font_name = overrides.get("font_name")
        if font_name:
            parts.append(f"FontName={font_name}")
        font_size = overrides.get("font_size")
        if font_size is not None:
            parts.append(f"FontSize={int(font_size)}")
        font_color = overrides.get("font_color")
        if font_color:
            parts.append(f"PrimaryColour={VideoCompositor._hex_to_ass_color(font_color)}")
        alignment = overrides.get("alignment")
        if alignment is not None:
            parts.append(f"Alignment={int(alignment)}")
        wrap_style = overrides.get("wrap_style")
        if wrap_style is not None:
            parts.append(f"WrapStyle={int(wrap_style)}")
        margin_v = overrides.get("margin_v")
        if margin_v is not None:
            parts.append(f"MarginV={int(margin_v)}")
        return ",".join(parts) if parts else ""

    @staticmethod
    def _escape_filter_quoted_value(value: str) -> str:
        """Escape a value used inside single quotes in an FFmpeg filtergraph."""
        return (
            str(value)
            .replace("\\", "/")
            .replace("\\", "\\\\")
            .replace("'", r"\'")
            .replace(":", r"\:")
        )

    def execute(
        self,
        video_path: str,
        audio_path: Optional[str] = None,
        subtitle_path: Optional[str] = None,
        output_filename: Optional[str] = None,
        subtitle_style_overrides: Optional[Dict[str, Any]] = None,
        audio_pad_to: Optional[float] = None
    ) -> VideoCompositionResult:
        """
        Execute video composition

        Args:
            video_path: Path to input animation video
            audio_path: Optional path to external synchronized audio
            subtitle_path: Optional path to SRT subtitle file
            output_filename: Optional custom output filename
            subtitle_style_overrides: Optional dict with font_name, font_size, font_color, alignment, wrap_style

        Returns:
            VideoCompositionResult with output video details
        """
        start_time = datetime.now()

        try:
            self.logger.info(f"Starting video composition")
            self.logger.info(f"  Video: {video_path}")
            self.logger.info(f"  Audio: {audio_path}")
            self.logger.info(f"  Subtitles: {subtitle_path}")

            # Validate inputs
            self._validate_inputs(video_path, audio_path, subtitle_path)

            # Generate output filename if not provided
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"final_video_{timestamp}.mp4"

            # Ensure .mp4 extension
            if not output_filename.endswith('.mp4'):
                output_filename += '.mp4'

            output_path = self.output_dir / output_filename

            # Get video information
            video_info = self._get_video_info(video_path)
            self.logger.info(f"  Input video: {video_info['duration']:.2f}s, {video_info['resolution']}")

            # Get audio information (if external audio is provided)
            if audio_path:
                audio_info = self._get_audio_info(audio_path)
                self.logger.info(f"  Input audio: {audio_info['duration']:.2f}s")
            else:
                self.logger.info("  Input audio: use embedded audio from input video")

            # Execute composition with retry logic
            for attempt in range(self.max_retries):
                try:
                    if attempt > 0:
                        self.logger.info(f"Retry attempt {attempt + 1}/{self.max_retries}")

                    success = self._compose_video(
                        video_path, audio_path, subtitle_path, str(output_path),
                        subtitle_style_overrides=subtitle_style_overrides,
                        audio_pad_to=audio_pad_to
                    )

                    if success:
                        break

                except Exception as e:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        raise e
            else:
                raise RuntimeError("Video composition failed after all retries")

            # Validate output
            if not output_path.exists():
                raise RuntimeError("Output video file was not created")

            # Get output video information
            output_info = self._get_video_info(str(output_path))
            file_size_mb = output_path.stat().st_size / (1024 * 1024)

            generation_time = (datetime.now() - start_time).total_seconds()

            self.logger.info(f"Video composition completed successfully")
            self.logger.info(f"  Output: {output_path}")
            self.logger.info(f"  Duration: {output_info['duration']:.2f}s")
            self.logger.info(f"  Resolution: {output_info['resolution']}")
            self.logger.info(f"  File size: {file_size_mb:.2f}MB")
            self.logger.info(f"  Generation time: {generation_time:.2f}s")

            return VideoCompositionResult(
                success=True,
                output_path=str(output_path),
                input_video_path=video_path,
                input_audio_path=audio_path,
                input_subtitle_path=subtitle_path,
                output_duration=output_info['duration'],
                file_size_mb=file_size_mb,
                resolution=output_info['resolution'],
                generation_time=generation_time
            )

        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Video composition failed: {e}"
            self.logger.error(error_msg)

            return VideoCompositionResult(
                success=False,
                error_message=error_msg,
                input_video_path=video_path,
                input_audio_path=audio_path,
                input_subtitle_path=subtitle_path,
                generation_time=generation_time
            )

    def _validate_inputs(self, video_path: str, audio_path: Optional[str], subtitle_path: Optional[str] = None):
        """Validate input files"""
        # Validate video file
        video_file = Path(video_path)
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not video_file.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
            raise ValueError(f"Invalid video format: {video_file.suffix}")

        # Validate audio file (optional)
        if audio_path:
            audio_file = Path(audio_path)
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            if not audio_file.suffix.lower() in ['.mp3', '.wav', '.aac', '.m4a']:
                raise ValueError(f"Invalid audio format: {audio_file.suffix}")

        # Validate subtitle file if provided
        if subtitle_path:
            subtitle_file = Path(subtitle_path)
            if not subtitle_file.exists():
                raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")
            if not subtitle_file.suffix.lower() in ['.srt', '.ass', '.vtt']:
                raise ValueError(f"Invalid subtitle format: {subtitle_file.suffix}")

        self.logger.info("All input files validated successfully")

    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using FFprobe"""
        try:
            probe = ffmpeg.probe(video_path, cmd=self.ffprobe_cmd)

            # Video stream info
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if not video_stream:
                raise ValueError("No video stream found")

            width = int(video_stream['width'])
            height = int(video_stream['height'])

            # Duration
            duration = float(probe['format']['duration'])

            return {
                'duration': duration,
                'resolution': (width, height),
                'fps': eval(video_stream.get('r_frame_rate', '25/1'))
            }

        except Exception as e:
            raise RuntimeError(f"Failed to get video info: {e}")

    def _get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """Get audio information using FFprobe"""
        try:
            probe = ffmpeg.probe(audio_path, cmd=self.ffprobe_cmd)

            # Duration
            duration = float(probe['format']['duration'])

            return {
                'duration': duration
            }

        except Exception as e:
            raise RuntimeError(f"Failed to get audio info: {e}")

    def _compose_video(
        self,
        video_path: str,
        audio_path: Optional[str],
        subtitle_path: Optional[str],
        output_path: str,
        subtitle_style_overrides: Optional[Dict[str, Any]] = None,
        audio_pad_to: Optional[float] = None
    ) -> bool:
        """
        Compose final video using FFmpeg

        Args:
            video_path: Input video file
            audio_path: Optional input audio file
            subtitle_path: Optional input subtitle file
            output_path: Output video file
            subtitle_style_overrides: Optional style dict (font_name, font_size, font_color, alignment, wrap_style)

        Returns:
            True if successful, False otherwise
        """
        try:
            filter_parts: List[str] = []
            video_map = "0:v:0"
            # Create subtitle filter if burning in and subtitle_path provided
            if self.subtitle_burn_in and subtitle_path:
                # Ensure subtitles stay inside the bottom safe zone:
                # auto-inject MarginV / Alignment defaults.
                style_overrides = dict(subtitle_style_overrides) if subtitle_style_overrides else {}
                # CRITICAL: libass interprets MarginV (and FontSize) in the subtitle
                # *script* coordinate space — PlayResY — NOT in output-video pixels.
                # When FFmpeg burns an .srt it synthesizes an ASS header with a FIXED
                # PlayResY=288 regardless of the output resolution, then scales every
                # coordinate by output_height / PlayResY. So MarginV must be computed
                # against this fixed script height. Computing it against the real video
                # height (the old behaviour) double-scaled it: the same logical margin
                # drifted UPWARD at higher resolutions (e.g. 1080p subtitles ended up
                # ~2.7% of frame height higher than the 480p preview). A constant MarginV
                # makes the relative position (MarginV / PlayResY) identical at every
                # resolution. Verified 480p/720p/1080p/1440p all land at ~5.7% from the
                # bottom. See git history / subtitle position probe.
                SRT_SCRIPT_HEIGHT = 288  # libass/FFmpeg default PlayResY for burned-in SRT
                safe_zone = max(1, int(round(SRT_SCRIPT_HEIGHT * self.subtitle_safe_zone_ratio)))
                # Place subtitle vertically within the safe zone;
                # libass MarginV (with alignment=2) is measured from the bottom of the screen.
                # subtitle_margin_ratio 控制在 safe zone 内的垂直占比，越小越贴底。
                margin_ratio = getattr(settings, "subtitle_margin_ratio", 0.15)
                default_margin_v = max(6, int(round(safe_zone * margin_ratio)))
                style_overrides.setdefault("margin_v", default_margin_v)
                style_overrides.setdefault("alignment", 2)  # 2 = bottom-center
                self.logger.info(
                    f"  Subtitle MarginV (script space, PlayResY={SRT_SCRIPT_HEIGHT}): "
                    f"{style_overrides['margin_v']} (safe_zone_ratio={self.subtitle_safe_zone_ratio}, "
                    f"margin_ratio={margin_ratio}), Alignment={style_overrides['alignment']} "
                    f"— resolution-independent"
                )
                force_style = self._build_force_style(style_overrides)
                # FFmpeg's subtitles filter has its own parser. Passing the
                # path through ffmpeg-python can over-escape Windows paths
                # into output\\\\scripts..., which FFmpeg reads as invalid
                # filter syntax. Build this filtergraph explicitly.
                posix_subtitle_path = str(subtitle_path).replace("\\", "/")
                escaped_subtitle_path = self._escape_filter_quoted_value(posix_subtitle_path)
                if force_style:
                    escaped_force_style = self._escape_filter_quoted_value(force_style)
                    subtitle_filter = (
                        f"[0:v]subtitles=filename='{escaped_subtitle_path}':"
                        f"force_style='{escaped_force_style}'[v]"
                    )
                else:
                    subtitle_filter = f"[0:v]subtitles=filename='{escaped_subtitle_path}'[v]"
                filter_parts.append(subtitle_filter)
                video_map = "[v]"

            # Build output: optional external audio, otherwise keep input video's audio track.
            cmd = [self.ffmpeg_cmd, "-i", video_path]
            output_args = [
                "-map", video_map,
                "-c:v", self.video_codec,
                "-preset", self.subtitle_burn_preset,
                "-crf", str(self.video_crf),
                "-movflags", "+faststart",
                "-pix_fmt", "yuv420p",
            ]

            if audio_path is not None:
                cmd.extend(["-i", audio_path])
                output_args.extend([
                    "-map", "1:a:0",
                    "-c:a", self.audio_codec,
                    "-b:a", self.audio_bitrate,
                    "-shortest",
                ])
            else:
                # Keep embedded audio when no external audio is provided.
                # After subtitles filter, `video` is video-only; we must pass the original audio stream explicitly.
                probe = ffmpeg.probe(video_path, cmd=self.ffprobe_cmd)
                has_embedded_audio = any(s.get("codec_type") == "audio" for s in probe.get("streams", []))
                if has_embedded_audio and audio_pad_to:
                    # Fused single-pass mode: the caller handed us a raw scene mp4
                    # instead of a concatenated one, so the audio padding that
                    # _concatenate_scenes used to do has to happen here.
                    #
                    # Manim writes an audio track ~1.9s shorter than its video.
                    # Padding it to the exact VIDEO duration is what makes the
                    # tail of the render survive; note -shortest is deliberately
                    # NOT set on this branch, since with a padded track it would
                    # have nothing to trim but with an unpadded one it silently
                    # truncates the ending.
                    filter_parts.append(
                        f"[0:a]aresample=async=1:first_pts=0,apad,"
                        f"atrim=start=0:end={float(audio_pad_to)},asetpts=PTS-STARTPTS[a]"
                    )
                    output_args.extend([
                        "-map", "[a]",
                        "-c:a", _fast_aac_encoder(self.audio_codec, self.ffmpeg_cmd),
                        "-b:a", self.audio_bitrate,
                    ])
                elif has_embedded_audio:
                    output_args.extend([
                        "-map", "0:a:0",
                        "-c:a", "copy",
                        "-shortest",
                    ])
                else:
                    output_args.append("-an")

            if filter_parts:
                cmd.extend(["-filter_complex", ";".join(filter_parts)])
            cmd.extend(output_args)
            cmd.extend([output_path, "-y"])

            # Run FFmpeg.
            #
            # overwrite_output is REQUIRED. Without -y, ffmpeg prompts
            # "File '...' already exists. Overwrite? [y/N]", reads EOF from the
            # inherited stdin, declines, and exits with returncode 0 while
            # leaving the pre-existing file untouched. Both of this module's
            # success checks (this returncode test and the output_path.exists()
            # test in execute()) pass in that case, so the caller is handed a
            # stale, unrelated video and told the composition succeeded.
            self.logger.info(f"FFmpeg command: {' '.join(cmd)}")

            # Record the launch time so the freshness check below can tell a
            # newly written file apart from one that was already on disk.
            launch_time = time.time()

            # Execute with timeout. stdin is closed so ffmpeg can never block on
            # an interactive prompt.
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            try:
                stdout, stderr = process.communicate(timeout=self.timeout)

                if process.returncode != 0:
                    raise RuntimeError(f"FFmpeg failed with return code {process.returncode}: {stderr}")

                # Freshness guard: existence alone is what let the missing -y bug
                # through, so require the file to have been written by THIS run.
                out_file = Path(output_path)
                if not out_file.exists():
                    raise RuntimeError(f"FFmpeg reported success but wrote no output: {output_path}")
                if out_file.stat().st_mtime < launch_time - 1:
                    raise RuntimeError(
                        f"FFmpeg reported success but {output_path} predates this run "
                        f"(stale output, refusing to return it)"
                    )

                self.logger.info("FFmpeg processing completed successfully")
                return True

            except subprocess.TimeoutExpired:
                process.kill()
                raise RuntimeError(f"FFmpeg processing timed out after {self.timeout}s")

        except Exception as e:
            self.logger.error(f"FFmpeg processing failed: {e}")
            raise

    def get_supported_formats(self) -> List[str]:
        """Get list of supported input/output formats"""
        return [
            "mp4", "avi", "mov", "mkv", "webm"  # Video formats
        ]

    def estimate_output_size(
        self,
        video_duration: float,
        video_resolution: Tuple[int, int],
        audio_bitrate: str = "128k"
    ) -> float:
        """
        Estimate output file size in MB

        Args:
            video_duration: Duration in seconds
            video_resolution: Resolution as (width, height)
            audio_bitrate: Audio bitrate

        Returns:
            Estimated file size in MB
        """
        # Rough estimation based on settings
        width, height = video_resolution
        pixels = width * height

        # Video bitrate estimation (simplified)
        if pixels <= 640 * 480:  # SD
            video_bitrate_kbps = 500
        elif pixels <= 1280 * 720:  # HD
            video_bitrate_kbps = 2000
        elif pixels <= 1920 * 1080:  # Full HD
            video_bitrate_kbps = 5000
        else:  # 4K and above
            video_bitrate_kbps = 15000

        # Adjust for CRF
        video_bitrate_kbps = video_bitrate_kbps * (1 - (self.video_crf - 23) / 51)

        # Audio bitrate
        audio_bitrate_kbps = int(audio_bitrate.replace('k', ''))

        # Total bitrate
        total_bitrate_kbps = video_bitrate_kbps + audio_bitrate_kbps

        # Convert to file size (MB)
        file_size_mb = (total_bitrate_kbps * video_duration) / (8 * 1024)

        return max(file_size_mb, 0.1)  # Minimum 0.1MB
