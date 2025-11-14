from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime
import uuid

# =============================================================
# APP CONFIG
# =============================================================

app = FastAPI(
    title="EduAI Principal - School Management System",
    description="AI-Powered School Management Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files safely
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

DB_FILE = "data.json"

# =============================================================
# MODELS
# =============================================================

class WaitlistEntry(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    type: str = "waitlist"
    created_at: str
    status: str = "pending"

class Enrollment(BaseModel):
    id: str
    name: str
    email: str
    track: str
    experience: str
    newsletter: bool = True
    scholarship_info: bool = True
    created_at: str
    status: str = "pending"

# =============================================================
# DB HELPERS
# =============================================================

def init_db():
    """Initialize or repair database file."""
    try:
        if not os.path.exists(DB_FILE):
            data = {
                "waitlist": [],
                "enrollments": [],
                "analytics": {
                    "page_views": 0,
                    "waitlist_count": 0,
                    "enrollment_count": 0,
                    "last_updated": datetime.now().isoformat()
                }
            }
            write_db(data)
            return data

        if os.path.getsize(DB_FILE) == 0:
            raise ValueError("Database empty")

        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"[DB ERROR] Resetting database: {e}")
        data = {
            "waitlist": [],
            "enrollments": [],
            "analytics": {
                "page_views": 0,
                "waitlist_count": 0,
                "enrollment_count": 0,
                "last_updated": datetime.now().isoformat()
            }
        }
        write_db(data)
        return data

def read_db():
    return init_db()

def write_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[WRITE ERROR] {e}")

# =============================================================
# ROUTES
# =============================================================

@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        html = """<h1>EduAI Principal</h1><p>Place index.html in static/ folder.</p>"""

    data = read_db()
    data["analytics"]["page_views"] += 1
    data["analytics"]["last_updated"] = datetime.now().isoformat()
    write_db(data)

    return HTMLResponse(content=html)


# WAITLIST
@app.post("/api/waitlist")
async def join_waitlist(email: str = Form(...), name: Optional[str] = Form(None)):
    try:
        data = read_db()

        if any(entry["email"] == email for entry in data["waitlist"]):
            return JSONResponse(status_code=400, content={"message": "Email already registered"})

        entry = WaitlistEntry(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            created_at=datetime.now().isoformat()
        )

        data["waitlist"].append(entry.dict())
        data["analytics"]["waitlist_count"] = len(data["waitlist"])
        data["analytics"]["last_updated"] = datetime.now().isoformat()

        write_db(data)
        return {"message": "Successfully added to waitlist!", "id": entry.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ENROLLMENT
@app.post("/api/enroll")
async def submit_enrollment(
    name: str = Form(...),
    email: str = Form(...),
    track: str = Form(...),
    experience: str = Form(...),
    newsletter: bool = Form(True),
    scholarship_info: bool = Form(True)
):
    try:
        data = read_db()

        entry = Enrollment(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            track=track,
            experience=experience,
            newsletter=newsletter,
            scholarship_info=scholarship_info,
            created_at=datetime.now().isoformat()
        )

        data["enrollments"].append(entry.dict())
        data["analytics"]["enrollment_count"] = len(data["enrollments"])
        data["analytics"]["last_updated"] = datetime.now().isoformat()

        write_db(data)
        return {"message": "Enrollment submitted!", "id": entry.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# STATS
@app.get("/api/stats")
async def stats():
    data = read_db()
    return {
        "analytics": data["analytics"],
        "waitlist_count": len(data["waitlist"]),
        "enrollment_count": len(data["enrollments"])
    }


# ADMIN GETTERS
@app.get("/api/enrollments")
async def get_enrollments():
    return {"enrollments": read_db()["enrollments"]}

@app.get("/api/waitlist")
async def get_waitlist():
    return {"waitlist": read_db()["waitlist"]}


# DELETE endpoints
@app.delete("/api/waitlist/{entry_id}")
async def delete_waitlist(entry_id: str):
    data = read_db()
    data["waitlist"] = [e for e in data["waitlist"] if e["id"] != entry_id]
    write_db(data)
    return {"message": "Deleted"}

@app.delete("/api/enrollments/{enrollment_id}")
async def delete_enrollment(enrollment_id: str):
    data = read_db()
    data["enrollments"] = [e for e in data["enrollments"] if e["id"] != enrollment_id]
    write_db(data)
    return {"message": "Deleted"}


# HEALTH CHECK
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "time": datetime.now().isoformat(),
        "db_exists": os.path.exists(DB_FILE),
    }


# RESET DB
@app.get("/reset-db")
async def reset_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()
    return {"message": "Database reset"}


# =============================================================
# RAILWAY STARTUP
# =============================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Railway injects PORT automatically
    uvicorn.run(app, host="0.0.0.0", port=port)
