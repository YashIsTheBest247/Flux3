import json
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from google import genai
from google.genai import types

class VideoScriptGenerator:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

        self.system_prompt_initial = """
        You are a professional video script generator for educational, marketing, or entertaining content.  
        Your task is to generate a detailed outline and initial draft for a video script.
        Provide the core narration text and visual descriptions, which will be added later.
        Visual Description should not contain animations, moving images, transitions, or video effects description.
        Output a JSON structure with these keys, but *without timestamps, speed, pitch, or detailed visual parameters* (these will be added in a later stage):

        {
            "topic": "Topic Name",
            "overall_narrative": "A concise summary of the entire video's storyline.",
            "key_sections": [
                {
                    "section_title": "Descriptive title for this section",
                    "narration_text": "The complete text to be spoken in this section.",
                    "visual_description": "A general description of the visuals for this section."
                }
            ]
        }
        """

        self.system_prompt_segmentation = """
        You are a professional video script segmenter.  
        Your task is to take an existing video script draft and break it down into precise, timestamped segments for both audio and visuals, adhering to strict formatting and parameter guidelines.
        Rules for Segmentation:
        
        1. Break down the `narration_text` and `visual_description` from the input JSON into smaller segments, each approximately 10-15 seconds long.
        2. Generate timestamps ("00:00", "00:15", "00:30", etc.) for each segment in both `audio_script` and `visual_script`.
        3. Maintain *strict synchronization*: The `timestamp` values *must* be identical for corresponding audio and visual segments, and the number of segments in audio_script *must be same* as the number of segments in visual_script.
        4. For each visual segment, expand the general `visual_description` into a *simple and realistic* `prompt` suitable for finding images online. The `prompt` must be exactly 5 words long. Include a corresponding `negative_prompt`. 
        5. Ensure the `prompt` describes a realistic, static image that can be easily found on stock image websites or through web scraping. Avoid abstract or overly complex descriptions.
        6. Choose appropriate values for `speaker`, `speed`, `pitch`, and `emotion` for each audio segment.
        7. Remove unnecessary parameters like `style`, `guidance_scale`, `steps`, `seed`, `width`, and `height` since we are not generating images with Stable Diffusion.
        8. Ensure visual continuity: Use consistent and logical descriptions across consecutive visual segments.
        9. Adhere to the specified ranges for numerical parameters (speed, pitch).
        10. Validate JSON structure before output with the example_json given.

        Input JSON Structure (from previous stage):

        {
            "topic": "Topic Name",
            "overall_narrative": "...",
            "key_sections": [
                {
                    "section_title": "...",
                    "narration_text": "...",
                    "visual_description": "..."
                }
            ]
        }
        
        Output JSON Structure (with all required fields):

        {
            "topic": "Topic Name",
            "description": "description of video",
            "audio_script": [{
                "timestamp": "00:00",
                "text": "Narration text",
                "speaker": "default|narrator_male|narrator_female",
                "speed": 0.9-1.1,
                "pitch": 0.9-1.2,
                "emotion": "neutral|serious|dramatic|mysterious|informative"
            }],
            "visual_script": [{
                "timestamp_start": "00:00",
                "timestamp_end": "00:05",
                "prompt": " a realistic image, e.g., 'Wide panoramic football stadium fans cheering'",
                "negative_prompt": "Avoid abstract images, moving objects, or overly complex designs."
            }]
        }
        """

    def _search_web(self, query: str) -> str:
        """
        Fetch search results using BeautifulSoup and Requests.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            snippets = [div.text for div in soup.find_all("div", class_="BNeawe s3v9rd AP7Wnd")]
            return " ".join(snippets[:5])
        except Exception as e:
            print(f"Error fetching web results: {e}")
            return ""

    def _generate_content(self, prompt: str, system_prompt: str) -> str:
        """
        Generate content using the Gemini API.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=2000,
                ),
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {str(e)}")

    def _extract_json(self, raw_text: str) -> Dict:
        """
        Extract JSON from raw text output.
        """
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            try:
                json_match = re.search(r'```json\n(.*?)\n```', raw_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                return json.loads(json_match.group()) if json_match else {}
            except Exception as e:
                raise ValueError(f"JSON extraction failed: {str(e)}")

    def generate_script(self, topic: str, duration: int = 60, key_points: Optional[List[str]] = None) -> Dict:
        """
        Generate a video script based on the given topic, duration, and key points.
        
        Args:
            topic (str): The topic of the video.
            duration (int): The duration of the video in seconds (default: 60).
            key_points (Optional[List[str]]): Optional list of key points to include in the script.
        
        Returns:
            Dict: A structured video script in JSON format.
        """
        # Step 1: Fetch web context for the topic
        web_context = self._search_web(topic)
        
        # Step 2: Generate the initial script outline
        initial_prompt = f"""Generate an initial video script outline for a {duration}-second video about: {topic}.
        Key Points: {key_points or 'Comprehensive coverage'}
        Additional Context: {web_context}
        Focus on the overall narrative and key sections, but do *not* include timestamps or detailed technical parameters yet."""
        
        raw_initial_output = self._generate_content(initial_prompt, self.system_prompt_initial)
        initial_script = self._extract_json(raw_initial_output)
        
        # Step 3: Segment the script into timestamped audio and visual segments
        segmentation_prompt = f"""
        Here is the initial script draft:
        {json.dumps(initial_script, indent=2)}
        Now, segment this script into 5-10 second intervals, adding timestamps and all required audio/visual parameters. The total duration should be approximately {duration} seconds.
        """
        
        raw_segmented_output = self._generate_content(segmentation_prompt, self.system_prompt_segmentation)
        segmented_script = self._extract_json(raw_segmented_output)
        
        # Step 4: Add the topic to the segmented script
        segmented_script['topic'] = initial_script['topic']
        
        return segmented_script

    def refine_script(self, existing_script: Dict, feedback: str) -> Dict:
        prompt = f"""Refine this script based on feedback:
        Existing Script: {json.dumps(existing_script, indent=2)}
        Feedback: {feedback}
        """
        raw_output = self._generate_content(prompt, self.system_prompt_segmentation)
        return self._extract_json(raw_output)
    
    def save_script(self, script: Dict, filename: str) -> None:
        with open(filename, 'w') as f:
            json.dump(script, f, indent=2)
            print(f"Script saved to {filename}")