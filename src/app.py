"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import json
from pathlib import Path
from typing import Optional

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Security
security = HTTPBearer(auto_error=False)

# Load teacher credentials
def load_teachers():
    try:
        with open(os.path.join(current_dir, 'teachers.json'), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"teachers": []}

# Simple session storage (in production, use proper session management)
active_sessions = set()

def authenticate_teacher(username: str, password: str) -> bool:
    """Authenticate teacher credentials"""
    teachers_data = load_teachers()
    for teacher in teachers_data.get('teachers', []):
        if teacher['username'] == username and teacher['password'] == password:
            return True
    return False

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current authenticated user"""
    if credentials is None:
        return None
    
    # Simple token validation (in production, use proper JWT tokens)
    if credentials.credentials in active_sessions:
        return credentials.credentials
    return None

def require_teacher_auth(current_user = Depends(get_current_user)):
    """Require teacher authentication"""
    if current_user is None:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required. Only teachers can perform this action."
        )
    return current_user

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    """Teacher login endpoint"""
    if authenticate_teacher(username, password):
        # Create a simple token (in production, use proper JWT)
        token = f"teacher_{username}_{len(active_sessions)}"
        active_sessions.add(token)
        return {
            "message": "Login successful",
            "token": token,
            "username": username
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )


@app.post("/logout")
def logout(current_user = Depends(get_current_user)):
    """Teacher logout endpoint"""
    if current_user:
        active_sessions.discard(current_user)
        return {"message": "Logout successful"}
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")


@app.get("/auth/status")
def auth_status(current_user = Depends(get_current_user)):
    """Check authentication status"""
    if current_user:
        username = current_user.split('_')[1] if '_' in current_user else 'unknown'
        return {
            "authenticated": True,
            "username": username
        }
    else:
        return {"authenticated": False}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, current_user = Depends(require_teacher_auth)):
    """Sign up a student for an activity (requires teacher authentication)"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, current_user = Depends(require_teacher_auth)):
    """Unregister a student from an activity (requires teacher authentication)"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
