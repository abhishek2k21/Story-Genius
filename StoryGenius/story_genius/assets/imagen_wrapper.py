from vertexai.preview.vision_models import ImageGenerationModel
import vertexai

class ImagenWrapper:
    def __init__(self, project_id="winged-precept-458206-j1", location="us-central1"):
        try:
            vertexai.init(project=project_id, location=location)
            self.model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        except Exception as e:
            print(f"Failed to init Imagen: {e}")
            self.model = None

    def generate_image(self, prompt, output_path):
        if not self.model:
            print("Imagen model not initialized.")
            return None
        
        try:
            print(f"Generating image for: {prompt}")
            images = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="16:9",
                language="en"
            )
            images[0].save(location=output_path, include_generation_parameters=False)
            return output_path
        except Exception as e:
            print(f"Imagen Generation Error: {e}")
            return None
