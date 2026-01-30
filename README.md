# Story-Genius: AI Creative Operating System 🎬

> **Automated Short-Form Video Generation for Retention & Virality**

Story-Genius is a **Creative AI Platform** that systematically generates, optimizes, and scales high-retention short-form videos (Shorts/Reels/TikTok) using audience intelligence, emotional modeling, hook engineering, and continuous feedback loops.

This platform does **not just generate videos** — it engineers **watch-time and virality**.

---

## 📘 Project Overview

### The Problem
Short-form platforms reward retention, replays, and emotional hooks. Creators struggle because creativity is inconsistent, production is slow, and feedback loops are manual.

### The Solution
An "AI Creative Director" that:
1.  Decides *what* to create based on strategy
2.  Engineers *how* it should perform (hooks, pacing, emotion)
3.  Learns *why* something worked via retention feedback
4.  Improves future outputs automatically

---

## ✨ Key Features

-   **Creative Orchestrator**: Acts as a director, making decisions on persona, emotion, and hooks.
-   **Audience Intelligence**: Adapts content for specific demographics and cultural contexts.
-   **Retention Engineering**: Optimizes every second for maximum viewer retention.
-   **Platform Native**: Specific strategies for YouTube Shorts, Instagram Reels, and TikTok.
-   **Feedback Loops**: "Critic" engine that scores content before publication.

---

## 🏗️ High-Level Architecture

The system is divided into **6 major layers**:

1.  **Client / API Layer**: Entry point (Web Dashboard, REST API).
2.  **Shorts Strategy Brain**: Decides how to win attention on a specific platform.
3.  **Creative Orchestrator**: The "Director" that coordinates all engines.
4.  **Creative Intelligence Layer**: Handles audience modeling, emotion curves, and personas.
5.  **Story & Asset Execution Layer**: Generates micro-scenes and narratives.
6.  **Media Generation Layer**: Converts instructions into assets (Video, Audio, Text).

---

## 🛠️ Technology Stack

-   **Backend**: Python 3.10+, FastAPI
-   **Database**: PostgreSQL / SQLAlchemy
-   **AI/ML**: Google Vertex AI, Custom LLM Pipelines
-   **Media Processing**: FFmpeg, MoviePy
-   **Frontend**: React, Next.js, Tailwind CSS
-   **Infrastructure**: Docker, Docker Compose

---

## 🚀 Getting Started

### Prerequisites

-   Python 3.10+
-   Node.js 18+
-   Docker & Docker Compose
-   FFmpeg (installed and added to PATH)
-   Google Cloud Credentials (for Vertex AI)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/story-genius.git
    cd story-genius
    ```

2.  **Set up the Backend**
    ```bash
    cd [backend_dir]
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

3.  **Set up the Frontend**
    ```bash
    cd [frontend_dir]
    npm install
    ```

4.  **Environment Variables**
    -   Copy `.env.example` to `.env` in both backend and frontend directories.
    -   Fill in your API keys (Google Cloud, Database URL, etc.).

### Running the Application

**Start the Backend:**
```bash
uvicorn app.api.main:app --reload
```

**Start the Frontend:**
```bash
npm run dev
```

Visit `http://localhost:3000` to access the commercial dashboard.

---

## 📂 Project Structure

```
yt-video-creator/
├── app/                  # Main application logic
├── backend/              # Backend services and API
├── frontend/             # Web interface
├── StoryGenius/          # Core story generation engine
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── tests/                # Test suite
└── .story_assets/        # Active media assets
```

---

## 📅 Roadmap (90-Day Plan)

We are currently executing a 90-day modernization plan to scale the platform.

-   **Phase 1 (Month 1)**: Foundation Hardening (Exceptions, Logging, Transactions)
-   **Phase 2 (Month 2)**: Quality & Observability (Prompts, Testing, Monitoring)
-   **Phase 3 (Month 3)**: Content Engine & Workflow Automation
-   **Launch**: Scheduled for April 28, 2026

See [90_DAY_PLAN.md](./90_DAY_PLAN.md) for full details.

---

## 📄 License

[MIT License](LICENSE)
