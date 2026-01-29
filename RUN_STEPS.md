# How to Run the Project

Follow these steps one by one.

## 1. Prerequisites
- Install Python (3.10 or newer)
- Install Node.js (18 or newer)
- Install VS Code (recommended)

## 2. Setup Backend (Terminal 1)
Open a terminal in the project root folder `yt-video-creator`.

1. **Active Virtual Environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Start Server** (Database creates automatically):
   ```powershell
   uvicorn app.api.main:app --reload
   ```
   *Wait until you see: "Application startup complete"*

## 3. Setup Frontend (Terminal 2)
Open a **new** terminal window.

1. **Go to frontend folder**:
   ```powershell
   cd frontend
   ```

2. **Install Dependencies** (Only first time):
   ```powershell
   npm install
   ```

3. **Start Website**:
   ```powershell
   npm run dev
   ```

## 4. Open Application
- **Website**: [http://localhost:5173](http://localhost:5173)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 5. Login Details
Use this default admin account:
- **Email**: `admin@storygenius.ai`
- **Password**: `Admin123!`

---

## optional: Run via ngrok (If sharing link)
If you want to share the link with others:
1. Open PowerShell as Administrator
2. Run:
   ```powershell
   .\start_live.ps1
   ```
