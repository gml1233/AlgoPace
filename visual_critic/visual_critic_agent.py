import cv2
import os
import glob
import base64
from pathlib import Path
from openai import OpenAI
from typing import Dict, Any, Tuple

class VisualCriticAgent:
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def extract_keyframes(self, video_path: str, num_frames: int = 4) -> list:
        cap = cv2.VideoCapture(video_path)
        frames = []
        if not cap.isOpened():
            return frames
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            return frames
            
        step = max(total_frames // num_frames, 1)
        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                # Run OpenCV low-level spatial error checks
                cv_errors = self.detect_low_level_errors(frame)
                if cv_errors:
                    frame_cv_errors.extend(cv_errors)
                    
                # Convert to base64
                _, buffer = cv2.imencode('.jpg', frame)
                base64_image = base64.b64encode(buffer).decode('utf-8')
                frames.append(f"data:image/jpeg;base64,{base64_image}")
            if len(frames) >= num_frames:
                break
        cap.release()
        return frames

    def critique(self, video_path: str) -> Tuple[bool, str]:
        """
        Critiques a video visually using a Vision Language Model.
        Returns:
            Tuple[bool, str]: (is_passed, feedback_if_failed)
        """
        frames = self.extract_keyframes(video_path)
        if not frames:
            return False, "Could not extract frames from video for critique."

        content = [
            {"type": "text", "text": "Observe these keyframes from a Manim algorithm animation. "
                                     "Does the animation contain any severe visual errors, such as text "
                                     "severely overlapping, objects going completely off screen, or garbled rendering? "
                                     "If there are major errors, describe what they are so the Manim code can be fixed. "
                                     "If the frames look visually correct and well-arranged, reply exactly with 'PASS'."}
        ]
        
        for frame in frames:
            content.append({
                "type": "image_url",
                "image_url": {"url": frame}
            })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=300
            )
            feedback = response.choices[0].message.content.strip()
            if "PASS" in feedback.upper() and len(feedback) < 20: # simple heuristics
                return True, "Looks good."
            else:
                return False, feedback
        except Exception as e:
            return False, f"Vision critique failed with API error: {e}"
