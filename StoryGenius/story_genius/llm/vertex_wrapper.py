import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import os

class VertexLLM:
    def __init__(self, project_id="winged-precept-458206-j1", location="us-central1", model_name="gemini-2.0-flash-001"):
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self._initialize()

    def _initialize(self):
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_name)
            print(f"Vertex AI initialized with project {self.project_id} and model {self.model_name}")
        except Exception as e:
            print(f"Failed to initialize Vertex AI: {e}")
            raise

    def generate_content(self, prompt, system_instruction=None, temperature=0.7):
        """
        Generates content using Vertex AI Gemini model.
        """
        try:
            # Note: system_instruction is supported in newer SDK versions for Gemini 1.5
            # If creating a chat session, system_instruction goes into history or model init.
            # For simplicity, we prepend it to the prompt if provided, or use the model's system_instruction arg if available.
            
            # Re-init model with system instruction if needed (expensive) or just prepend.
            # Efficient way: instantiate model with system_instruction if provided.
            if system_instruction:
                 model = GenerativeModel(self.model_name, system_instruction=[system_instruction])
            else:
                 model = self.model

            generation_config = {
                "max_output_tokens": 8192,
                "temperature": temperature,
                "top_p": 0.95,
            }

            safety_settings = [
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                ),
            ]

            response = model.generate_content(
                [prompt],
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=False,
            )

            return response.text
        except Exception as e:
            print(f"Error generating content with Vertex AI: {e}")
            # Fallback or re-raise
            raise

if __name__ == "__main__":
    # Test the wrapper
    llm = VertexLLM()
    print(llm.generate_content("Tell me a one sentence story about a brave toaster."))
