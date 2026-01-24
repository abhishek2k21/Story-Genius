try:
    from google import genai
    from google.genai import types
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")

try:
    print("Initializing client...")
    client = genai.Client(vertexai=True, project="winged-precept-458206-j1", location="us-central1")
    print("Client initialized")
except Exception as e:
    print(f"Client init failed: {e}")
