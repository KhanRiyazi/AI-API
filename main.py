from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime
import uuid

app = FastAPI(
    title="EduAI Principal - School Management System",
    description="AI-Powered School Management Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database file
DB_FILE = "data.json"

# Pydantic models
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

# Initialize database with better error handling
def init_db():
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
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return data
        
        # Check if file is empty or corrupted
        file_size = os.path.getsize(DB_FILE)
        if file_size == 0:
            raise ValueError("Database file is empty")
            
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
            
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Database corrupted, recreating: {e}")
        # Create fresh database
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
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return data
    except Exception as e:
        print(f"Error initializing database: {e}")
        return {
            "waitlist": [],
            "enrollments": [],
            "analytics": {
                "page_views": 0,
                "waitlist_count": 0,
                "enrollment_count": 0,
                "last_updated": datetime.now().isoformat()
            }
        }

def read_db():
    return init_db()

def write_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error writing to database: {e}")

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Update page views
        data = read_db()
        data["analytics"]["page_views"] += 1
        data["analytics"]["last_updated"] = datetime.now().isoformat()
        write_db(data)
        
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EduAI Principal - School Management</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #0f1724; color: white; }
                .container { max-width: 800px; margin: 0 auto; text-align: center; }
                .btn { background: #6ee7b7; color: #04121a; padding: 12px 24px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; margin: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏫 EduAI Principal</h1>
                <p>AI-Powered School Management System</p>
                <p>FastAPI backend is running successfully!</p>
                <p>Place your index.html file in the static/ directory.</p>
                <p>
                    <a href="/docs"><button class="btn">API Documentation</button></a>
                    <a href="/health"><button class="btn">Health Check</button></a>
                </p>
            </div>
        </body>
        </html>
        """)

@app.post("/api/waitlist")
async def join_waitlist(
    email: str = Form(...),
    name: Optional[str] = Form(None),
    type: str = Form("waitlist")
):
    try:
        data = read_db()
        
        # Check if email already exists
        existing = [entry for entry in data["waitlist"] if entry["email"] == email]
        if existing:
            return JSONResponse(
                status_code=400,
                content={"message": "Email already registered"}
            )
        
        # Create new entry
        entry = WaitlistEntry(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            type=type,
            created_at=datetime.now().isoformat()
        )
        
        data["waitlist"].append(entry.dict())
        data["analytics"]["waitlist_count"] = len(data["waitlist"])
        data["analytics"]["last_updated"] = datetime.now().isoformat()
        write_db(data)
        
        return {"message": "Successfully added to waitlist!", "id": entry.id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
        enrollment = Enrollment(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            track=track,
            experience=experience,
            newsletter=newsletter,
            scholarship_info=scholarship_info,
            created_at=datetime.now().isoformat()
        )
        
        data["enrollments"].append(enrollment.dict())
        data["analytics"]["enrollment_count"] = len(data["enrollments"])
        data["analytics"]["last_updated"] = datetime.now().isoformat()
        write_db(data)
        
        return {"message": "Enrollment submitted successfully!", "id": enrollment.id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    try:
        data = read_db()
        return {
            "analytics": data["analytics"],
            "waitlist_count": len(data["waitlist"]),
            "enrollment_count": len(data["enrollments"])
        }
    except Exception as e:
        print(f"Error in get_stats: {e}")
        return {
            "analytics": {
                "page_views": 0,
                "waitlist_count": 0,
                "enrollment_count": 0,
                "last_updated": datetime.now().isoformat()
            },
            "waitlist_count": 0,
            "enrollment_count": 0
        }

@app.get("/api/waitlist")
async def get_waitlist():
    try:
        data = read_db()
        return {"waitlist": data["waitlist"]}
    except Exception as e:
        print(f"Error in get_waitlist: {e}")
        return {"waitlist": []}

@app.get("/api/enrollments")
async def get_enrollments():
    try:
        data = read_db()
        return {"enrollments": data["enrollments"]}
    except Exception as e:
        print(f"Error in get_enrollments: {e}")
        return {"enrollments": []}

@app.delete("/api/waitlist/{entry_id}")
async def delete_waitlist_entry(entry_id: str):
    try:
        data = read_db()
        data["waitlist"] = [entry for entry in data["waitlist"] if entry["id"] != entry_id]
        data["analytics"]["waitlist_count"] = len(data["waitlist"])
        data["analytics"]["last_updated"] = datetime.now().isoformat()
        write_db(data)
        return {"message": "Waitlist entry deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/enrollments/{enrollment_id}")
async def delete_enrollment(enrollment_id: str):
    try:
        data = read_db()
        data["enrollments"] = [enrollment for enrollment in data["enrollments"] if enrollment["id"] != enrollment_id]
        data["analytics"]["enrollment_count"] = len(data["enrollments"])
        data["analytics"]["last_updated"] = datetime.now().isoformat()
        write_db(data)
        return {"message": "Enrollment deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulate-data")
async def simulate_data():
    try:
        data = read_db()
        
        sample_waitlist = WaitlistEntry(
            id=str(uuid.uuid4()),
            email="student@school.edu",
            name="Sample Student",
            type="waitlist",
            created_at=datetime.now().isoformat()
        )
        
        sample_enrollment = Enrollment(
            id=str(uuid.uuid4()),
            name="Sample Teacher",
            email="teacher@school.edu",
            track="Mathematics",
            experience="Expert",
            created_at=datetime.now().isoformat()
        )
        
        data["waitlist"].append(sample_waitlist.dict())
        data["enrollments"].append(sample_enrollment.dict())
        
        data["analytics"]["waitlist_count"] = len(data["waitlist"])
        data["analytics"]["enrollment_count"] = len(data["enrollments"])
        data["analytics"]["last_updated"] = datetime.now().isoformat()
        
        write_db(data)
        return {"message": "Sample data added successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "EduAI Principal API",
        "database": "operational" if os.path.exists(DB_FILE) else "initializing"
    }

@app.get("/reset-db")
async def reset_database():
    """Endpoint to reset the database if it gets corrupted"""
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        init_db()
        return {"message": "Database reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)