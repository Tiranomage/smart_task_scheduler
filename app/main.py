from fastapi import FastAPI, Depends, HTTPException
from typing import List
import uvicorn
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .database import get_db
from . import models, schemas, crud

app = FastAPI(title="Smart Task Scheduler", description="An intelligent task scheduling system")

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Task Scheduler API"}

@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    return crud.create_task(db=db, task=task)

@app.get("/tasks/", response_model=List[schemas.TaskResponse])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tasks"""
    tasks = crud.get_tasks(db, skip=skip, limit=limit)
    return tasks

@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task"""
    task = crud.get_task(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """Update a specific task"""
    updated_task = crud.update_task(db=db, task_id=task_id, task_update=task_update)
    if updated_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a specific task"""
    deleted = crud.delete_task(db=db, task_id=task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

@app.get("/schedule/daily", response_model=schemas.DailySchedule)
def get_daily_schedule(date: str = None, db: Session = Depends(get_db)):
    """Generate daily schedule based on Eisenhower matrix"""
    target_date = datetime.now().date()
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    return crud.generate_daily_schedule(db, target_date)

@app.get("/analytics/productivity", response_model=schemas.ProductivityReport)
def get_productivity_report(days: int = 7, db: Session = Depends(get_db)):
    """Get productivity analytics report"""
    return crud.get_productivity_report(db, days)

@app.post("/integrations/google-calendar/import")
def import_from_google_calendar(credentials: schemas.GoogleCalendarCredentials, db: Session = Depends(get_db)):
    """Import tasks from Google Calendar"""
    # Implementation would connect to Google Calendar API
    # This is a placeholder for now
    return {"status": "import started", "credentials": credentials}

@app.post("/integrations/todoist/import")
def import_from_todoist(token: str, db: Session = Depends(get_db)):
    """Import tasks from Todoist"""
    # Implementation would connect to Todoist API
    # This is a placeholder for now
    return {"status": "import started", "token": token}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)