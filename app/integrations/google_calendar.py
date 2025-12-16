import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from ..models import Task
from ..schemas import TaskCreate

class GoogleCalendarIntegration:
    def __init__(self, credentials_path: str = None, token_path: str = None):
        self.credentials_path = credentials_path or "credentials.json"
        self.token_path = token_path or "token.json"
        self.scopes = ['https://www.googleapis.com/auth/calendar.readonly']
        self.service = None

    def authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        
        # If no valid credentials, initiate OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = Flow.from_client_secrets_file(
                    self.credentials_path,
                    scopes=self.scopes,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                )
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                print(f'Please visit this URL to authorize the application: {auth_url}')
                code = input('Enter the authorization code: ')
                
                flow.fetch_token(code=code)
                creds = flow.credentials
            
            # Save credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        return creds

    def get_events(self, calendar_id: str = 'primary', time_min: datetime = None, time_max: datetime = None) -> List[Dict[str, Any]]:
        """Get events from Google Calendar"""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Set default time range (next 7 days)
        if not time_min:
            time_min = datetime.utcnow()
        if not time_max:
            time_max = time_min + timedelta(days=7)
        
        # Convert to RFC3339 format
        time_min_rfc3339 = time_min.isoformat() + 'Z'
        time_max_rfc3339 = time_max.isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=time_min_rfc3339,
            timeMax=time_max_rfc3339,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events

    def events_to_tasks(self, events: List[Dict[str, Any]]) -> List[TaskCreate]:
        """Convert Google Calendar events to TaskCreate objects"""
        tasks = []
        
        for event in events:
            # Extract start time
            start_time = None
            if 'date' in event['start']:  # All-day event
                start_time = datetime.fromisoformat(event['start']['date'])
            elif 'dateTime' in event['start']:
                start_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            
            # Determine priority based on event properties
            priority = 3  # Default priority
            if 'priority' in event:
                priority = int(event['priority'])
            elif 'high' in event.get('summary', '').lower():
                priority = 5
            elif 'medium' in event.get('summary', '').lower():
                priority = 3
            elif 'low' in event.get('summary', '').lower():
                priority = 1
            
            # Estimate duration based on event length (default 30 mins)
            estimated_duration = 30
            if 'end' in event and 'start' in event:
                if 'dateTime' in event['start'] and 'dateTime' in event['end']:
                    start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                    estimated_duration = int((end_dt - start_dt).total_seconds() / 60)
            
            task = TaskCreate(
                title=event.get('summary', 'Untitled Event'),
                description=event.get('description', ''),
                deadline=start_time,
                priority=priority,
                estimated_duration=estimated_duration,
                source='google_calendar'
            )
            
            tasks.append(task)
        
        return tasks

    def import_events_as_tasks(self, db, calendar_id: str = 'primary') -> List[Task]:
        """Import events from Google Calendar as tasks in the database"""
        events = self.get_events(calendar_id=calendar_id)
        task_objects = self.events_to_tasks(events)
        
        imported_tasks = []
        for task_obj in task_objects:
            # Create task in database
            db_task = Task(
                title=task_obj.title,
                description=task_obj.description,
                deadline=task_obj.deadline,
                priority=task_obj.priority,
                estimated_duration=task_obj.estimated_duration,
                source=task_obj.source
            )
            db.add(db_task)
            db.commit()
            db.refresh(db_task)
            imported_tasks.append(db_task)
        
        return imported_tasks