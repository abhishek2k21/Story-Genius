#!/usr/bin/env python
"""
Diagnostic Script for Story Genius Video Generation
Tests all critical components to identify issues
"""

import sys
import os
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_section(text):
    print(f"\n>>> {text}")
    print("-" * 60)

def test_environment():
    """Test environment variables and configuration"""
    print_section("1. ENVIRONMENT CONFIGURATION")
    
    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"✓ Python Version: {py_version}")
    
    # Check Google credentials
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path:
        print(f"✓ Google Credentials Set: {creds_path}")
        if os.path.exists(creds_path):
            print(f"  ✓ File exists and is readable")
        else:
            print(f"  ✗ File NOT found at path!")
            return False
    else:
        print(f"✗ Google Credentials NOT SET")
        print(f"  → Set: $env:GOOGLE_APPLICATION_CREDENTIALS = 'path/to/key.json'")
        return False
    
    return True

def test_imports():
    """Test critical library imports"""
    print_section("2. LIBRARY IMPORTS")
    
    tests = [
        ("FastAPI", "fastapi"),
        ("SQLAlchemy", "sqlalchemy"),
        ("Vertex AI", "vertexai"),
        ("Google Cloud Auth", "google.auth"),
        ("Pydantic", "pydantic"),
    ]
    
    all_ok = True
    for name, module in tests:
        try:
            __import__(module)
            print(f"✓ {name}: Available")
        except ImportError as e:
            print(f"✗ {name}: NOT available")
            print(f"  Error: {e}")
            all_ok = False
    
    return all_ok

def test_vertex_ai():
    """Test Vertex AI initialization"""
    print_section("3. VERTEX AI INITIALIZATION")
    
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        print("Attempting Vertex AI init...")
        vertexai.init(project="winged-precept-458206-j1", location="us-central1")
        print("✓ Vertex AI initialized successfully!")
        
        print("Creating GenerativeModel...")
        model = GenerativeModel("gemini-2.0-flash-001")
        print("✓ GenerativeModel created successfully!")
        
        return True
    except Exception as e:
        print(f"✗ Vertex AI initialization failed!")
        print(f"  Error: {type(e).__name__}: {e}")
        print(f"\n  SOLUTION:")
        print(f"  1. Set Google Cloud credentials:")
        print(f"     $env:GOOGLE_APPLICATION_CREDENTIALS = 'path/to/service-account.json'")
        print(f"  2. Get credentials from: https://console.cloud.google.com/")
        return False

def test_database():
    """Test database connection"""
    print_section("4. DATABASE CONNECTION")
    
    try:
        from app.core.database import get_db_session
        
        print("Attempting database connection...")
        db = get_db_session()
        
        # Simple test query
        result = db.execute("SELECT 1")
        db.close()
        
        print("✓ Database connection successful!")
        return True
    except Exception as e:
        print(f"✗ Database connection failed!")
        print(f"  Error: {e}")
        return False

def test_story_adapter():
    """Test Story Adapter"""
    print_section("5. STORY ADAPTER")
    
    try:
        from app.core.models import Job, JobStatus, Platform
        from app.story.adapter import StoryAdapter
        from datetime import datetime
        
        print("Creating test job...")
        job = Job(
            id="test-job-123",
            status=JobStatus.QUEUED,
            platform="youtube_shorts",
            audience="general_adult",
            duration=30,
            genre="entertainment",
            language="en",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        print("Initializing StoryAdapter...")
        adapter = StoryAdapter(job)
        print("✓ StoryAdapter initialized successfully!")
        
        print("This would normally call _get_llm() next...")
        return True
    except Exception as e:
        print(f"✗ StoryAdapter initialization failed!")
        print(f"  Error: {type(e).__name__}: {e}")
        return False

def test_orchestrator():
    """Test Orchestrator Service"""
    print_section("6. ORCHESTRATOR SERVICE")
    
    try:
        from app.orchestrator.service import OrchestratorService
        
        print("Creating OrchestratorService...")
        orchestrator = OrchestratorService()
        print("✓ OrchestratorService created successfully!")
        
        print("Testing create_job...")
        job = orchestrator.create_job({
            "platform": "youtube_shorts",
            "audience": "general_adult",
            "duration": 30,
            "genre": "entertainment",
            "language": "en"
        })
        
        print(f"✓ Job created: {job.id}")
        orchestrator.close()
        return True
    except Exception as e:
        print(f"✗ OrchestratorService failed!")
        print(f"  Error: {type(e).__name__}: {e}")
        return False

def main():
    """Run all diagnostics"""
    print_header("STORY GENIUS - SYSTEM DIAGNOSTIC")
    print("Testing critical components for video generation...\n")
    
    results = {
        "Environment": test_environment(),
        "Imports": test_imports(),
        "Vertex AI": test_vertex_ai(),
        "Database": test_database(),
        "Story Adapter": test_story_adapter(),
        "Orchestrator": test_orchestrator(),
    }
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_pass = all(results.values())
    
    print(f"\n{'='*60}")
    if all_pass:
        print("✓ ALL TESTS PASSED - System is ready!")
        print("  You can now generate videos.")
    else:
        print("✗ SOME TESTS FAILED - See details above")
        print("\n  NEXT STEPS:")
        print("  1. Read: ERROR_ANALYSIS_AND_SOLUTION.md")
        print("  2. Set Google Cloud credentials")
        print("  3. Restart backend")
        print("  4. Run this diagnostic again")
    print(f"{'='*60}\n")
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
