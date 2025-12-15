from datetime import datetime, timedelta
from typing import List
from ..models import Task
from ..schemas import TaskResponse

def categorize_task(task: Task) -> str:
    """
    Categorize a task based on the Eisenhower Matrix:
    - Urgent and Important (Do First)
    - Important but Not Urgent (Schedule)
    - Urgent but Not Important (Delegate)
    - Neither Urgent nor Important (Eliminate)
    """
    if task.urgent and task.important:
        return "do_first"
    elif not task.urgent and task.important:
        return "schedule"
    elif task.urgent and not task.important:
        return "delegate"
    else:
        return "eliminate"

def prioritize_by_eisenhower(tasks: List[Task]) -> List[Task]:
    """
    Sort tasks based on Eisenhower matrix priority:
    1. Do First (Urgent and Important)
    2. Schedule (Important but Not Urgent)
    3. Delegate (Urgent but Not Important)
    4. Eliminate (Neither Urgent nor Important)
    """
    def get_priority_score(task: Task) -> int:
        category = categorize_task(task)
        if category == "do_first":
            return 4  # Highest priority
        elif category == "schedule":
            return 3
        elif category == "delegate":
            return 2
        else:
            return 1  # Lowest priority
    
    # Sort tasks by their Eisenhower priority score, then by deadline (if exists), then by original priority
    sorted_tasks = sorted(tasks, key=lambda t: (-get_priority_score(t), 
                                               t.deadline if t.deadline else datetime.max,
                                               -t.priority))
    return sorted_tasks

def calculate_urgency(task: Task) -> bool:
    """
    Calculate if a task is urgent based on deadline proximity
    A task is considered urgent if it's due within 24 hours
    """
    if not task.deadline:
        return False
    
    time_to_deadline = task.deadline - datetime.now()
    return time_to_deadline <= timedelta(hours=24)