from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Issue, Base
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class IssueCreate(BaseModel):
    student_name: str
    room_number: str
    category: str
    description: str

@app.post("/submit")
def submit_issue(issue: IssueCreate, db: Session = Depends(get_db)):
    new_issue = Issue(**issue.dict())
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    return {"issue_id": new_issue.id, "status": new_issue.status}

@app.get("/track/{issue_id}")
def track_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        return {"error": "Issue not found"}
    return issue

@app.get("/admin/issues")
def view_all(db: Session = Depends(get_db)):
    return db.query(Issue).all()

@app.put("/admin/update/{issue_id}")
def update_status(issue_id: int, status: str, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        return {"error": "Issue not found"}
    issue.status = status
    db.commit()
    return {"message": "Status updated"}
app.mount("/static", StaticFiles(directory="static"), name="static")
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def login_page():
    return FileResponse("static/login.html")

@app.get("/")
def serve_frontend():
    return FileResponse("static/login.html")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

