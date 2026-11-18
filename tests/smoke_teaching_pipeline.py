"""Offline pipeline smoke test. Run with the project's Manim environment activated."""
import math
import os
import re
import struct
import sys
import wave
from pathlib import Path
root = Path(__file__).resolve().parents[1]
os.chdir(root)
sys.path[:0] = [str(root), str(root / "tests")]
os.environ.update(OPENROUTER_API_KEY="offline", GOOGLE_API_KEY="offline", LANGFUSE_TRACING_ENABLED="false")
from unittest.mock import patch
from test_teaching_planner import fixtures
from pipeline import Pipeline
from agents.concept_interpreter import ConceptInterpreterAgent
from agents.manim_agent import ManimAgent
req, design, graph = fixtures()
p = Pipeline()
p.manim_agent.config.lint_enabled = False
p.manim_agent.config.render_fix_enabled = False
p.manim_agent.config.render_regen_enabled = False
p.manim_agent.renderer.max_retries = 0
wav = root / 'tmp' / 'smoke.wav'
wav.parent.mkdir(exist_ok=True)
with wave.open(str(wav),'wb') as f:
    f.setparams((1,2,16000,0,'NONE',''))
    f.writeframes(b''.join(struct.pack('<h',int(500*math.sin(i*.1))) for i in range(16000)))
def code(system_prompt, **kwargs):
    name = re.search(r'VoiceoverScene class named (\w+)',system_prompt)[1]
    assert 'sorted prefix' in system_prompt and 'from_snapshot' in system_prompt
    return f"""<manim>
from manim import *
class {name}(Scene):
    def construct(self):
        self.add(Text("12 < 21"))
        self.add_sound({str(wav)!r})
        self.add_subcaption("Values up to 12 are too small.", duration=1)
        self.wait(1.2)
</manim>"""
with patch.object(ConceptInterpreterAgent, '_call_llm_structured', return_value=design.model_dump()), patch.object(ManimAgent, '_call_llm_structured', return_value=graph.model_dump()), patch.object(ManimAgent, '_call_llm', side_effect=code):
    r = p.run("binary search", teaching_request=req, render_quality="l")
    assert r["status"] == "success", r["error"]
    assert Path(r["video_result"]["output_path"]).is_file()
    assert r['srt_content'] and r['manim_source_code']
    print("SMOKE OK",r["video_result"]["output_duration"])
