#!/usr/bin/env python3
"""
Test script to generate a video and capture the error
"""
import sys
import os
sys.path.insert(0, r'C:\Users\kumar\Desktop\WorkSpace\yt-video-creator')
os.chdir(r'C:\Users\kumar\Desktop\WorkSpace\yt-video-creator')

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.core.models import Job, JobStatus
from app.story.adapter import StoryAdapter
from app.orchestrator.service import OrchestratorService
from datetime import datetime
import traceback

print("\n" + "="*60)
print("VIDEO GENERATION TEST")
print("="*60 + "\n")

try:
    print("[STEP 1] Create test job...")
    orchestrator = OrchestratorService()
    
    job_data = {
        "platform": "youtube_shorts",
        "audience": "general_adult",
        "duration": 30,
        "genre": "entertainment",
        "language": "en"
    }
    
    job = orchestrator.create_job(job_data)
    print(f"[OK] Job created: {job.id}")
    print(f"     Status: {job.status}")
    
    print("\n[STEP 2] Start job processing...")
    try:
        result = orchestrator.start_job(job.id)
        if result:
            print("[OK] Job completed successfully!")
        else:
            print("[FAIL] Job failed (returned False)")
    except Exception as e:
        print(f"[FAIL] Job processing failed!")
        print(f"\n     Exception Type: {type(e).__name__}")
        print(f"     Exception Message: {str(e)}")
        print(f"\n     Full Traceback:")
        traceback.print_exc()
        
except Exception as e:
    print(f"[FATAL] Error: {e}")
    traceback.print_exc()

finally:
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")
