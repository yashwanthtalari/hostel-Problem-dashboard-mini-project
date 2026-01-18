from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import csv
import os

from database import SessionLocal, engine
from models import Issue, Base
from auth import require_login

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    SessionMiddleware, secret_key="supersecretkey", same_site="lax", https_only=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# CSV paths
LOGIN_CSV = "data/logins.csv"
ISSUES_CSV = "data/issues.csv"


# ---------------- DATABASE ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- SCHEMAS ----------------
class IssueCreate(BaseModel):
    student_name: str
    room_number: str
    category: str
    description: str


# ---------------- LOGIN ----------------
@app.get("/")
def login_page():
    return FileResponse("static/login.html")


@app.post("/login")
def login(
    username: str = Form(...), password: str = Form(...), request: Request = None
):

    # Demo validation
    if username and password:
        request.session["user"] = username

        # Save login to CSV
        os.makedirs("data", exist_ok=True)
        with open(LOGIN_CSV, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([username, password])

        return RedirectResponse("/index", status_code=302)

    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    response = RedirectResponse(url="/", status_code=302)
    return response


# ---------------- PAGES ----------------
@app.get("/index")
def dashboard(request: Request):
    if not require_login(request):
        return RedirectResponse("/")
    return FileResponse("static/index.html")


@app.get("/track")
def track_page(request: Request):
    if not require_login(request):
        return RedirectResponse("/")
    return FileResponse("static/track.html")


# ---------------- API ----------------
@app.post("/submit")
def submit_issue(issue: IssueCreate, request: Request, db: Session = Depends(get_db)):

    username = request.session.get("user")

    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")

    # Prevent duplicate issue by same user
    existing = db.query(Issue).filter(Issue.student_name == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already submitted an issue")

    # Save to database
    new_issue = Issue(**issue.dict(), status="Open")
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)

    # Save to CSV
    os.makedirs("data", exist_ok=True)
    with open(ISSUES_CSV, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                new_issue.id,
                new_issue.student_name,
                new_issue.room_number,
                new_issue.category,
                new_issue.description,
                new_issue.status,
            ]
        )

    return JSONResponse({"message": "Issue submitted", "issue_id": new_issue.id})


@app.get("/track/{issue_id}")
def track_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return {
        "id": issue.id,
        "student_name": issue.student_name,
        "room": issue.room_number,
        "category": issue.category,
        "description": issue.description,
        "status": issue.status,
    }
