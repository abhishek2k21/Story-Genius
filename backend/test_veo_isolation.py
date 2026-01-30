"""
Veo Isolation Test
Tests Veo video generation independently to diagnose auth/quota issues.
"""
import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv()

from src.clients.vertex_client import get_vertex_client

async def test_veo_simple():
    print("Initializing Vertex Client...")
    client = get_vertex_client()
    
    prompt = "A calm ocean wave rolling gently, cinematic style, high resolution, 4k"
    output_path = "test_veo_output.mp4"
    
    print(f"\nTesting Veo generation with prompt: '{prompt}'")
    print("-" * 50)
    
    try:
        # Note: This will actually try to call the underlying Veo wrapper
        # If the wrapper is missing or fails, we'll see the specific error
        result = await client.generate_video(
            prompt=prompt,
            output_path=output_path,
            duration_seconds=5
        )
        print(f"\nSUCCESS: Video generated at {result}")
        
    except Exception as e:
        print(f"\nFAILURE: Veo generation failed")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        # Check for common keywords
        msg = str(e).lower()
        if "quota" in msg or "resource exhausted" in msg:
            print("\nDIAGNOSIS: Quota limit reached or billing issue.")
        elif "safety" in msg or "blocked" in msg:
            print("\nDIAGNOSIS: Prompt blocked by safety filters.")
        elif "permission" in msg or "access" in msg:
            print("\nDIAGNOSIS: IAM permission denied (Vertex AI User role needed).")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_veo_simple())
