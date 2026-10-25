"""Opt-in monkey patches that speed up Manim's own render loop.

This module is imported from INSIDE the generated scene script (appended as the
last line by ManimRenderer._build_manim_command's temp-file writer), so it runs
in the Manim subprocess after the scene module is imported but before Manim
instantiates the Scene and its SceneFileWriter — early enough for every patch
below to take effect.

Why appended at the END of the script rather than prepended: the render-failure
auto-fix prompt (agents/manim_agent.py RENDER_FIX_PROMPT) asks the LLM to fix
only the line the traceback points at. A prologue would shift every line number
in the user's code and make those tracebacks lie.

Every patch is behind its own environment variable and every variable defaults
to OFF, so a renderer that does not opt in behaves exactly like stock Manim.
ManimRenderer only turns them on for the fast-preview quality preset.

Measured on the real 260.6s GetNextCangjieVideo scene at 854x480/10fps, three
mirrored A/B pairs on an idle machine: 49.83s -> 38.06s median (-11.77s) with
all three enabled. The three do NOT stack additively — FRAMEREUSE and ULTRAFAST
both draw down the same close_partial_movie_stream bucket.

None of this touches Manim's animation cache. manim.cfg keeps
disable_caching = True, which is load-bearing: a cache-served animation sets
renderer.skip_animations, and Scene.add_sound early-returns on that flag, which
silently drops manim-voiceover narration.
"""

import os
import sys

import av
import manim
from manim import config
from manim.scene import scene_file_writer as _sfw
from manim.scene.scene_file_writer import SceneFileWriter


def _enabled(name: str) -> bool:
    """Patches are opt-in: anything other than an explicit "1" leaves Manim stock."""
    return os.environ.get(name, "0") == "1"


# These patches reach into Manim internals, so they are pinned to the version
# they were validated against. A mismatch disables them rather than risking a
# silently wrong render against a changed implementation.
_SUPPORTED_MANIM = "0.20.1"
_VERSION_OK = getattr(manim, "__version__", None) == _SUPPORTED_MANIM

if not _VERSION_OK:
    print(
        f"[manim_speedups] manim {getattr(manim, '__version__', '?')} != "
        f"{_SUPPORTED_MANIM}; speedups disabled",
        file=sys.stderr,
    )


# --------------------------------------------------------------------------
# 1. Encode the scene soundtrack with aac_mf instead of libav's native aac.
#
# SceneFileWriter.combine_to_movie muxes the assembled WAV soundtrack to AAC via
# convert_audio(..., "aac"). On this machine libav's aac encoder runs the 258.6s
# soundtrack in ~6.4s while Windows MediaFoundation's aac_mf does it in ~1.4s.
# Measured contribution to a full render: -5.85s (median of 3 mirrored pairs).
#
# The .aac produced here is a throwaway intermediate: _concatenate_scenes
# immediately re-encodes the audio at 128k, so aac_mf's lower default bitrate
# does not reach the finished video.
# --------------------------------------------------------------------------
if _VERSION_OK and _enabled("ALGOT2V_MANIM_AACMF") and hasattr(_sfw, "convert_audio"):
    _orig_convert_audio = _sfw.convert_audio

    def _convert_audio_fast(input_path, output_path, codec_name):
        # The try/except must wrap the ENCODE ITSELF. Probing with
        # av.codec.Codec("aac_mf", "w") succeeds on machines where the encode
        # later fails, so a probe guards nothing.
        if codec_name == "aac":
            try:
                return _orig_convert_audio(input_path, output_path, "aac_mf")
            except Exception as exc:  # noqa: BLE001 — any failure must fall back
                print(
                    f"[manim_speedups] aac_mf failed ({exc!r}); falling back to aac",
                    file=sys.stderr,
                )
        return _orig_convert_audio(input_path, output_path, codec_name)

    _sfw.convert_audio = _convert_audio_fast


# --------------------------------------------------------------------------
# 2. Convert a frozen frame RGBA->YUV once and reuse the AVFrame.
#
# During narration waits Manim hands SceneFileWriter the same ndarray N times
# (Scene.compile_animation_data flags static waits, and the renderer replays the
# frozen frame). Stock encode_and_write_frame rebuilds and re-converts an
# AVFrame for each repeat. Converting once and re-muxing the same frame produces
# a byte-identical file (verified: output md5 matches stock) for less work.
# --------------------------------------------------------------------------
if (
    _VERSION_OK
    and _enabled("ALGOT2V_MANIM_FRAMEREUSE")
    and hasattr(SceneFileWriter, "encode_and_write_frame")
):

    def _encode_and_write_frame(self, frame, num_frames):
        if num_frames < 1:
            return
        if num_frames == 1:
            av_frame = av.VideoFrame.from_ndarray(frame, format="rgba")
            for packet in self.video_stream.encode(av_frame):
                self.video_container.mux(packet)
            return

        # Repeat run: pay the pixel-format conversion once.
        av_frame = av.VideoFrame.from_ndarray(frame, format="rgba").reformat(
            format=self.video_stream.pix_fmt
        )
        for i in range(num_frames):
            av_frame.pts = i
            for packet in self.video_stream.encode(av_frame):
                self.video_container.mux(packet)

    SceneFileWriter.encode_and_write_frame = _encode_and_write_frame


# --------------------------------------------------------------------------
# 3. x264 preset=ultrafast for the partial movie files.
#
# The partial movie files are intermediates that _concatenate_scenes re-encodes
# anyway, so their compression efficiency does not matter — only how long the
# main thread blocks joining the writer thread. Preview quality only; the
# publish presets never enable this, because it costs disk size.
# --------------------------------------------------------------------------
if (
    _VERSION_OK
    and _enabled("ALGOT2V_MANIM_ULTRAFAST")
    and hasattr(SceneFileWriter, "open_partial_movie_stream")
):
    from queue import Queue
    from threading import Thread

    from manim.scene.scene_file_writer import to_av_frame_rate

    def _open_partial_movie_stream(self, file_path=None):
        """Stock open_partial_movie_stream with preset=ultrafast added.

        Kept as a full copy of the upstream body (rather than a wrapper) because
        the encoder options are baked in at av.open time and cannot be adjusted
        afterwards.
        """
        if file_path is None:
            file_path = self.partial_movie_files[self.renderer.num_plays]
        self.partial_movie_file_path = file_path

        fps = to_av_frame_rate(config.frame_rate)

        partial_movie_file_codec = "libx264"
        partial_movie_file_pix_fmt = "yuv420p"
        av_options = {
            "an": "1",  # ffmpeg: -an, no audio
            "crf": "23",
        }

        if config.movie_file_extension == ".webm":
            partial_movie_file_codec = "libvpx-vp9"
            av_options["-auto-alt-ref"] = "1"
            if config.transparent:
                partial_movie_file_pix_fmt = "yuva420p"
        elif config.transparent:
            partial_movie_file_codec = "qtrle"
            partial_movie_file_pix_fmt = "argb"
        else:
            av_options["preset"] = "ultrafast"  # <-- the only deviation from stock

        video_container = av.open(file_path, mode="w")
        stream = video_container.add_stream(
            partial_movie_file_codec, rate=fps, options=av_options
        )
        stream.pix_fmt = partial_movie_file_pix_fmt
        stream.width = config.pixel_width
        stream.height = config.pixel_height

        self.video_container = video_container
        self.video_stream = stream

        self.queue = Queue()
        self.writer_thread = Thread(target=self.listen_and_write, args=())
        self.writer_thread.start()

    SceneFileWriter.open_partial_movie_stream = _open_partial_movie_stream
