import time
from google import genai
from google.genai import types
import os

class VeoWrapper:
    def __init__(self, project_id="winged-precept-458206-j1", location="us-central1"):
        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = "veo-3.1-generate-001"
            print("VeoWrapper initialized.")
        except Exception as e:
            print(f"Failed to init VeoWrapper: {e}")
            self.client = None

    def generate_video(self, prompt, output_path):
        if not self.client:
             print("Veo client not ready.")
             return None

        print(f"Generating Veo video for prompt: {prompt[:50]}...")
        
        try:
            source = types.GenerateVideosSource(
                prompt=prompt,
            )

            config = types.GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1, # Generate 1 to save cost/time
                duration_seconds=8, # 8 seconds per clip
                person_generation="allow_all",
                generate_audio=False, # We generate our own narration
                resolution="720p",
                seed=0,
            )

            operation = self.client.models.generate_videos(
                model=self.model_name, source=source, config=config
            )

            # Polling
            while not operation.done:
                print("Veo is generating... waiting 10s")
                time.sleep(10)
                operation = self.client.operations.get(operation)

            response = operation.result
            if not response or not response.generated_videos:
                print("No Veo videos generated.")
                return None

            # Save the first video
            video_result = response.generated_videos[0]
            if video_result.video:
                # Save bytes to file
                video_result.video.save(output_path)
                print(f"Veo video saved to: {output_path}")
                return output_path
                
        except Exception as e:
            print(f"Veo Generation Error: {e}")
            return None
