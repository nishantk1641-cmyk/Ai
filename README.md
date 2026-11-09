# NEXRUN AI — Acode + Cloud Starter

This is a working starter architecture, not a finished unrestricted autonomous agent.

## What is included
- Mobile-first PWA frontend suitable for editing in Acode.
- Task submission and task history.
- Four agent modes: research, writer, coder and planner.
- FastAPI backend using Gemini through a server-side API key.
- SQLite task persistence and a background worker thread.
- Speech-to-text and text-to-speech when supported by the mobile browser.
- PWA shell cache so the interface can open offline.

## Important limitations
1. The phone being powered off does not stop work running on an always-on cloud server. The cloud backend must remain deployed and running.
2. The included worker is a single-process starter. For production, replace it with a durable queue such as Redis + Celery/RQ or a managed task queue, and use PostgreSQL.
3. The research agent in this starter does not have live web search wired in. It must not be treated as a verified live research service until a search provider is integrated.
4. Voice input/output uses browser speech features. It is not a continuous phone call. True low-latency two-way voice needs a real-time voice provider and server-side session/token handling.
5. There is no hidden phone control, unrestricted shell execution, or automatic sending/purchasing/publishing. Add integrations one at a time with explicit user approval.
6. Use HTTPS in deployment. Never put Gemini keys in `frontend/app.js`, HTML, or a public GitHub repository.

## Run locally (computer or cloud shell)
1. Install Python 3.12.
2. Open a terminal in `backend/`.
3. Install dependencies: `pip install -r requirements.txt`
4. Set `GEMINI_API_KEY` as an environment variable. Do not commit it.
5. Start: `uvicorn main:app --host 0.0.0.0 --port 8000`
6. Open `frontend/index.html` through a local web server or host the `frontend/` folder.
7. In the app's Server Connection panel, set the API URL, e.g. `http://192.168.1.20:8000` on the same Wi-Fi, or your HTTPS deployed backend URL.

## Acode on Android
- Extract this ZIP.
- Open the `frontend` folder in Acode.
- Edit `index.html` and `app.js`.
- Acode is an editor, not a cloud server. Deploy the backend separately.
- To install as a PWA, host the frontend on HTTPS and open it in Chrome; use Chrome's Install app / Add to Home screen option.

## Cloud deployment
- Deploy `backend/` as a Docker web service on an always-on host.
- Set secret `GEMINI_API_KEY`.
- Set `GEMINI_MODEL` to a model available to your API account.
- Add persistent disk storage for `nexrun.db` for this starter.
- Deploy `frontend/` as a static HTTPS site.
- Set the backend URL in the app.
- Restrict `CORS_ORIGINS` to your frontend origin before public launch.
- For reliable production tasks, use PostgreSQL + a durable queue and separate worker service.

## Architecture
Android PWA (Acode-edited) -> HTTPS FastAPI API -> task database/queue -> agent worker -> Gemini API.
The browser can close or the phone can power off after task submission; cloud processing continues while the deployed worker and database are available.

## Security checklist before public use
- Add user authentication and per-user task ownership.
- Add rate limits and usage limits.
- Add request size limits and logging without storing secrets.
- Add explicit approval screens before any external side effect.
- Add backup, monitoring, error handling and abuse protection.
- Never expose API keys in frontend source.
