import time
import requests
import json
import os

BASE_URL = "http://localhost:8000"

def run_verification():
    print(f"Checking API Health at {BASE_URL}/v1/health...")
    try:
        health = requests.get(f"{BASE_URL}/v1/health")
        if health.status_code != 200:
            print(f"❌ API Health Check Failed: {health.status_code}")
            return
        print("✅ API is Healthy")
    except Exception as e:
        print(f"❌ Could not connect to API: {e}")
        return

    # 1. Start Job
    print("\n🚀 Starting Video Generation Job...")
    payload = {
        "platform": "youtube_shorts",
        "audience": "general",
        "topic": "The history of coffee in 30 seconds",
        "duration": 30,
        "genre": "educational",
        "language": "english"
    }
    
    try:
        # Check if auth needed (likely yes)
        # Try without first
        start_res = requests.post(f"{BASE_URL}/v1/shorts/generate", json=payload)
        
        headers = {}
        if start_res.status_code == 401 or start_res.status_code == 403:
            print("🔒 Auth Required. Logging in...")
            # Try logging in with default test user
            login_res = requests.post(f"{BASE_URL}/v1/auth/login", json={"email": "testuser", "password": "password"})
            
            token = None
            if login_res.status_code == 200:
                print("   Logged in as 'testuser'.")
                token = login_res.json()["access_token"]
            else:
                 # Try registering if login fails
                print("⚠️ Login failed. Trying to register temp user...")
                reg_payload = {"email": f"testGen_{int(time.time())}@example.com", "password": "Password123!", "username": f"tester_{int(time.time())}", "full_name": "Test Gen"}
                reg_res = requests.post(f"{BASE_URL}/v1/auth/signup", json=reg_payload)
                if reg_res.status_code == 200:
                    token = reg_res.json()["access_token"]
                    print("   Registered new test user.")
                else:
                    print(f"❌ Login/Register failed: {reg_res.text}")
                    return
            
            headers = {"Authorization": f"Bearer {token}"}
            print("🔑 Authenticated.")
            start_res = requests.post(f"{BASE_URL}/v1/shorts/generate", json=payload, headers=headers)

        if start_res.status_code != 200:
            print(f"❌ Failed to start job: {start_res.text}")
            return

        job_data = start_res.json()
        job_id = job_data["job_id"]
        print(f"✅ Job Started! ID: {job_id}")

    except Exception as e:
        print(f"❌ Execution Error: {e}")
        return

    # 2. Poll Status
    print("\n⏳ Polling for completion...")
    status = "queued"
    start_time = time.time()
    
    while status not in ["completed", "failed"]:
        if time.time() - start_time > 300: # 5 min timeout
            print("\n⏰ Timeout reached.")
            return

        try:
            status_res = requests.get(f"{BASE_URL}/v1/jobs/{job_id}")
            if status_res.status_code != 200:
                print(f"⚠️ Error checking status: {status_res.status_code}")
                time.sleep(2)
                continue
                
            status_data = status_res.json()
            status = status_data["status"]
            print(f"   Status: {status.upper()}...", end="\r")
            
            if status == "failed":
                print(f"\n❌ Job Failed: {status_data.get('error_message', 'Unknown error')}")
                return
            
            if status == "completed":
                print("\n🎉 GENERATION COMPLETE!")
                video_url = status_data.get('video_url', 'No URL found')
                print(f"📺 Video URL: {video_url}")
                return
                
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n🛑 Polling stopped by user.")
            return
        except Exception as e:
            print(f"\n❌ Loop Error: {e}")
            return

if __name__ == "__main__":
    run_verification()
