from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import List
from . import models, schemas

def create_task(db: Session, task: schemas.TaskCreate):
    """Create a new task in the database"""
    # Calculate urgency based on deadline proximity (within 24 hours)
    urgent = False
    if task.deadline:
        time_to_deadline = task.deadline - datetime.now()
        urgent = time_to_deadline <= timedelta(hours=24)
    
    db_task = models.Task(
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        priority=task.priority,
        urgent=urgent,
        important=task.important,
        estimated_duration=task.estimated_duration,
        source=task.source
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    """Retrieve all tasks from the database"""
    return db.query(models.Task).offset(skip).limit(limit).all()

def get_task(db: Session, task_id: int):
    """Retrieve a specific task by ID"""
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate):
    """Update a specific task"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        return None
    
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    # Update urgent status based on new deadline
    if 'deadline' in update_data and db_task.deadline:
        time_to_deadline = db_task.deadline - datetime.now()
        db_task.urgent = time_to_deadline <= timedelta(hours=24)
    
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    """Delete a specific task"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        return False
    
    db.delete(db_task)
    db.commit()
    return True

def generate_daily_schedule(db: Session, target_date: datetime.date):
    """Generate daily schedule based on Eisenhower matrix and time blocks"""
    # Get all pending tasks
    pending_tasks = db.query(models.Task).filter(
        and_(
            models.Task.status != "completed",
            models.Task.deadline >= datetime.combine(target_date, datetime.min.time()),
            models.Task.deadline <= datetime.combine(target_date, datetime.max.time()) if target_date else True
        )
    ).order_by(models.Task.priority.desc(), models.Task.urgent.desc()).all()
    
    # Simple scheduling algorithm - assign tasks to time slots
    # Starting from 9 AM to 6 PM with breaks
    start_time = datetime.combine(target_date, datetime.min.time()).replace(hour=9, minute=0)
    schedule_items = []
    
    for i, task in enumerate(pending_tasks):
        # Calculate slot duration (minimum 15 minutes, rounded to 15-min intervals)
        duration = max(15, ((task.estimated_duration + 14) // 15) * 15)  # Round up to nearest 15 min
        
        # Add some buffer time between tasks
        if i > 0:
            start_time += timedelta(minutes=5)  # 5-minute break between tasks
        
        end_time = start_time + timedelta(minutes=duration)
        
        # Skip if we go beyond 6 PM
        if end_time.hour > 18:
            break
            
        schedule_items.append(schemas.DailyScheduleItem(
            task_id=task.id,
            title=task.title,
            start_time=start_time,
            end_time=end_time,
            duration=duration
        ))
        
        start_time = end_time
    
    return schemas.DailySchedule(
        date=target_date.isoformat(),
        schedule=schedule_items
    )

def get_productivity_report(db: Session, days: int = 7):
    """Generate productivity analytics report"""
    start_date = datetime.now() - timedelta(days=days)
    
    # Total tasks in the period
    total_tasks_query = db.query(models.Task).filter(models.Task.created_at >= start_date)
    total_tasks = total_tasks_query.count()
    
    # Completed tasks in the period
    completed_tasks_query = db.query(models.Task).filter(
        and_(
            models.Task.created_at >= start_date,
            models.Task.status == "completed"
        )
    )
    completed_tasks = completed_tasks_query.count()
    
    # Calculate productivity percentage
    productivity_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Generate insights
    insights = []
    if total_tasks > 0:
        low_priority_tasks = db.query(models.Task).filter(
            and_(
                models.Task.created_at >= start_date,
                models.Task.priority <= 2  # Low priority tasks (1-2)
            )
        ).count()
        
        low_priority_percentage = (low_priority_tasks / total_tasks * 100) if total_tasks > 0 else 0
        insights.append(f"You spent {low_priority_percentage:.0f}% of your time on low-priority tasks.")
    
    # Generate recommendations
    recommendations = []
    if low_priority_tasks > 0:
        recommendations.append("Consider focusing more on high-priority tasks to improve productivity.")
    
    if productivity_percentage < 50:
        recommendations.append("Try to improve your completion rate by breaking large tasks into smaller ones.")
    
    return schemas.ProductivityReport(
        period=f"Last {days} days",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        productivity_percentage=productivity_percentage,
        insights=insights,
        recommendations=recommendations
    )