import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional

# Import using absolute paths since Streamlit runs the script directly
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas import PomodoroTimer

class PomodoroTimerManager:
    def __init__(self):
        self.timer = PomodoroTimer()
        self.timer_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.on_session_complete: Optional[Callable] = None

    def start_timer(self):
        """Start the Pomodoro timer"""
        if self.timer.is_active:
            return False  # Timer already running
        
        self.timer.is_active = True
        self.stop_event.clear()
        
        # Set initial remaining time based on current mode
        if self.timer.is_working:
            self.timer.remaining_time = self.timer.work_duration * 60
        else:
            if self.timer.current_session % self.timer.sessions_before_long_break == 0:
                self.timer.remaining_time = self.timer.long_break_duration * 60
            else:
                self.timer.remaining_time = self.timer.break_duration * 60
        
        self.timer_thread = threading.Thread(target=self._timer_worker)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        return True

    def pause_timer(self):
        """Pause the Pomodoro timer"""
        self.timer.is_active = False
        self.stop_event.set()
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join()

    def stop_timer(self):
        """Stop and reset the Pomodoro timer"""
        self.timer.is_active = False
        self.timer.remaining_time = 0
        self.stop_event.set()
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join()

    def _timer_worker(self):
        """Internal worker function that runs in a separate thread"""
        while self.timer.remaining_time > 0 and not self.stop_event.is_set():
            time.sleep(1)
            if self.timer.is_active:
                self.timer.remaining_time -= 1
        
        if self.timer.remaining_time <= 0 and not self.stop_event.is_set():
            # Session completed
            self._complete_session()

    def _complete_session(self):
        """Handle session completion"""
        if self.timer.is_working:
            # Work session completed, switch to break
            self.timer.is_working = False
            self.timer.current_session += 1
            if self.timer.current_session % self.timer.sessions_before_long_break == 0:
                self.timer.remaining_time = self.timer.long_break_duration * 60
            else:
                self.timer.remaining_time = self.timer.break_duration * 60
        else:
            # Break session completed, switch to work
            self.timer.is_working = True
            self.timer.remaining_time = self.timer.work_duration * 60
        
        # Call the callback if registered
        if self.on_session_complete:
            self.on_session_complete(self.timer.is_working)

    def reset_timer(self):
        """Reset the timer to initial state"""
        self.pause_timer()
        self.timer.current_session = 1
        self.timer.is_working = True
        self.timer.remaining_time = self.timer.work_duration * 60
        self.timer.is_active = False

    def get_status(self):
        """Get current timer status"""
        return self.timer


# Global instance for use throughout the application
pomodoro_manager = PomodoroTimerManager()