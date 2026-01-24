from vertexai.preview.vision_models import VideoGenerationModel, Image
import vertexai
import os

def test_veo_31():
    project_id = "winged-precept-458206-j1"
    location = "us-central1"
    
    try:
        vertexai.init(project=project_id, location=location)
        
        # Exact model name from user screenshot
        model_name = "veo-3.1-fast-generate-001" 
        print(f"Loading model: {model_name}")
        model = VideoGenerationModel.from_pretrained(model_name)
        
        # We need an input image. Let's use the one we generated earlier if it exists, or generate a dummy?
        # Let's hope 'test_dino.png' exists from previous test, otherwise generating video from text.
        
        prompt = "A cute fluffy bunny eating a giant red berry, cartoon style, animation, moving, 4k"
        print("Generating video from text (Veo 3.1)...")
        
        response = model.generate_video(
            prompt=prompt,
        )
        
        output_file = "veo_video.mp4"
        response.save(output_file)
        print(f"Veo Video saved to {output_file}")
        
    except Exception as e:
        print(f"Veo 3.1 Error: {e}")

if __name__ == "__main__":
    test_veo_31()
