# AlgoT2V

**AI-powered STEM concept visualizer that generates narrated educational animations using Manim, LLMs, and multimodal AI.**


## Features

- 🎬 **Automated Animation Generation**: Convert STEM concepts to Manim animations
- 🧠 **Multi-Agent Architecture**: Concept interpreter + Manim code generator agents
- 🎙️ **AI Narration**: Narration is generated directly in Manim `VoiceoverScene` code
- 🔊 **Text-to-Speech**: Powered by `manim-voiceover` + custom Edge TTS service (Edge/OpenAI/ElevenLabs/Coqui)
- ⚡ **Parallel Processing**: Concurrent scene code generation for faster output
- 🎨 **Gradio Web Interface**: Simple browser-based UI for easy interaction
- 🧹 **Auto Cleanup**: Removes temporary files after successful generation

---

## Demo

https://github.com/kesiyuan0927/AlgoT2V

---

## Installation

### Prerequisites

**System Requirements:**
- Python 3.10 – 3.12 (3.13+ not tested; `pydub` still relies on the stdlib `audioop` module)
- FFmpeg (for video processing)
- LaTeX (for mathematical notation in animations)
- SoX (optional — silences a noisy warning from `manim-voiceover`; not required for rendering. See [Step 1c](#step-1c-optional--install-sox-to-silence-the-voiceover-warning).)

**Python 3.12 note**: the optional Coqui TTS backend (`TTS==0.22.0`) does not
build on Python 3.12+. The default installation skips it and you won't need
it unless you explicitly set `TTS_PROVIDER=coqui`.

**API Keys Required:**
- [OpenRouter API Key](https://openrouter.ai/) (for LLM reasoning)
- [Google AI Studio API Key](https://aistudio.google.com/app/apikey) (for multimodal script generation)
- One voice provider key: OpenAI or ElevenLabs (`edge` mode uses free online Edge TTS — no key needed)

---

### Step 1: Install System Dependencies

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install FFmpeg
brew install ffmpeg

# Install LaTeX (required for math rendering in Manim)
brew install --cask mactex

# After LaTeX installation, update PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="/Library/TeX/texbin:$PATH"
source ~/.zshrc  # or source ~/.bash_profile
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install FFmpeg
sudo apt install ffmpeg

# Install LaTeX (full TeX Live distribution)
sudo apt install texlive-full

# Alternative: minimal LaTeX install (faster, but may miss some packages)
# sudo apt install texlive texlive-latex-extra texlive-fonts-extra texlive-science
```

#### Windows
```powershell
# Install Chocolatey if not already installed (run PowerShell as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install FFmpeg
choco install ffmpeg

# Install MiKTeX (LaTeX distribution for Windows)
choco install miktex

# After installation, restart your terminal and update PATH if needed
```

**Verify installations:**
```bash
ffmpeg -version
latex --version
```

---

### Step 1c (optional) — Install SoX to silence the voiceover warning

`manim-voiceover` pulls in the `sox` Python binding, which prints a harmless
but repeated `SoX could not be found!` warning whenever the native `sox`
binary is missing. Rendering and Edge TTS still work without it.

**Windows (one-liner, no admin required):**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_sox_windows.ps1
```
The script downloads SoX 14.4.2 from SourceForge mirrors to
`%LOCALAPPDATA%\sox`, adds it to the user `PATH`, and is idempotent. After
it finishes, open a **new** PowerShell window so future `python app.py`
processes inherit the new `PATH`.

**macOS:** `brew install sox`

**Linux (Debian/Ubuntu):** `sudo apt install sox`

---

### Step 2: Clone Repository

```bash
# IMPORTANT: --recurse-submodules pulls third_party/manim-linter, which
# requirements.txt installs with `pip install -e ./third_party/manim-linter`.
# Without it, `pip install -r requirements.txt` will fail on that line.
git clone --recurse-submodules https://github.com/kesiyuan0927/AlgoT2V.git
cd AlgoT2V

# If you already cloned without submodules, run:
git submodule update --init --recursive
```

---

### Step 3: Install Python Environment (Using UV - Recommended)

We recommend using [UV](https://github.com/astral-sh/uv) for fast, reliable Python package management.

#### Install UV

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Create Virtual Environment and Install Dependencies

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Optional: verify Manim static linter (manim-lint) from submodule
manim-lint --help
```

**Alternative (using pip):**
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

### Step 4: Configure API Keys

1. Copy the example environment file:
   ```bash
   # macOS / Linux
   cp .env.example .env

   # Windows PowerShell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and fill in at least the two required keys:
   ```bash
   OPENROUTER_API_KEY=your_openrouter_key_here
   GOOGLE_API_KEY=your_google_ai_key_here
   # Defaults below are fine; override only if needed.
   TTS_PROVIDER=edge
   EDGE_TTS_VOICE=zh-CN-YunxiNeural
   ```

See [`.env.example`](.env.example) for every tunable (TTS backends, Manim
quality, render-failure auto-fix rounds, Langfuse tracing, etc.).

**Where to get API keys:**
- **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai/) and create an API key
- **Google AI Studio**: Get a Gemini key from [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **OpenAI / ElevenLabs**: Optional alternatives; only needed if you switch `TTS_PROVIDER`
- **Azure Speech**: Not required for default `edge` mode

---

### Step 5: Verify Manim Installation

Test that Manim is properly installed:

```bash
manim --version
```

If Manim is not found, ensure your virtual environment is activated and reinstall:
```bash
uv pip install --force-reinstall manim
```

---

## Usage

### Batch render existing Manim scripts with the AIgo environment

From the repository root, choose a source directory and video destination:

```powershell
python render_aigo.py --source "codetest/python版" --output "D:/videos" -q m
```

The script searches subdirectories, renders every scene in each animation file,
and keeps the source directory structure under the destination. Manim stores each
video under `videos/<script name>/<resolution>/<scene name>.mp4`. Use `--dry-run`
to preview the commands or pass a single `.py` file to `--source`. Rendering
continues if one file fails and exits with a nonzero status when any file fails.

### Launch Gradio Web Interface

```bash
python app.py
```

The Gradio interface will open in your browser at `http://127.0.0.1:7860`

### Using the Interface

1. **Enter a STEM concept** in the text box (e.g., "Explain QuickSort algorithm", "Demonstrate gradient descent", "Show Bayes' theorem")
2. **Click "Generate Animation"**
3. **Wait for the pipeline** to complete (typically 3-5 minutes depending on complexity)
4. **Watch the generated video** with synchronized narration

### Example Prompts

```
- Explain bubble sort algorithm
```

---

## Architecture

```
User Input (STEM concept via Gradio)
  ↓
Concept Interpreter Agent (structured analysis)
  ↓
Manim Agent (scene planning → parallel code generation → rendering)
  ↓
Concatenated Voiceover Animation (audio embedded by manim-voiceover)
  ↓
Voiceover timing aggregation → SRT
  ↓
Video Compositor (burn subtitles, keep embedded audio)
  ↓
Display in Gradio
```

### Technology Stack

- **UI**: Gradio
- **Animation**: Manim Community Edition
- **LLMs**: 
  - Reasoning: Claude Sonnet 4.5 via OpenRouter
  - Multimodal: Gemini 2.5 Flash
- **TTS**: manim-voiceover (`edge` maps to custom `EdgeTTSService`)
- **Media Processing**: FFmpeg

---

## Configuration

Prefer `.env` for secrets and per-machine overrides; use `config.py` only when
you need to change the typed defaults. The most useful knobs:

- **Animation quality**: `manim_quality` / `MANIM_QUALITY` (`l` 480p15 | `m` 720p30 | `h` 1080p30 | `p` 1080p60 | `k` 1440p60)
- **LLM models**: `reasoning_model`, `multimodal_model`
- **TTS settings**: `tts_provider`, `edge_tts_voice`, `openai_voice`, `elevenlabs_voice_id`
- **Video settings**: `video_codec`, `video_crf`, `audio_bitrate`
- **Timeouts and retries**: Various `*_timeout` and `*_max_retries` settings
- **Static lint + LLM fix** (before rendering): `MANIM_LINT_ENABLED`, `MANIM_LINT_MAX_FIX_ATTEMPTS`
- **Runtime render auto-fix** (after rendering crashes): `MANIM_RENDER_FIX_ENABLED`, `MANIM_RENDER_FIX_MAX_ATTEMPTS` — when Manim's subprocess exits non-zero (e.g. an LLM-generated `TypeError` the static lint cannot catch), the agent feeds stderr back to the LLM and re-renders with the patched scene up to N extra times. Default: 2 rounds.

---

## Output Structure

```
output/
├── analyses/       # Concept analysis JSON files
├── scene_codes/    # Generated Manim code (cleaned up after success)
├── scenes/         # Individual scene videos (cleaned up after success)
├── animations/     # Concatenated animations (voiceover embedded)
├── scripts/        # Timestamped SRT narration scripts
└── final/          # Final videos with narration ✅ (KEPT)
```

**Note:** Temporary files are automatically cleaned up after successful video generation. Only final videos and scripts are preserved.

---

## Troubleshooting

### Common Issues

**1. "LaTeX not found" error**
```bash
# Verify LaTeX installation
latex --version

# macOS: Ensure PATH includes LaTeX
export PATH="/Library/TeX/texbin:$PATH"

# Linux: Reinstall TeX Live
sudo apt install texlive-full
```

**2. "FFmpeg not found" error**
```bash
# Verify FFmpeg installation
ffmpeg -version

# Reinstall if needed (macOS)
brew reinstall ffmpeg

# Linux
sudo apt reinstall ffmpeg
```

**3. "Manim command not found"**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Reinstall Manim
uv pip install --force-reinstall manim
```

**4. API Key errors**
- Verify `.env` file exists and contains valid API keys
- Check API key quotas/limits on respective platforms
- Ensure no extra spaces or quotes around API keys in `.env`

**5. Out of memory errors**
- Reduce animation quality in `config.py`: `manim_quality = "720p30"`
- Reduce `manim_max_scene_duration` to simplify scenes
- Close other applications to free up RAM

**6. Slow generation**
- First run is slower due to LaTeX package downloads
- Subsequent runs are faster as packages are cached
- Complex concepts naturally take longer (3-5 minutes average)

**7. `ModuleNotFoundError: No module named 'manim_voiceover'` during rendering**

The rendering subprocess needs `manim-voiceover` installed in the **same
Python environment** that runs `python app.py`. If `pip install -r
requirements.txt` silently skipped it because Coqui failed to compile on
Python 3.12, install the core package directly:

```bash
pip install "manim-voiceover==0.3.4.post1"
```

Do NOT add `[coqui]` or `TTS==0.22.0` on Python 3.12+ — they can't build.

**8. `RuntimeError: edge-tts synthesis failed` / `ConnectionTimeoutError` / `ParseError: no element found`**

Bing's free Edge TTS endpoint throttles concurrent WebSocket connections
from the same IP. When 4 scenes render in parallel this causes 2-4 of them
to fail. The project's `EdgeTTSService` (generation/tts/edge_service.py)
already retries with exponential backoff + jitter against the right
exception types, but that logic needs `edge-tts >= 7.2.8`:

```bash
pip install --upgrade "edge-tts>=7.2.8"
```

**9. `TypeError: Cannot compare ManimColor with str` / `AttributeError` / other runtime errors in generated scenes**

These are LLM-generated code bugs that static lint cannot catch. The agent
ships with an **automatic render-failure LLM fix loop**: when Manim exits
non-zero, the stderr is fed back to the LLM, a corrected scene file is
generated, and the scene is re-rendered (up to 2 extra rounds by default).
Look for `[Worker] 渲染失败，准备 LLM 修复` in the logs. You can tune the
number of repair rounds via `MANIM_RENDER_FIX_MAX_ATTEMPTS` in `.env`; set
to `0` to disable entirely.

**10. `SoX could not be found!` warnings in rendering logs**

Cosmetic only — rendering still succeeds. Silence it by installing SoX via
[Step 1c](#step-1c-optional--install-sox-to-silence-the-voiceover-warning).
On Windows, remember to open a **new** terminal after running the
installer so the updated `PATH` propagates to `python app.py`.

**11. `manim-lint not found and third_party/manim-linter/src missing; skipping lint`**

The `third_party/manim-linter` submodule wasn't initialized. Fix:
```bash
git submodule update --init --recursive
pip install -e ./third_party/manim-linter
```
Static lint is optional; when the submodule is missing the agent skips it
and falls back to the runtime render-fix loop (Troubleshooting #9).

---

## Development

### Project Structure

```
AlgoT2V/
├── agents/                  # AI agents
│   ├── concept_interpreter.py   # Analyzes and decomposes STEM concepts
│   ├── manim_agent.py            # Generates and renders Manim animations
│   └── manim_models.py           # Data models for animation pipeline
├── generation/              # Content generation
│   ├── script_generator.py       # Multimodal narration generation
│   ├── audio_synthesizer.py      # TTS audio synthesis
│   └── video_compositor.py       # Final video composition
├── rendering/               # Animation rendering
│   └── manim_renderer.py         # Manim code execution
├── utils/                   # Utilities
│   └── validators.py             # Input validation
├── config.py                # Centralized configuration
├── pipeline.py              # Main orchestration pipeline
├── app.py                   # Gradio web interface
└── requirements.txt         # Python dependencies
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under a non-commercial License - see the LICENSE file for details.

---

## Acknowledgments

- **Manim Community**: For the amazing mathematical animation engine
- **3Blue1Brown**: For inspiring educational math visualizations
- **Anthropic, Google, ElevenLabs**: For powerful AI APIs

---

## Citation

If you use AlgoT2V in your research or project, please cite:

```bibtex
@software{AlgoT2V2026,
  author = {KeSiyuan},
  title = {AlgoT2V: AI-Powered DataStructure Concept Visualizer},
  year = {2025},
  url = {https://github.com/kesiyuan0927/AlgoT2V}
}

**⭐ Star this repo if you find it useful!**
