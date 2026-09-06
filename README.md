# Flux — AI Video & Podcast Automation

Flux turns a topic into a finished, vertical (9:16) short-form **video** or **podcast**, then auto-publishes it to YouTube. It can also run unattended: monitoring **Economic Times** RSS feeds, ranking trending stories, and generating videos for the top picks on a schedule.

Topic in → script, visuals, narration, subtitles, assembled MP4, thumbnail, and a YouTube upload out.

---

## Features

- **Two output modes**
  - **Video** — a distinct image per scene (Pexels stock → Gemini image fallback)
  - **Podcast** — a single themed cover image held over the full narration
- **AI script generation** — Gemini writes a scene-by-scene script (narration + visual prompts)
- **Stock + generated visuals** — Pexels is the primary image source; Gemini image generation is the fallback
- **Text-to-speech** — narration via Kokoro TTS
- **Subtitles** — auto-timed captions burned into the video (+ a sidecar `.srt`)
- **Vertical assembly** — composed to **1080×1920 (9:16)** for YouTube Shorts, with intro/outro
- **Thumbnails** — a poster frame is generated per render and shown in the library
- **YouTube auto-publishing** — optional per render, with **Unlisted / Public / Private** visibility and `#Shorts` tagging
- **Trending pipeline** — scheduled monitoring of Economic Times RSS, heuristic ranking, and auto-generation of the top N stories
- **Web UI** — a studio to create renders, watch the live pipeline, and browse the output library

---

## Architecture

```
                          ┌──────────────────────────────┐
   Browser  ──────────▶   │  Frontend (React + Vite)      │
                          │  studio · pipeline · library  │
                          └───────────────┬───────────────┘
                                           │  /api/v1  (Vite proxy in dev)
                                           ▼
                          ┌──────────────────────────────┐
                          │  Backend (FastAPI)            │
                          │                               │
   ET RSS feeds ─▶ Trends │  VideoGenerationService       │ ─▶ YouTube
   (APScheduler)  service │   1. script   (Gemini)        │   (Data API)
                          │   2. images   (Pexels→Gemini) │
                          │      └─ podcast: single cover │
                          │   3. audio    (Kokoro TTS)    │
                          │   4. subtitles                │
                          │   5. assemble (MoviePy 9:16)  │
                          │   6. thumbnail (ffmpeg)       │
                          │   7. publish  (optional)      │
                          └──────────────────────────────┘
```

### Backend pipeline ([backend/app/services/video_service.py](backend/app/services/video_service.py))
A render runs as a background task through these stages:
1. **Script** — `imagegen/generate_script.py` (Gemini, JSON output: `audio_script` + `visual_script`)
2. **Visuals** — `imagegen/gen_img.py` (Pexels → Gemini fallback). Podcast mode sources one cover and holds it across segments.
3. **Audio** — `tts/generate_audio_refactored.py` (Kokoro)
4. **Subtitles** — `assembly/scripts/assembly_video_refactored.py` (`create_complete_srt`)
5. **Assembly** — MoviePy composes images + audio + captions into a 1080×1920 MP4 (`create_video`)
6. **Thumbnail** — a poster frame is extracted via ffmpeg
7. **Publish** — optional YouTube upload (`app/services/youtube_service.py`)

> The heavy ML deps (torch, MoviePy, Kokoro) are **lazy-imported** inside the render task, so the API/health/trends endpoints stay lightweight at boot.

### Trending pipeline ([backend/app/services/trends_service.py](backend/app/services/trends_service.py), [trends_scheduler.py](backend/app/services/trends_scheduler.py))
- Fetches the configured Economic Times RSS feeds (`feedparser`)
- Ranks articles by `0.45·recency + 0.55·cross-feed keyword overlap` (free, deterministic; trending = the same story surfacing across feeds)
- Skips stale and already-processed articles (dedup state in `resources/trends_state.json`)
- An **APScheduler** background job auto-generates the top N on an interval (disabled by default)

### Frontend ([frontend/](frontend/))
React 19 + Vite + Tailwind. In dev, the Vite server proxies `/api` and `/static` to the backend; in production it talks to `VITE_API_BASE_URL`.

---

## Tech stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Uvicorn, Pydantic |
| AI / media | Google Gemini (`google-genai`), Pexels API, Kokoro TTS (torch), MoviePy + ffmpeg, Pillow, OpenCV |
| Scheduling | APScheduler, feedparser |
| Publishing | YouTube Data API (`google-api-python-client`, `google-auth`) |
| Frontend | React 19, Vite, Tailwind CSS |

---

## Project structure

```
Flux2-main/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan (starts trends scheduler)
│   │   ├── api/v1/              # videos, upload, trends routers
│   │   ├── core/config.py       # settings (env-driven)
│   │   ├── schemas/             # request/response models
│   │   └── services/            # video, youtube, trends, trends_scheduler, document
│   ├── imagegen/                # generate_script.py, gen_img.py
│   ├── tts/                     # generate_audio_refactored.py (Kokoro)
│   ├── assembly/                # assembly_video_refactored.py (MoviePy)
│   ├── resources/              # generated scripts/images/audio/video/subtitles
│   ├── static/videos/          # finished MP4s + thumbnails (served at /static)
│   ├── secrets/                # YouTube OAuth client_secret + token (gitignored)
│   ├── authorize_youtube.py    # one-time OAuth flow to mint secrets/youtube_token.json
│   └── requirements.txt
├── frontend/                    # React + Vite app
├── render.yaml                  # Render blueprint (backend)
├── DEPLOYMENT.md                # full deploy guide (Render + Vercel)
└── README.md
```

---

## Setup

**Prerequisites:** Python **3.12** (the ML deps don't have wheels for 3.13+/3.14), Node 18+, and a [Gemini API key](https://aistudio.google.com/app/apikey). A [Pexels key](https://www.pexels.com/api/) is recommended.

### Backend
```bash
cd backend
py -3.12 -m venv venv          # Windows;  python3.12 -m venv venv on macOS/Linux
.\venv\Scripts\Activate.ps1    # source venv/bin/activate on macOS/Linux
pip install -r requirements.txt

cp .env.example .env           # then fill in GEMINI_API_KEY (and PEXELS_API_KEY)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Health: http://127.0.0.1:8000/health
- API docs: http://127.0.0.1:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```
The dev server proxies API/media calls to the backend automatically.

### YouTube publishing (optional)
1. Put your OAuth **desktop** client at `backend/secrets/youtube_client_secret.json`.
2. Run the one-time flow:
   ```bash
   cd backend && python authorize_youtube.py
   ```
   This opens a browser and writes `secrets/youtube_token.json`.
3. Set the publish options (below). For unattended/headless deploys, paste the token JSON into `YOUTUBE_TOKEN_JSON`.

> Tip: set your Google OAuth consent screen to **"In production"** so refresh tokens don't expire after 7 days.

---

## Configuration (key environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | **Required.** Script + image fallback |
| `PEXELS_API_KEY` | — | Primary image source (falls back to Gemini) |
| `CORS_ORIGINS` | localhost dev origins | Allowed frontend origins |
| `IMAGE_ASPECT_RATIO` | `1:1` | Use `9:16` for vertical Shorts |
| `DEFAULT_VIDEO_FPS` | `24` | Output frame rate |
| **YouTube** | | |
| `YOUTUBE_TOKEN_JSON` | — | Token JSON for headless deploys (overrides the file) |
| `YOUTUBE_AUTO_UPLOAD` | `false` | Publish **every** render (else the UI toggle decides) |
| `YOUTUBE_PRIVACY_STATUS` | `private` | `private` / `unlisted` / `public` |
| `YOUTUBE_CATEGORY_ID` | `27` | 27 = Education |
| **Trending** | | |
| `TRENDS_ENABLED` | `false` | Run the ET scheduler |
| `TRENDS_AUTO_PUBLISH` | `false` | Auto-publish trending videos |
| `TRENDS_INTERVAL_HOURS` | `6` | Run cadence |
| `TRENDS_TOP_N` | `3` | Stories per run |
| `TRENDS_FEED_URLS` | ET feeds | Comma-separated RSS URLs |
| **Frontend (Vercel)** | | |
| `VITE_API_BASE_URL` | — | Backend URL in production (build-time) |
| `VITE_FLUX_CHANNEL_URL` | fallback | Header channel link |

See [backend/.env.example](backend/.env.example) for the full list.

---

## API

Base path: `/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/videos/generate` | Start a render (`topic`, `duration`, `key_points`, `style`, `publish_to_youtube`, `privacy_status`) |
| `GET` | `/videos/list` | List finished videos (+ thumbnails) |
| `GET` | `/videos/download/{name}` | Download an MP4 |
| `GET` | `/videos/stream/{name}` | Stream an MP4 |
| `POST` | `/upload/file` | Upload a source document |
| `GET` | `/trends/status` | Scheduler status + last run |
| `GET` | `/trends/preview` | Ranked trending articles (no generation) |
| `POST` | `/trends/run` | Trigger one trending run now |
| `GET` | `/health` | Health check |

---

## Deployment

Backend → **Render** (via [render.yaml](render.yaml)), frontend → **Vercel** (via [frontend/vercel.json](frontend/vercel.json)). Full step-by-step guide in **[DEPLOYMENT.md](DEPLOYMENT.md)**.

> ⚠️ Rendering is RAM-heavy (torch + MoviePy + TTS). Render's free tier (512 MB) will OOM **during a render** — the API/trending parts work, but reliable rendering needs the **Standard** plan (2 GB+).

---

## Notes & limitations

- **Python 3.12 only** — torch/Kokoro/spaCy lack wheels for newer versions.
- **One render at a time** — generation is synchronous per request (in a background task).
- **Secrets** — `backend/secrets/` and `.env` are gitignored; never commit OAuth files.
- On first render the Kokoro and spaCy models download once (cached afterward).
