from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
# Note: Video generation is often under a specific class or endpoint.
# Trying to find VideoGenerationModel or similar.
try:
    from vertexai.preview.vision_models import VideoGenerationModel
except ImportError:
    print("VideoGenerationModel not found in SDK.")
    VideoGenerationModel = None

def test_veo():
    project_id = "winged-precept-458206-j1"
    location = "us-central1"
    
    vertexai.init(project=project_id, location=location)
    
    if not VideoGenerationModel:
        print("SDK does not support VideoGenerationModel class.")
        return

    try:
        # Common model names: "text-to-video", "video-generation"
        # Veo might be "veo-001" or similar if whitelisted.
        print("Attempting to load text-to-video model...")
        model = VideoGenerationModel.from_pretrained("text-to-video")
        
        print("Generating video...")
        response = model.generate_video(
            prompt="A cute fluffy bunny eating a giant red berry, cartoon style, animation",
            number_of_videos=1,
            aspect_ratio="16:9"
        )
        
        output_file = "test_video.mp4"
        response[0].save(output_file)
        print(f"Video saved to {output_file}")
        
    except Exception as e:
        print(f"Video Generation Error: {e}")

if __name__ == "__main__":
    test_veo()
