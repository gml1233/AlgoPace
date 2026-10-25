import asyncio
import json
import os
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict

from manim import logger
import manim_voiceover.services.base as _mv_base
from manim_voiceover.defaults import DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService
from pydub import AudioSegment
from pydub.silence import detect_leading_silence


# ---------------------------------------------------------------------------
# UTF-8 voiceover-cache I/O patch (Windows GBK-locale fix)
# ---------------------------------------------------------------------------
#
# manim-voiceover reads and writes its voiceover cache (media/voiceovers/
# cache.json) with bare open()/json.load(), i.e. WITHOUT an explicit encoding.
# Python then falls back to the platform default, which on a zh-CN Windows
# install is GBK — not UTF-8. Our narration is Chinese, so the cache holds raw
# UTF-8 bytes (e.g. "本" -> E6 9C AC). The FIRST render writes the file fine,
# but any SUBSEQUENT render tries to read it back under GBK and dies with:
#
#     UnicodeDecodeError: 'gbk' codec can't decode byte 0xac in position 19 ...
#
# inside the manim subprocess, which surfaces to the pipeline as a "二次渲染"
# (re-render) failure. We force UTF-8 for BOTH sides of the cache round-trip:
#   * the read  -> EdgeTTSService.get_cached_result (overridden below);
#   * the append -> base.append_to_json_file (module attribute patched here,
#     because base.py bound the name at import time).
# Both are made tolerant of a missing/corrupt cache so a bad file merely
# triggers regeneration instead of aborting the whole render.


# In-process index of the voiceover cache, keyed by cache.json path.
#   {path: {"stamp": (mtime, size), "keys": {entry_key: entry}}}
# The stamp is revalidated on every access, so a write from a concurrently
# running Manim subprocess invalidates our copy and forces a fresh read.
_CACHE_INDEX: Dict[str, Dict[str, Any]] = {}


def _entry_key(input_data) -> str:
    """Stable key for an ``input_data`` dict (the field the cache matches on)."""
    return json.dumps(input_data, sort_keys=True, ensure_ascii=False, default=str)


def _read_cache_list(json_file: str) -> list:
    """Read cache.json as a list, tolerating a missing or corrupt file."""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        logger.warning("Voiceover cache %s unreadable, rebuilding: %s", json_file, exc)
        return []
    return items if isinstance(items, list) else []


def _cache_index(json_file: str) -> Dict[str, Any]:
    """Return {entry_key: entry} for cache.json, re-reading only when it changed.

    SpeechService.get_cached_result re-opened, re-parsed and linearly scanned
    the whole file for EVERY voiceover block. With a 5.4 MB / 4500-entry cache
    and ~29 blocks per video that alone cost several seconds per render, all of
    it repeated work. Parsing once per file revision and looking up by key
    makes it O(1) after the first block.
    """
    try:
        st = os.stat(json_file)
        stamp = (st.st_mtime_ns, st.st_size)
    except OSError:
        stamp = None

    cached = _CACHE_INDEX.get(json_file)
    if cached is not None and cached["stamp"] == stamp:
        return cached["keys"]

    keys: Dict[str, Any] = {}
    for entry in _read_cache_list(json_file):
        if not isinstance(entry, dict):
            continue
        # First occurrence wins, matching the original linear scan's behaviour.
        keys.setdefault(_entry_key(entry.get("input_data")), entry)

    _CACHE_INDEX[json_file] = {"stamp": stamp, "keys": keys}
    return keys


def _utf8_append_to_json_file(json_file, data: dict) -> None:
    """UTF-8, locale-independent replacement for helper.append_to_json_file.

    Skips the write entirely when the entry is already cached. manim_voiceover
    calls this unconditionally at the end of _wrap_generate_from_text
    (services/base.py:126) — including when generate_from_text returned a pure
    cache HIT — so on a re-render every block used to append a byte-identical
    duplicate AND rewrite the whole multi-megabyte file. That made the cache
    grow by one junk entry per block per render (measured 4572 entries for
    2124 unique clips) and each render slower than the last.
    """
    json_file = str(json_file)
    key = _entry_key(data.get("input_data"))

    if key in _cache_index(json_file):
        return  # already on disk — nothing to write

    # Genuine miss: re-read from disk first so a concurrent worker's entries
    # survive, keeping the same race window the original implementation had.
    items = _read_cache_list(json_file)
    items.append(data)
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)

    _CACHE_INDEX.pop(json_file, None)  # force a re-stamp on next access


# Patch the name in the base module's namespace (that is what SpeechService.
# _wrap_generate_from_text actually calls); idempotent on re-import.
_mv_base.append_to_json_file = _utf8_append_to_json_file

try:
    import edge_tts
    import edge_tts.exceptions as _edge_tts_exceptions
except ImportError as exc:  # pragma: no cover - exercised in runtime env
    edge_tts = None
    _edge_tts_exceptions = None
    _EDGE_TTS_IMPORT_ERROR = exc
else:
    _EDGE_TTS_IMPORT_ERROR = None

try:
    import aiohttp
    _AIOHTTP_CLIENT_ERROR: tuple[type[BaseException], ...] = (aiohttp.ClientError,)
except ImportError:  # pragma: no cover - aiohttp is an edge-tts dependency
    _AIOHTTP_CLIENT_ERROR = ()

# Transient failures we retry on. Edge TTS routinely returns empty websocket
# frames (xml ParseError) or times out when the Bing speech endpoint is under
# concurrent load from the same client IP; exponential backoff with jitter
# usually recovers without user intervention.
_RETRYABLE_EXC: tuple[type[BaseException], ...] = (
    asyncio.TimeoutError,
    ConnectionError,
    OSError,
    ET.ParseError,
    *_AIOHTTP_CLIENT_ERROR,
    *((_edge_tts_exceptions.EdgeTTSException,) if _edge_tts_exceptions else ()),
)


# Cache version marker. Bump when trimming / encoding behavior changes so that
# previously-cached entries are not reused.
# v4: force the domain term “哈夫曼” to use 铪 (hā, first tone) for Edge TTS.
#     The subtitle/on-screen text keeps the standard spelling.
_CACHE_VERSION = 4


# ---------------------------------------------------------------------------
# TTS text normalization
# ---------------------------------------------------------------------------
#
# Edge TTS (and most neural TTS) happily reads plain prose but stumbles on
# math-heavy narration like "时间复杂度 O(N^2)" or "a_i 与 a_{i+1}":
#   * caret `^` is read as "caret" or simply skipped;
#   * `O(...)` is sometimes read letter-by-letter or dropped entirely;
#   * underscores leak as "underscore";
#   * comparison operators like `>=`, `!=` are silent.
#
# We therefore rewrite the string that is *sent to TTS* into a pronunciation-
# friendly form. The subtitle track and the tracker's visible narration still
# use the original text, so viewers keep seeing the clean formula on screen.
#
# Design rules:
#   1. Pure regex/string replace — no external deps, no LLM calls, fully offline.
#   2. Order matters: replace big composite patterns first (O(...), sqrt(...))
#      before touching their building blocks (^, _).
#   3. Default to Chinese readout (项目默认使用 zh-CN 音色). When an English
#      voice is in use we fall back to English readings for the same symbols.
#   4. Never mutate characters inside obvious code-block fences (triple
#      backticks); narration strings in this project don't carry those,
#      but we guard for it defensively.

_GREEK_ZH = {
    "α": "阿尔法", "β": "贝塔", "γ": "伽马", "δ": "德尔塔",
    "ε": "艾普西隆", "ζ": "泽塔", "η": "伊塔", "θ": "西塔",
    "ι": "约塔", "κ": "卡帕", "λ": "拉姆达", "μ": "谬",
    "ν": "纽", "ξ": "克西", "ο": "奥密克戎", "π": "派",
    "ρ": "柔", "σ": "西格玛", "τ": "陶", "υ": "宇普西隆",
    "φ": "斐", "χ": "卡", "ψ": "普西", "ω": "欧米伽",
    "Α": "阿尔法", "Β": "贝塔", "Γ": "伽马", "Δ": "德尔塔",
    "Θ": "西塔", "Λ": "拉姆达", "Π": "派", "Σ": "西格玛",
    "Φ": "斐", "Ω": "欧米伽",
}

_GREEK_EN = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta",
    "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu",
    "ν": "nu", "ξ": "xi", "ο": "omicron", "π": "pi",
    "ρ": "rho", "σ": "sigma", "τ": "tau", "υ": "upsilon",
    "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
    "Α": "Alpha", "Β": "Beta", "Γ": "Gamma", "Δ": "Delta",
    "Θ": "Theta", "Λ": "Lambda", "Π": "Pi", "Σ": "Sigma",
    "Φ": "Phi", "Ω": "Omega",
}


def _detect_lang(voice: str | None) -> str:
    """Return 'zh' for Chinese voices, else 'en'."""
    if not voice:
        return "zh"
    head = voice.split("-", 2)
    # edge-tts voice ids look like "zh-CN-YunxiNeural" / "en-US-AriaNeural".
    if len(head) >= 2 and head[0].lower() == "zh":
        return "zh"
    return "en"


def _replace_big_o(text: str, lang: str) -> str:
    """Rewrite O(expr) / Θ(expr) / Ω(expr) with balanced-paren awareness.

    Supports nested parentheses such as ``O(N * log(N))`` by scanning for the
    matching closing paren instead of using a non-greedy regex.
    """
    labels_zh = {"O": "欧 ", "Θ": "大Theta ", "Ω": "大Omega "}
    labels_en = {"O": "big O of ", "Θ": "big theta of ", "Ω": "big omega of "}
    labels = labels_zh if lang == "zh" else labels_en

    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in labels:
            # Must be at a word boundary on the left so we don't eat 'TODO('.
            at_boundary = i == 0 or not text[i - 1].isalnum()
            # Optional whitespace between the symbol and '('.
            j = i + 1
            while j < n and text[j] == " ":
                j += 1
            if at_boundary and j < n and text[j] == "(":
                depth = 0
                k = j
                while k < n:
                    if text[k] == "(":
                        depth += 1
                    elif text[k] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                if k < n and depth == 0:
                    inner = text[j + 1 : k].strip()
                    out.append(labels[ch])
                    out.append(inner)
                    i = k + 1
                    continue
        out.append(ch)
        i += 1
    return "".join(out)


def _replace_powers(text: str, lang: str) -> str:
    """Rewrite x^2, x^3, x^k, 2^n, (n+1)^2 into spoken form."""
    if lang == "zh":
        # x^2 / x^3 / x^(expr) / x^{expr}
        text = re.sub(r"([A-Za-z0-9\)\]])\s*\^\s*2\b", r"\1 的平方", text)
        text = re.sub(r"([A-Za-z0-9\)\]])\s*\^\s*3\b", r"\1 的立方", text)
        text = re.sub(
            r"([A-Za-z0-9\)\]])\s*\^\s*\{\s*([^{}]+?)\s*\}",
            r"\1 的 \2 次方",
            text,
        )
        text = re.sub(
            r"([A-Za-z0-9\)\]])\s*\^\s*\(\s*([^()]+?)\s*\)",
            r"\1 的 \2 次方",
            text,
        )
        text = re.sub(
            r"([A-Za-z0-9\)\]])\s*\^\s*([A-Za-z0-9]+)",
            r"\1 的 \2 次方",
            text,
        )
    else:
        text = re.sub(r"([A-Za-z0-9\)\]])\s*\^\s*2\b", r"\1 squared", text)
        text = re.sub(r"([A-Za-z0-9\)\]])\s*\^\s*3\b", r"\1 cubed", text)
        text = re.sub(
            r"([A-Za-z0-9\)\]])\s*\^\s*\{\s*([^{}]+?)\s*\}",
            r"\1 to the \2",
            text,
        )
        text = re.sub(
            r"([A-Za-z0-9\)\]])\s*\^\s*\(\s*([^()]+?)\s*\)",
            r"\1 to the \2",
            text,
        )
        text = re.sub(
            r"([A-Za-z0-9\)\]])\s*\^\s*([A-Za-z0-9]+)",
            r"\1 to the \2",
            text,
        )
    return text


def _replace_subscripts(text: str, lang: str) -> str:
    """Rewrite a_i, a_{i+1}, a_0 into spoken form ('a i', 'a i+1', ...).

    Leaves snake_case identifiers like ``arr_len`` / ``max_value`` alone
    (heuristic: both sides alphabetic and length >= 2 on the right).
    """
    # a_{...}
    text = re.sub(r"([A-Za-z])_\{\s*([^{}]+?)\s*\}", r"\1 \2", text)

    # a_i / a_1 / a_12 — single char OR digit run on the right.
    text = re.sub(r"([A-Za-z])_([A-Za-z])\b", r"\1 \2", text)
    text = re.sub(r"([A-Za-z])_(\d+)\b", r"\1 \2", text)
    return text


def _replace_symbols(text: str, lang: str) -> str:
    """Replace operators / relations / misc math glyphs."""
    if lang == "zh":
        pairs = [
            (">=", " 大于等于 "),
            ("<=", " 小于等于 "),
            ("!=", " 不等于 "),
            ("==", " 等于 "),
            ("≥", " 大于等于 "),
            ("≤", " 小于等于 "),
            ("≠", " 不等于 "),
            ("≈", " 约等于 "),
            ("→", " 到 "),
            ("->", " 到 "),
            ("⇒", " 推出 "),
            ("=>", " 推出 "),
            ("∞", " 无穷 "),
            ("∑", " 求和 "),
            ("∏", " 连乘 "),
            ("√", " 根号 "),
            ("±", " 正负 "),
            ("×", " 乘以 "),
            ("÷", " 除以 "),
            ("·", " 点乘 "),
        ]
    else:
        pairs = [
            (">=", " greater than or equal to "),
            ("<=", " less than or equal to "),
            ("!=", " not equal to "),
            ("==", " equals "),
            ("≥", " greater than or equal to "),
            ("≤", " less than or equal to "),
            ("≠", " not equal to "),
            ("≈", " approximately "),
            ("→", " to "),
            ("->", " to "),
            ("⇒", " implies "),
            ("=>", " implies "),
            ("∞", " infinity "),
            ("∑", " sum of "),
            ("∏", " product of "),
            ("√", " square root of "),
            ("±", " plus or minus "),
            ("×", " times "),
            ("÷", " divided by "),
            ("·", " dot "),
        ]
    for src, dst in pairs:
        text = text.replace(src, dst)
    return text


def _replace_greek(text: str, lang: str) -> str:
    table = _GREEK_ZH if lang == "zh" else _GREEK_EN
    for src, dst in table.items():
        if src in text:
            text = text.replace(src, f" {dst} ")
    return text


def _replace_sqrt(text: str, lang: str) -> str:
    repl = "根号 \\1" if lang == "zh" else "square root of \\1"
    return re.sub(r"\bsqrt\s*\(\s*([^()]+?)\s*\)", repl, text, flags=re.IGNORECASE)


def _replace_percent(text: str, lang: str) -> str:
    if lang == "zh":
        return re.sub(r"(\d+(?:\.\d+)?)\s*%", r"百分之 \1", text)
    return re.sub(r"(\d+(?:\.\d+)?)\s*%", r"\1 percent", text)


def _replace_homophones(text: str, lang: str) -> str:
    """Fix common TTS pronunciation errors by replacing words with homophones."""
    if lang == "zh":
        pairs = [
            # Edge TTS can read 哈夫曼 with the wrong tone.  “铪” is the
            # same first-tone syllable (hā), while remaining invisible to
            # viewers because this replacement is used only for synthesis.
            ("哈夫曼", "铪夫曼"),
            ("后插法", "厚插法"),
            ("O(n)", "欧恩"),
            ("O(N)", "欧恩"),
            ("ON", "欧恩"),
            ("O(1)", "欧一"),
            ("O(log n)", "欧 log 恩"),
            ("O(logn)", "欧 log 恩"),
            ("O(n log n)", "欧恩 log 恩"),
            ("O(nlogn)", "欧恩 log 恩"),
            ("O(log^2 n)", "欧 log 平方恩"),
            ("O(log^2n)", "欧 log 平方恩"),
            ("O(logn^2)", "欧 log 恩平方"),
            ("O(n^2)", "欧恩平方"),
            ("pa", "p a"),
            # 可以在这里继续添加其他容易读错的专有名词，例如：
            # ("前插法", "钱插法"), 
        ]
        for src, dst in pairs:
            text = text.replace(src, dst)
            
        # 强制将孤立的英文字母变量替换为谐音，防止被 TTS 引擎吞掉或错读
        text = re.sub(r"(?<![A-Za-z])i(?![A-Za-z])", "艾", text)
        
    return text


def normalize_for_tts(text: str, voice: str | None = None) -> str:
    """Rewrite math-heavy narration into a pronunciation-friendly string.

    The output is intended only for the TTS engine; callers should keep the
    original text for subtitles / on-screen narration.

    Handles the common cases that cause silent or mangled speech:
        - O(N^2), Θ(n log n), Ω(1)
        - x^2, x^3, 2^n, (n+1)^2, a^{k+1}
        - a_i, a_{i+1}, x_0
        - >=, <=, !=, ==, ≥, ≤, ≠, ≈
        - ->, →, ⇒
        - √, sqrt(x), ∑, ∏, ∞, ±, ×, ÷
        - Greek letters (α β γ Δ Θ Ω ...)
        - Percent values (50% -> 百分之 50 / 50 percent)

    Args:
        text: Narration string passed by the scene.
        voice: Edge-TTS voice id used for the current scene. Determines
            whether spoken replacements should be Chinese or English.
    """
    if not text:
        return text

    lang = _detect_lang(voice)

    # 4.5. Chinese homophones fix for TTS pronunciation.
    # We apply this FIRST so that exact text like "O(n)" is caught before
    # other normalizations (like _replace_big_o) modify them.
    text = _replace_homophones(text, lang)

    # 1. Composite patterns first so their inner contents are rewritten below.
    text = _replace_big_o(text, lang)
    text = _replace_sqrt(text, lang)

    # 2. Exponents and subscripts (before generic symbol pass, which would
    #    otherwise leave stray '^' / '_' characters behind).
    text = _replace_powers(text, lang)
    text = _replace_subscripts(text, lang)

    # 3. Relational / arithmetic operators and misc math glyphs.
    text = _replace_symbols(text, lang)

    # 4. Percent and Greek letters.
    text = _replace_percent(text, lang)
    text = _replace_greek(text, lang)

    # 5. Clean up any stray carets / underscores that slipped through so
    #    edge-tts does not read them literally.
    text = text.replace("^", " ")
    # Keep '_' inside snake_case identifiers alone — but collapse a lone '_'
    # surrounded by whitespace (rare).
    text = re.sub(r"\s_\s", " ", text)

    # 6. Collapse redundant whitespace introduced by the replacements. Do not
    #    touch leading/trailing newlines that callers may rely on.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


class EdgeTTSService(SpeechService):
    """Speech service backed by the edge-tts package."""

    def __init__(
        self,
        voice: str = "zh-CN-YunxiNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        trim_silence: bool = False,
        silence_threshold_db: float = -40.0,
        min_keep_padding_ms: int = 30,
        normalize_text: bool = True,
        **kwargs: Any,
    ) -> None:
        if edge_tts is None:
            raise ImportError(
                "Missing edge-tts. Run: uv pip install edge-tts"
            ) from _EDGE_TTS_IMPORT_ERROR

        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.trim_silence = trim_silence
        self.silence_threshold_db = silence_threshold_db
        self.min_keep_padding_ms = min_keep_padding_ms
        self.normalize_text = normalize_text
        super().__init__(**kwargs)

    def get_cached_result(self, input_data, cache_dir):
        """UTF-8, locale-independent cache lookup.

        Overrides SpeechService.get_cached_result, which opens the cache with
        the platform default encoding (GBK on zh-CN Windows) and crashes on our
        UTF-8 Chinese narration. A missing/corrupt cache returns None so the
        caller simply regenerates the clip instead of aborting the render.
        """
        json_path = Path(cache_dir) / DEFAULT_VOICEOVER_CACHE_JSON_FILENAME
        if not os.path.exists(json_path):
            return None
        # Indexed lookup: the file is parsed once per revision instead of once
        # per voiceover block, and matched by key instead of scanned linearly.
        return _cache_index(str(json_path)).get(_entry_key(input_data))

    async def _stream_once(self, text: str) -> tuple[bytes, list[dict[str, Any]]]:
        """Run a single edge-tts websocket session and buffer audio in memory."""
        assert edge_tts is not None
        communicator = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch,
        )

        audio = bytearray()
        word_boundaries: list[dict[str, Any]] = []
        running_offset = 0
        async for chunk in communicator.stream():
            chunk_type = chunk.get("type")
            if chunk_type == "audio":
                audio.extend(chunk["data"])
                continue

            if chunk_type not in {"WordBoundary", "SentenceBoundary"}:
                continue

            text_part = chunk.get("text", "")
            current_offset = text.find(text_part, running_offset)
            if current_offset == -1:
                current_offset = running_offset
            running_offset = current_offset + len(text_part)

            word_boundaries.append(
                {
                    "audio_offset": int(chunk.get("offset", 0)),
                    "duration_milliseconds": int(chunk.get("duration", 0) / 10_000),
                    "text_offset": current_offset,
                    "word_length": len(text_part),
                    "text": text_part,
                    "boundary_type": "Word" if chunk_type == "WordBoundary" else "Sentence",
                }
            )

        if not audio:
            raise RuntimeError("edge-tts returned empty audio stream")

        return bytes(audio), word_boundaries

    async def _synthesize_async(self, text: str, output_path: Path) -> list[dict[str, Any]]:
        """Synthesize with exponential backoff + jitter retry on transient errors.

        The Bing speech websocket endpoint frequently throttles concurrent
        connections from the same IP (parallel scene renders) with empty
        frames or connection timeouts; staggered retries recover cleanly.
        """
        max_attempts = 5
        base_delay = 0.8  # seconds; actual delays: ~0.8, 1.6, 3.2, 6.4, 12.8 + jitter
        last_exc: BaseException | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                audio_bytes, word_boundaries = await asyncio.wait_for(
                    self._stream_once(text), timeout=15.0
                )
            except _RETRYABLE_EXC as exc:
                last_exc = exc
                if attempt >= max_attempts:
                    break
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0.0, 0.5)
                logger.warning(
                    "edge-tts attempt %d/%d failed (%s: %s); retrying in %.2fs",
                    attempt,
                    max_attempts,
                    type(exc).__name__,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                continue

            with output_path.open("wb") as audio_file:
                audio_file.write(audio_bytes)
            if attempt > 1:
                logger.info("edge-tts recovered on attempt %d", attempt)
            return word_boundaries

        assert last_exc is not None
        raise last_exc

    def generate_from_text(
        self, text: str, cache_dir: str = None, path: str = None, **kwargs: Any
    ) -> dict[str, Any]:
        if cache_dir is None:
            cache_dir = self.cache_dir

        cache_dir_path = Path(cache_dir)
        cache_dir_path.mkdir(parents=True, exist_ok=True)

        # Visible narration (used for subtitle / tracker text) — keeps the
        # pretty on-screen form like "O(N^2)". The TTS-facing variant below
        # is rewritten into a pronunciation-friendly string so edge-tts
        # actually reads formulas instead of silently dropping them.
        input_text = remove_bookmarks(text)
        if self.normalize_text:
            tts_text = normalize_for_tts(input_text, voice=self.voice)
            if tts_text != input_text:
                logger.debug(
                    "EdgeTTS normalized narration for pronunciation:\n  in:  %s\n  out: %s",
                    input_text,
                    tts_text,
                )
        else:
            tts_text = input_text

        input_data = {
            "input_text": tts_text,
            "service": "edge-tts",
            "cache_version": _CACHE_VERSION,
            "config": {
                "voice": self.voice,
                "rate": self.rate,
                "volume": self.volume,
                "pitch": self.pitch,
                "trim_silence": self.trim_silence,
                "silence_threshold_db": self.silence_threshold_db,
                "min_keep_padding_ms": self.min_keep_padding_ms,
                "normalize_text": self.normalize_text,
            },
        }

        cached_result = self.get_cached_result(input_data, cache_dir_path)
        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        output_path = cache_dir_path / audio_path
        if output_path.exists():
            output_path.unlink()

        try:
            word_boundaries = asyncio.run(self._synthesize_async(tts_text, output_path))
        except RuntimeError as runtime_error:
            logger.error("EdgeTTSService synthesis failed: %s", runtime_error)
            raise
        except Exception as synth_error:
            logger.error("edge-tts request failed: %s", synth_error)
            raise RuntimeError("edge-tts synthesis failed") from synth_error

        if self.trim_silence:
            leading_trim_ms = self._trim_silence_in_place(output_path)
            if leading_trim_ms:
                # Shift word boundary offsets so post-trim offsets stay accurate.
                shift_100ns = int(leading_trim_ms * 10_000)
                for boundary in word_boundaries:
                    boundary["audio_offset"] = max(
                        0, int(boundary.get("audio_offset", 0)) - shift_100ns
                    )

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
            "word_boundaries": word_boundaries,
        }

    def _trim_silence_in_place(self, audio_path: Path) -> int:
        """Trim leading/trailing silence from an mp3 file in place.

        Returns the number of leading milliseconds that were trimmed, so
        callers can shift word-boundary offsets accordingly.
        """
        try:
            segment = AudioSegment.from_file(audio_path)
        except Exception as exc:
            logger.warning("Failed to load audio for silence trim %s: %s", audio_path, exc)
            return 0

        original_ms = len(segment)
        if original_ms == 0:
            return 0

        leading_ms = detect_leading_silence(segment, silence_threshold=self.silence_threshold_db)
        trailing_ms = detect_leading_silence(
            segment.reverse(), silence_threshold=self.silence_threshold_db
        )

        keep_pad = max(0, int(self.min_keep_padding_ms))
        start_ms = max(0, leading_ms - keep_pad)
        end_ms = max(start_ms + 1, original_ms - max(0, trailing_ms - keep_pad))

        if start_ms == 0 and end_ms == original_ms:
            return 0

        trimmed = segment[start_ms:end_ms]
        try:
            trimmed.export(audio_path, format="mp3")
        except Exception as exc:
            logger.warning("Failed to write trimmed audio %s: %s", audio_path, exc)
            return 0

        logger.info(
            "EdgeTTS trim silence: %s (leading %dms, trailing %dms, original %dms)",
            audio_path.name,
            start_ms,
            original_ms - end_ms,
            original_ms,
        )
        return start_ms
