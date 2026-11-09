import os, json, sqlite3, threading, time, uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai

DB=os.getenv("NEXRUN_DB","nexrun.db")
MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
API_KEY=os.getenv("GEMINI_API_KEY","")
client=genai.Client(api_key=API_KEY) if API_KEY else None

app=FastAPI(title="NEXRUN AI API",version="0.1.0")
origins=os.getenv("CORS_ORIGINS","*").split(",")
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["*"])

def connect():
    c=sqlite3.connect(DB,timeout=30);c.row_factory=sqlite3.Row;return c

def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS tasks(
        id TEXT PRIMARY KEY,prompt TEXT NOT NULL,agent TEXT NOT NULL,status TEXT NOT NULL,
        result TEXT,error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)""")
init_db()

class TaskIn(BaseModel):
    prompt: str=Field(min_length=2,max_length=12000)
    agent: str="auto"

AGENTS={
 "research":"You are the research agent. Produce a careful report. Separate known facts, assumptions, and items that need verification. Do not invent sources or claim you browsed if no search tool was used.",
 "writer":"You are the writing agent. Create clear, useful drafts matching the user's requested format and tone.",
 "coder":"You are a coding assistant. Explain assumptions, provide safe code, and include testing steps. Never claim code was executed unless it was.",
 "planner":"You are a planning agent. Break the task into steps, dependencies, risks, and a practical next action.",
 "auto":"You are NEXRUN, a general-purpose AI agent. Choose an appropriate approach and deliver a complete useful result."
}

def update_task(task_id,status,result=None,error=None):
    now=datetime.now(timezone.utc).isoformat()
    with connect() as c:
        c.execute("UPDATE tasks SET status=?,result=?,error=?,updated_at=? WHERE id=?",
                  (status,result,error,now,task_id))

def run_task(task_id,prompt,agent):
    update_task(task_id,"running")
    try:
        if not client:
            raise RuntimeError("Server is missing GEMINI_API_KEY. Add it as a secret environment variable.")
        role=AGENTS.get(agent,AGENTS["auto"])
        instruction=(role+"\n\nOperating rules:\n"
          "- You may research, reason, write, plan and generate code.\n"
          "- You do not have permission to send messages, spend money, publish content, delete data, or control devices.\n"
          "- Ask for explicit confirmation before any consequential external action.\n"
          "- Be honest about tool access and uncertainty.\n\nUSER TASK:\n"+prompt)
        response=client.models.generate_content(model=MODEL,contents=instruction)
        update_task(task_id,"completed",result=response.text or "No text response returned.")
    except Exception as e:
        update_task(task_id,"failed",error=str(e))

@app.on_event("startup")
def startup():
    # Single-process starter worker. For production, run a separate durable queue worker.
    def loop():
        while True:
            row=None
            try:
                with connect() as c:
                    row=c.execute("SELECT * FROM tasks WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
                    if row:
                        c.execute("UPDATE tasks SET status='claimed' WHERE id=? AND status='queued'",(row["id"],))
                if row: run_task(row["id"],row["prompt"],row["agent"])
            except Exception:
                pass
            time.sleep(1 if row else 2)
    threading.Thread(target=loop,daemon=True).start()

@app.get("/health")
def health():
    return {"status":"ok","model":MODEL,"ai_configured":bool(client)}

@app.post("/tasks")
def create_task(data:TaskIn):
    task_id=str(uuid.uuid4());now=datetime.now(timezone.utc).isoformat()
    agent=data.agent if data.agent in AGENTS else "auto"
    with connect() as c:
        c.execute("INSERT INTO tasks(id,prompt,agent,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                  (task_id,data.prompt,agent,"queued",now,now))
    return {"id":task_id,"status":"queued"}

@app.get("/tasks")
def list_tasks():
    with connect() as c:
        rows=c.execute("SELECT id,prompt,agent,status,created_at,updated_at FROM tasks ORDER BY created_at DESC LIMIT 50").fetchall()
    return {"tasks":[dict(r) for r in rows]}

@app.get("/tasks/{task_id}")
def get_task(task_id:str):
    with connect() as c:
        row=c.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
    if not row: raise HTTPException(404,"Task not found")
    return dict(row)
