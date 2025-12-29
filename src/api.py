import subprocess
import sys
import json
import sqlite3
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel


try:
    from src.config import settings
except ImportError:
    # Fallback for some IDEs/Debuggers
    from config import settings

app = FastAPI(title="Metron Dynamic Policy Engine")
# --- DATABASE ---
def init_db():
    conn = sqlite3.connect(settings.DB_NAME) 
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS executions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, code TEXT, status TEXT, exit_code INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# Mount Static Files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

class CodeSubmission(BaseModel):
    code: str

class PolicyUpdate(BaseModel):
    item: str

# --- ROUTES ---

@app.get("/")
async def read_index():
    return FileResponse('src/static/index.html')

@app.get("/admin/policy")
async def get_policy():
    with open(settings.POLICY_FILE, 'r') as f: 
        return json.load(f)

@app.post("/admin/ban_module")
async def ban_module(update: PolicyUpdate):
    with open(settings.POLICY_FILE, 'r+') as f:
        data = json.load(f)
        if update.item not in data['banned_modules']:
            data['banned_modules'].append(update.item)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    return {"status": "updated", "banned": update.item}

@app.post("/admin/unban_module")
async def unban_module(update: PolicyUpdate):
    with open(settings.POLICY_FILE, 'r+') as f:
        data = json.load(f)
        if update.item in data['banned_modules']:
            data['banned_modules'].remove(update.item)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    return {"status": "updated", "unbanned": update.item}

@app.get("/history")
async def get_history():
    conn = sqlite3.connect(settings.DB_NAME) 
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, status, code, exit_code FROM executions ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/execute")
async def execute_code(submission: CodeSubmission):
    user_code = submission.code
    if not user_code: raise HTTPException(status_code=400, detail="No code")

    try:
        # Pass the Timeout from Config
        result = subprocess.run(
            [sys.executable, settings.SANDBOX_PATH, user_code],
            capture_output=True, text=True, 
            timeout=settings.TIMEOUT 
        )

        try:
            raw_output = result.stdout.strip().split('\n')[-1]
            report = json.loads(raw_output)
            
            if report.get("security_alerts"): status = "BLOCKED_STATIC"
            elif report.get("error") and "banned" in report["error"]: status = "BLOCKED_RUNTIME"
            elif report.get("file_access") and "BLOCKED" in str(report["file_access"]): status = "BLOCKED_FILE"
            elif report.get("error"): status = "RUNTIME_ERROR"
            else: status = "SUCCESS"
        except:
            report = {"error": "Invalid JSON", "raw": result.stdout}
            status = "SYSTEM_ERROR"

        conn = sqlite3.connect(settings.DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO executions (timestamp, code, status, exit_code) VALUES (?, ?, ?, ?)",
                  (datetime.now().isoformat(), user_code, status, result.returncode))
        conn.commit()
        conn.close()

        return {"status": "completed", "report": report, "audit_status": status}

    except subprocess.TimeoutExpired:
        conn = sqlite3.connect(settings.DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO executions (timestamp, code, status, exit_code) VALUES (?, ?, ?, ?)",
                  (datetime.now().isoformat(), user_code, "TIMEOUT", -1))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=408, detail=f"Timeout ({settings.TIMEOUT}s)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
