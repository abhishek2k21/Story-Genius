from vertexai.preview.vision_models import ImageGenerationModel
import vertexai

def test_imagen():
    project_id = "winged-precept-458206-j1"
    location = "us-central1"
    
    try:
        vertexai.init(project=project_id, location=location)
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        print("Generating test image...")
        images = model.generate_images(
            prompt="A cute cartoon dinosaur dancing in a forest, vibrant colors, 4k",
            number_of_images=1,
            language="en",
            aspect_ratio="16:9",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )
        
        output_file = "test_dino.png"
        images[0].save(location=output_file, include_generation_parameters=False)
        print(f"Image saved to {output_file}")
        
    except Exception as e:
        print(f"Imagen Error: {e}")

if __name__ == "__main__":
    test_imagen()
