import asyncio
from typing import Optional
from telegram import Bot
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
from .models import Task

class NotificationService:
    def __init__(self, telegram_token: Optional[str] = None, slack_token: Optional[str] = None):
        self.telegram_bot = Bot(token=telegram_token) if telegram_token else None
        self.slack_client = WebClient(token=slack_token) if slack_token else None

    async def send_telegram_notification(self, chat_id: str, message: str):
        """Send notification via Telegram"""
        if not self.telegram_bot:
            print("Telegram bot not configured")
            return
        
        try:
            await self.telegram_bot.send_message(chat_id=chat_id, text=message)
            print(f"Telegram notification sent to {chat_id}")
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")

    def send_slack_notification(self, channel: str, message: str):
        """Send notification via Slack"""
        if not self.slack_client:
            print("Slack client not configured")
            return
        
        try:
            response = self.slack_client.chat_postMessage(channel=channel, text=message)
            print(f"Slack notification sent to {channel}")
        except SlackApiError as e:
            print(f"Failed to send Slack notification: {e.response['error']}")

    def notify_upcoming_task(self, task: Task, user_preferences: dict):
        """Notify user about upcoming task"""
        if not task.scheduled_start:
            return
        
        time_to_start = task.scheduled_start - datetime.now()
        minutes_to_start = int(time_to_start.total_seconds() / 60)
        
        message = f"⏰ Upcoming Task: {task.title}\n"
        message += f"Starts in: {minutes_to_start} minutes\n"
        message += f"Priority: {task.priority}/5\n"
        if task.deadline:
            message += f"Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}"
        
        # Send notifications based on user preferences
        if user_preferences.get('telegram_chat_id'):
            asyncio.create_task(
                self.send_telegram_notification(
                    chat_id=user_preferences['telegram_chat_id'],
                    message=message
                )
            )
        
        if user_preferences.get('slack_channel'):
            self.send_slack_notification(
                channel=user_preferences['slack_channel'],
                message=message
            )

    def notify_task_reminder(self, task: Task, user_preferences: dict):
        """Send reminder for a task"""
        message = f"🔔 Reminder: It's time to work on '{task.title}'\n"
        message += f"Priority: {task.priority}/5\n"
        if task.deadline:
            message += f"Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}"
        
        # Send notifications based on user preferences
        if user_preferences.get('telegram_chat_id'):
            asyncio.create_task(
                self.send_telegram_notification(
                    chat_id=user_preferences['telegram_chat_id'],
                    message=message
                )
            )
        
        if user_preferences.get('slack_channel'):
            self.send_slack_notification(
                channel=user_preferences['slack_channel'],
                message=message
            )

    def notify_pomodoro_session_change(self, is_work_session: bool, user_preferences: dict):
        """Notify user about Pomodoro session change"""
        if is_work_session:
            message = "🍅 Time to focus! Starting work session."
        else:
            message = "🎉 Great job! Take a break during your Pomodoro session."
        
        # Send notifications based on user preferences
        if user_preferences.get('telegram_chat_id'):
            asyncio.create_task(
                self.send_telegram_notification(
                    chat_id=user_preferences['telegram_chat_id'],
                    message=message
                )
            )
        
        if user_preferences.get('slack_channel'):
            self.send_slack_notification(
                channel=user_preferences['slack_channel'],
                message=message
            )