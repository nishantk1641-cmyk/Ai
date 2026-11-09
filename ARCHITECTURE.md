# NEXRUN AI Cloud Architecture

```text
Android phone
  └── Installable PWA (frontend/)
       ├── Task composer
       ├── Speech input/output
       └── Task status polling
             │ HTTPS
             ▼
      FastAPI API (backend/)
       ├── POST /tasks
       ├── GET /tasks
       ├── GET /tasks/{id}
       └── Health endpoint
             │
             ▼
      Persistent task store
       └── SQLite starter → PostgreSQL production
             │
             ▼
      Background worker
       ├── Research agent (search integration still required)
       ├── Writer agent
       ├── Coding agent
       └── Planner agent
             │
             ▼
      Gemini API (server-side secret)
```

## Production upgrade path
- Identity: Firebase Authentication or an equivalent identity provider.
- Database: PostgreSQL with per-user row ownership.
- Queue: Redis + Celery/RQ or a managed queue with retries and dead-letter handling.
- Worker: separate always-on worker service.
- Research: approved search API with URL allow-listing, source capture and citations.
- Voice: real-time voice provider using short-lived server-issued session credentials.
- Notifications: Firebase Cloud Messaging (FCM).
- Observability: structured logs, task tracing, metrics and alerts.

## Permission model
- Read-only research and drafting can run after the user submits a task.
- Sending messages, publishing, purchases, deleting files, changing account settings or controlling devices require a separate confirmation step.
- Never store passwords or provider secrets in task prompts.
