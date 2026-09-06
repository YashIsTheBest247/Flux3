# Flux — Deployment

**Live: https://flux3-production.up.railway.app**

Goal: one public URL that serves both the UI and the API, with every generated
asset stored durably on **Backblaze B2**.

The Docker image at the repository root builds the React SPA and serves it from
FastAPI, so there is nothing to deploy separately and no CORS to configure.
Because B2 owns the media, the host's filesystem can be completely ephemeral.

---

## 1. Prerequisites

### 1a. Backblaze B2 (required)

The library lives here. Free tier includes 10 GB.

1. Sign up: <https://www.backblaze.com/sign-up/cloud-storage>
2. **B2 Cloud Storage → Buckets → Create a Bucket**
   - Name it (e.g. `flux-media`)
   - **Files in Bucket are: Private** — Flux hands out short-lived presigned
     URLs, so the bucket never needs to be public
3. **Application Keys → Add a New Application Key**
   - Restrict it to the bucket you just made
   - Access: **Read and Write**
   - Copy `keyID` and `applicationKey` — the secret is shown **once**
4. Note the bucket's **Endpoint** (e.g. `s3.us-west-004.backblazeb2.com`);
   the region is the middle segment: `us-west-004`

| Variable | Value |
|---|---|
| `B2_KEY_ID` | the `keyID` |
| `B2_APP_KEY` | the `applicationKey` |
| `B2_BUCKET` | your bucket name |
| `B2_REGION` | e.g. `us-west-004` |

### 1b. Script model (required, but enter it in the app)

`GEMINI_API_KEY` from <https://aistudio.google.com/app/apikey> (free tier).
Alternatively set `SCRIPT_PROVIDER=ollama` for a fully local model.

You can set this as an environment variable, but you do not have to: the
**Connect** screen takes it after the app is running and stores it encrypted
(§4b). B2 above is the only credential that must be an env var, because it is
where everything else is kept.

### 1c. Optional

| Variable | Effect |
|---|---|
| `GMI_API_KEY` | Turns on Genblaze cloud image **and** narration models. Worth adding: cloud narration removes torch/Kokoro from the critical path, cutting render time and memory. |
| `PEXELS_API_KEY` | Stock photography for scene visuals (free, fast) |
| `YOUTUBE_TOKEN_JSON` | Contents of `secrets/youtube_token.json`, enables publishing |

---

## 2. Recommended: Render (this is what the live deploy runs on)

### Host options

The default image carries **no torch** — narration runs through Edge TTS — so
peak memory is ~300 MB rather than ~1.5 GB. That reopens the small tiers:

| Host | Free tier | Verdict |
|---|---|---|
| **Render** | 512 MB, sleeps after 15 min idle | ✓ what the live deploy runs on |
| Koyeb | 512 MB, no card | ✓ same image, same constraints |
| Fly.io | Pay-as-you-go with a small allowance | ✓ works, needs a card |
| Google Cloud Run | Generous, but CPU is throttled outside a request | ✗ renders are background tasks and get killed |
| Hugging Face Spaces | **Static only** — Docker Spaces now require PRO | ✗ cannot run the backend |

> If you set `TTS_PROVIDER=kokoro` and install `requirements-kokoro.txt`, peak
> memory returns to ~1.5 GB and the 512 MB tiers will OOM mid-render. That is
> exactly what happened on the first deploy of this app — the container was
> killed while loading the TTS model, twice, reproducibly.

### Steps

1. Push this repository to GitHub.
2. 🔗 <https://render.com> → sign up with GitHub → **New → Blueprint** → pick
   this repository. Render reads [render.yaml](render.yaml) and creates one
   Docker web service; [`.dockerignore`](.dockerignore) keeps old renders out of
   the build context (198 MB → 17 MB).

   > **If Render asks for a card:** the Blueprint flow can require payment
   > details on file even when every service in the file is on the free plan.
   > There is no way to satisfy it from the YAML. Create the service by hand
   > instead — **New → Web Service** → the same repo → Runtime **Docker**,
   > Instance Type **Free** — then paste the environment variables from §2.3
   > into the Environment tab. You lose only the convenience of the blueprint
   > filling them in; the resulting service is identical, since every setting
   > that matters is an env var.
3. Render prompts for every `sync: false` variable in the blueprint. Fill in:
   ```
   GEMINI_API_KEY=...
   B2_KEY_ID=...
   B2_APP_KEY=...
   B2_BUCKET=...
   B2_REGION=us-east-005
   PEXELS_API_KEY=...
   ```
   **The app builds and serves fine without them — it just can't render.**
   `/health` reports exactly which are missing, so check it after the first
   deploy rather than assuming.
4. Render assigns the public URL itself (`https://<service>.onrender.com`) and
   exposes it immediately — there is no separate "generate domain" step. That
   URL is the one for judges.
5. Set the `RENDER_URL` repository secret so the keep-alive cron can reach the
   service (§3), then verify `/health` (§7) and run 2–3 renders to populate the
   library.

First build takes ~3–5 minutes now that torch is out of the image (it was 8–15).
Later deploys reuse the dependency layer unless `requirements.txt` changes.

### Which plan

**The blueprint ships `plan: free`,** and the memory budget it sets is what
makes that work:

```yaml
FLUX_VIDEO_WIDTH: 480      # kept — 720/1080 will not fit
FLUX_VIDEO_HEIGHT: 854
DEFAULT_VIDEO_FPS: 15      # from 20; near-invisible here, 25% fewer frames
FLUX_FFMPEG_PRESET: ultrafast
FLUX_FFMPEG_THREADS: 2
TRENDS_TOP_N: 1            # two overlapping renders is the fastest OOM
INGEST_MAX_MB: 250         # upload + frame + audio share one small disk
```

The frame rate is the cheapest lever and the resolution is the most expensive
one to give up. These shorts are photographs held under narration with the
occasional slow pan, so the difference between 20 and 15 fps is very hard to
see — whereas dropping below 480x854 is the first thing a viewer notices on a
phone.

The reason free is viable at all is that narration moved to Edge TTS, so the
image carries no torch and a stills-only render peaks near **300 MB** of the
512 MB available. The app also reads its own cgroup limit and, below
`SCENE_VIDEO_MIN_MEMORY_MB` (768), runs **zero** stock video clips — each one
costs roughly 140 MB of decoder on top of the baseline.

That last point is a real trade, so it is worth stating plainly: **on the free
plan the opening scenes lose their motion** and use photographs instead. The
alternative is an OOM-killed render, which produces nothing at all.

| Plan | Sleeps? | Renders? |
|---|---|---|
| **Free (512 MB)** | after 15 min idle — §3 handles it | ✓ stills only, no scene clips |
| Starter ($7/mo, 512 MB) | never | ✓ same ceiling, no cold starts |
| Standard (2 GB) | never | ✓ comfortable, clips enabled |

If a render is killed, check the logs for an OOM around the `voice` or
`assembly` stage before suspecting the pipeline — and run one real render early
rather than discovering it on demo day.

---

## 3. Keeping it awake

Render idles a web service out after ~15 minutes without inbound traffic, and
the cold start costs the better part of a minute — long enough that someone
opening the demo link sees a blank page first. Two pingers run on a 12-minute
interval, and **you need both**:

| | What it is | What it can do |
|---|---|---|
| **Internal** | [`app/services/keepalive.py`](backend/app/services/keepalive.py) — an APScheduler job hitting the service's own public URL | *Prevents* a spin-down while the process is alive |
| **External** | [`.github/workflows/keepalive.yml`](.github/workflows/keepalive.yml) — a GitHub Actions cron | *Reverses* one; this is the only half that can |

The distinction matters: once Render stops the container, nothing inside it
runs, so the self-ping cannot bring the service back after a deploy, a crash or
an OOM. Only a request from outside does that.

**Internal** — on by default, nothing to configure. Render injects
`RENDER_EXTERNAL_URL`, and the app derives the target from it.

| Variable | Default | Effect |
|---|---|---|
| `KEEPALIVE_ENABLED` | `true` | Turn the self-ping off |
| `KEEPALIVE_MINUTES` | `12` | Interval, comfortably inside the 15-minute window |
| `KEEPALIVE_URL` | *(unset)* | Override the target on a host that does not advertise its own URL |

**External** — set one repository secret:
**Settings → Secrets and variables → Actions → New repository secret**,
`RENDER_URL` = your `https://<service>.onrender.com` (no trailing slash). Then
**Actions → keepalive → Run workflow** once to confirm it returns 200.

Both target `/ping`, not `/health`: `/health` calls out to Backblaze and YouTube
on every request, and 120 of those a day is pure waste when all the ping has to
do is arrive.

> **Add a third, independent pinger.** GitHub's scheduler is best-effort and
> drifts under load — sometimes past the 15-minute window — and it disables
> scheduled workflows in a repository with no commits for 60 days. Registering
> the same URL on cron-job.org or UptimeRobot takes a minute and removes both
> failure modes.
>
> **Instance hours.** Render's free tier allows 750 instance-hours a month per
> account. Running one service 24/7 costs ~730, so one free service fits and two
> do not.

## 4. First run: making it yours

Only **Backblaze B2** has to be an environment variable. It is the bootstrap:
the media library, the credential vault, the custom profiles and the active
profile all live in the bucket, so nothing else can be stored until it exists.

Everything else is entered in the app.

### 4a. Pick a channel type

Open the site, scroll to **Channel**, choose one of the six presets — Tech News,
Markets & Money, Gaming, Fitness & Health, Entertainment, Science & Curiosity.
That single choice sets the trend sources, the ranking weights, the narrator's
voice, the visual vocabulary, the YouTube category and the publish schedule.

**Check sources** on the same screen reports what each source returned just now.
Use it before blaming the pipeline: "found nothing" and "Reddit is unreachable
from this host" look identical from the outside, and only one of them is your
problem.

### 4b. Add your keys

Under **Connect**, paste a [Gemini key](https://aistudio.google.com/app/apikey)
(required — it writes the script, title, description and tags) and optionally
[Pexels](https://www.pexels.com/api/) and
[Unsplash](https://unsplash.com/oauth/applications) keys for visuals.

They are Fernet-encrypted and written to `{B2_PREFIX}/config/credentials.enc`.
They are never returned by the API — the settings screen shows only the last
four characters, which is enough to tell two keys apart.

> The encryption key comes from `FLUX_SECRET_KEY`. The blueprint sets it with
> `generateValue: true`, so each deployment gets its own. If it is unset the key
> is derived from `B2_APP_KEY` instead, so a fresh deploy works with nothing
> extra to configure — the tradeoff being that whoever holds the B2 key can
> decrypt the vault. **Changing this value makes previously saved credentials
> unreadable.** The app says so plainly and you re-enter them.

### 4c. Connect a YouTube channel

You bring your own Google Cloud project, so uploads go to your channel and the
daily quota is yours.

1. Google Cloud → **APIs & Services** → enable **YouTube Data API v3**
2. **Credentials → Create credentials → OAuth client ID → Web application**
3. Add the redirect URI **exactly** as the Connect screen prints it:
   ```
   https://<your-service>.onrender.com/api/v1/auth/youtube/callback
   ```
   Google compares this character for character. A trailing slash, `http`
   instead of `https`, or the wrong host is a `redirect_uri_mismatch` — which is
   the single most common way this fails. The Connect screen shows the exact
   string to copy, so copy it from there rather than typing it.
4. Paste the client ID and secret into **Connect**, save, then **Connect a
   channel**. Google's consent screen opens in a popup and hands you back.

Scopes requested are `youtube.upload` and `youtube.force-ssl` — the first
publishes, the second is what allows setting a thumbnail and attaching a caption
track. Disconnecting revokes the token at Google, not just locally.

> While your OAuth consent screen is in **Testing**, add your own Google account
> under **Test users** or Google refuses the sign-in. Refresh tokens issued in
> testing mode also expire after seven days — fine for a demo, worth publishing
> the app for anything longer.

### 4d. Bring your own video

**Upload** takes an existing file (mp4, mov, mkv, webm, avi) up to
`INGEST_MAX_MB` — 400 MB by default, capped because Render's disk is small and
ephemeral and the upload, its extracted frame and its audio all live there at
once.

Nothing re-encodes the video. One frame is extracted for the thumbnail, the
audio is pulled at 48 kbps mono and transcribed, and the **original bytes** are
what get uploaded; the thumbnail and `.srt` are attached afterwards. That is
what keeps a 300 MB upload inside a 512 MB instance.

> **Custom thumbnails need a verified YouTube account.** An unverified channel
> gets a 403 on `thumbnails.set`. Flux treats that as a warning rather than a
> failure — the video publishes and uses an auto-generated frame — and tells you
> to verify at [youtube.com/verify](https://www.youtube.com/verify).

---

## 5. Fly.io / Cloud Run

Both build the root `Dockerfile` unchanged.

- **Fly.io**: `fly launch --dockerfile Dockerfile`, then
  `fly secrets set GEMINI_API_KEY=... B2_KEY_ID=... B2_APP_KEY=... B2_BUCKET=... B2_REGION=...`
  and size the VM with `fly scale memory 2048`.
- **Cloud Run**: `gcloud run deploy flux --source . --memory 2Gi --timeout 900
  --min-instances 1 --no-cpu-throttling`. Both flags matter: renders run as
  background tasks that outlive the HTTP response, so scale-to-zero or throttled
  CPU would kill one mid-flight.

## 6. Split deploy (frontend on Vercel)

Still supported if you prefer it:

1. Deploy the backend by any method above.
2. Vercel → import the repo, **Root Directory: `frontend`**
3. Set `VITE_API_BASE_URL` to the backend URL (build-time)
4. Set `CORS_ORIGINS` on the backend to your Vercel URL (no trailing slash)

---

## 7. Verify the deployment

```bash
curl https://flux3-production.up.railway.app/health
```

```jsonc
{
  "status": "healthy",
  "ready": true,             // a script model is configured
  "durable_storage": true,   // B2 reachable — this is the one to check
  "checks": {
    "script_llm": true,
    "backblaze_b2": true,
    "genblaze": true,
    "genblaze_sink": true,   // Genblaze is writing manifests to B2
    "stock_images": true,
    "gmi_cloud": false
  },
  "keepalive": {
    "enabled": true,
    "running": true,          // false locally — there is no public URL to ping
    "target": "https://flux3-production.up.railway.app/ping",
    "interval_minutes": 12,
    "next_ping_at": "..."
  }
}
```

`durable_storage: false` means the B2 credentials are missing or wrong — the app
will still render, but into ephemeral local disk. `backblaze_b2.error` in the
same response says why.

Then, in the UI:

1. Open the site → the **Library** header shows `Backblaze B2 · <bucket>` and
   `Genblaze provenance`
2. **Automation → Run Automation** with top-N = 1
3. Watch the pipeline advance through **Provenance** and **Backblaze B2**
4. When the card appears it carries a **B2** badge and a verified shield
5. Card menu → **Provenance** shows the manifest: generation chain, per-artefact
   SHA-256, and the verification result

---

## 8. Notes and gotchas

- **One render at a time.** The render lock and live status are in-process, so
  run a single worker (the Dockerfile pins `--workers 1`). Horizontal scaling
  would need Redis or a task queue.
- **A restart mid-render looks like "no video was produced".** Live status is
  in-memory, so a killed container comes back with `updated_at: null` and the UI
  reports the render stopped. If you see that, check the platform logs for an
  OOM around the `voice` or `assembly` stage rather than suspecting the pipeline.
- **Memory.** ~300 MB peak on the default image. `FLUX_FFMPEG_THREADS=2` and a
  lower `FLUX_VIDEO_WIDTH`/`HEIGHT` trim the assembly peak further.
- **Presigned URLs expire** after `B2_URL_TTL_SECONDS` (default 1 h). The
  library re-signs on every refresh, so this only matters for links you copy
  out of the app.
- **A self-ping cannot wake a sleeping instance.** Worth repeating because it
  is the one way this setup silently fails: if the external cron stops firing —
  GitHub disabled the schedule, the `RENDER_URL` secret is wrong — the internal
  ping keeps working right up until the first spin-down, and then nothing brings
  the service back until a human opens the URL.
- **The scheduler is on in the blueprint.** `TRENDS_ENABLED=true` means the
  service renders unattended at 08:00/14:00/20:00 IST and spends Gemini quota
  doing it. `TRENDS_AUTO_PUBLISH` stays `false`, so nothing reaches YouTube
  until you opt in.
- **Never commit** `backend/.env` or `backend/secrets/` — both are gitignored.
