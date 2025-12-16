import requests
from typing import List, Dict, Any
from datetime import datetime
from ..models import Task
from ..schemas import TaskCreate

class TodoistIntegration:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.todoist.com/rest/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks from Todoist"""
        url = f"{self.base_url}/tasks"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch tasks: {response.status_code} - {response.text}")
        
        return response.json()

    def todoist_task_to_smart_task(self, todoist_task: Dict[str, Any]) -> TaskCreate:
        """Convert a Todoist task to a TaskCreate object"""
        # Map Todoist priority to our 1-5 scale
        # Todoist priorities: P1 (highest) to P4 (lowest)
        priority_mapping = {
            'P1': 5,  # Urgent
            'P2': 4,  # High
            'P3': 3,  # Medium
            'P4': 2   # Low
        }
        
        priority = priority_mapping.get(todoist_task.get('priority', 'P3'), 3)
        
        # Parse due date if available
        deadline = None
        if todoist_task.get('due'):
            due_info = todoist_task['due']
            due_string = due_info.get('datetime') or due_info.get('date')
            if due_string:
                try:
                    deadline = datetime.fromisoformat(due_string.replace('Z', '+00:00'))
                except ValueError:
                    # Handle different date formats
                    try:
                        deadline = datetime.strptime(due_string.split('T')[0], '%Y-%m-%d')
                    except ValueError:
                        deadline = None
        
        # Estimate duration based on labels or content
        estimated_duration = 30  # Default 30 minutes
        labels = todoist_task.get('labels', [])
        
        # Look for labels that might indicate duration
        for label in labels:
            if 'short' in label.lower():
                estimated_duration = 15
                break
            elif 'long' in label.lower():
                estimated_duration = 60
                break
            elif 'meeting' in label.lower():
                estimated_duration = 45
                break
        
        return TaskCreate(
            title=todoist_task.get('content', 'Untitled Task'),
            description="",  # Todoist tasks don't have a separate description field
            deadline=deadline,
            priority=priority,
            important=todoist_task.get('priority', 'P3') in ['P1', 'P2'],  # P1 and P2 are important
            estimated_duration=estimated_duration,
            source='todoist'
        )

    def import_tasks(self, db) -> List[Task]:
        """Import tasks from Todoist to the database"""
        todoist_tasks = self.get_tasks()
        imported_tasks = []
        
        for todoist_task in todoist_tasks:
            smart_task = self.todoist_task_to_smart_task(todoist_task)
            
            # Create task in database
            db_task = Task(
                title=smart_task.title,
                description=smart_task.description,
                deadline=smart_task.deadline,
                priority=smart_task.priority,
                important=smart_task.important,
                estimated_duration=smart_task.estimated_duration,
                source=smart_task.source
            )
            
            db.add(db_task)
            db.commit()
            db.refresh(db_task)
            imported_tasks.append(db_task)
        
        return imported_tasks

    def sync_task_completion(self, task_id: int, completed: bool = True):
        """Sync task completion status back to Todoist"""
        if completed:
            url = f"{self.base_url}/tasks/{task_id}/close"
            response = requests.post(url, headers=self.headers)
        else:
            url = f"{self.base_url}/tasks/{task_id}/reopen"
            response = requests.post(url, headers=self.headers)
        
        if response.status_code not in [200, 204]:
            raise Exception(f"Failed to sync task status: {response.status_code} - {response.text}")
        
        return response.status_code == 200