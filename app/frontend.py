import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# Import using absolute paths since Streamlit runs the script directly
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.pomodoro_timer import pomodoro_manager
from app.schemas import TaskCreate, TaskUpdate, TaskStatus

# Configuration
st.set_page_config(page_title="Smart Task Scheduler", layout="wide")
API_BASE_URL = "http://localhost:8000"

# Title
st.title("🧠 Smart Task Scheduler")

# Sidebar navigation
page = st.sidebar.selectbox("Choose a page", ["Dashboard", "Tasks", "Schedule", "Analytics", "Pomodoro"])

if page == "Dashboard":
    st.header("Dashboard")
    
    # Fetch tasks stats
    try:
        tasks_response = requests.get(f"{API_BASE_URL}/tasks/")
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tasks", total_tasks)
            col2.metric("Completed", completed_tasks)
            col3.metric("Pending", total_tasks - completed_tasks if total_tasks > 0 else 0)
        else:
            st.error(f"Failed to fetch tasks: {tasks_response.status_code}")
            tasks = []
    except:
        st.warning("Could not connect to API. Make sure the backend is running.")
        tasks = []

    # Show recent tasks
    if tasks:
        st.subheader("Recent Tasks")
        df_tasks = pd.DataFrame(tasks[:10])  # Show last 10 tasks
        if not df_tasks.empty:
            df_tasks['deadline'] = pd.to_datetime(df_tasks['deadline']).dt.strftime('%Y-%m-%d %H:%M') if 'deadline' in df_tasks.columns else ""
            df_tasks['created_at'] = pd.to_datetime(df_tasks['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(df_tasks[['title', 'priority', 'status', 'deadline', 'created_at']], use_container_width=True)

elif page == "Tasks":
    st.header("Manage Tasks")
    
    # Task creation form
    with st.form("create_task_form"):
        st.subheader("Add New Task")
        title = st.text_input("Title *", help="Enter the task title")
        description = st.text_area("Description", help="Enter task description")
        deadline_date = st.date_input("Deadline Date", value=None, help="Set task deadline date")
        deadline_time = st.time_input("Deadline Time", value=None, help="Set task deadline time")
        
        # Combine date and time into a single datetime object if both are provided
        deadline = None
        if deadline_date is not None:
            if deadline_time is not None:
                deadline = datetime.combine(deadline_date, deadline_time)
            else:
                deadline = datetime.combine(deadline_date, datetime.min.time())
        priority = st.slider("Priority (1-5)", 1, 5, 3, help="Higher number means higher priority")
        important = st.checkbox("Important", help="Mark as important in Eisenhower matrix")
        estimated_duration = st.number_input("Estimated Duration (minutes)", min_value=5, max_value=480, value=30, help="Time needed to complete this task")
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted:
            if title.strip() == "":
                st.error("Title is required!")
            else:
                task_data = TaskCreate(
                    title=title,
                    description=description,
                    deadline=deadline,
                    priority=priority,
                    important=important,
                    estimated_duration=estimated_duration
                )
                
                try:
                    response = requests.post(f"{API_BASE_URL}/tasks/", json=task_data.model_dump())
                    if response.status_code == 200:
                        st.success("Task created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create task: {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
    
    # Display existing tasks
    try:
        response = requests.get(f"{API_BASE_URL}/tasks/")
        if response.status_code == 200:
            tasks = response.json()
            
            if tasks:
                st.subheader("All Tasks")
                
                for task in tasks:
                    status_color = {
                        'pending': 'gray',
                        'in_progress': 'blue', 
                        'completed': 'green',
                        'cancelled': 'red'
                    }.get(task['status'], 'gray')
                    
                    urgency_importance = "🔴 Urgent & Important" if task['urgent'] and task['important'] else \
                                        "🟡 Important" if task['important'] and not task['urgent'] else \
                                        "🟠 Urgent" if task['urgent'] and not task['important'] else \
                                        "⚪ Not Urgent/Important"
                    
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{task['title']}**")
                        if task['description']:
                            st.caption(task['description'][:100] + ("..." if len(task['description']) > 100 else ""))
                    
                    with col2:
                        st.markdown(f"📅 Deadline: {task['deadline'] or 'None'}")
                        st.markdown(f"⏱️ Duration: {task['estimated_duration']} min")
                        st.markdown(f"⭐ Priority: {task['priority']}/5 - {urgency_importance}")
                    
                    with col3:
                        st.markdown(f"<span style='color:{status_color}; font-weight:bold;'>{task['status'].replace('_', ' ').title()}</span>", unsafe_allow_html=True)
                        
                        # Status update buttons
                        if task['status'] == 'pending':
                            if st.button(f"Start##{task['id']}"):
                                update_data = {'status': 'in_progress'}
                                resp = requests.put(f"{API_BASE_URL}/tasks/{task['id']}", json=update_data)
                                if resp.status_code == 200:
                                    st.rerun()
                                else:
                                    st.error(f"Failed to update task: {resp.text}")
                        elif task['status'] == 'in_progress':
                            if st.button(f"Complete##{task['id']}"):
                                update_data = {'status': 'completed'}
                                resp = requests.put(f"{API_BASE_URL}/tasks/{task['id']}", json=update_data)
                                if resp.status_code == 200:
                                    st.rerun()
                                else:
                                    st.error(f"Failed to update task: {resp.text}")
                    
                    with col4:
                        if st.button(f"❌ Delete##{task['id']}"):
                            resp = requests.delete(f"{API_BASE_URL}/tasks/{task['id']}")
                            if resp.status_code == 200:
                                st.rerun()
                            else:
                                st.error(f"Failed to delete task: {resp.text}")
                    
                    st.divider()
            else:
                st.info("No tasks found. Create your first task above!")
        else:
            st.error(f"Failed to fetch tasks: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

elif page == "Schedule":
    st.header("Daily Schedule")
    
    selected_date = st.date_input("Select Date", value=datetime.today())
    
    try:
        response = requests.get(f"{API_BASE_URL}/schedule/daily?date={selected_date}")
        if response.status_code == 200:
            schedule = response.json()
            
            if schedule['schedule']:
                st.subheader(f"Schedule for {schedule['date']}")
                
                # Create a timeline visualization
                schedule_items = schedule['schedule']
                df_schedule = pd.DataFrame(schedule_items)
                
                if not df_schedule.empty:
                    df_schedule['start_time'] = pd.to_datetime(df_schedule['start_time'])
                    df_schedule['end_time'] = pd.to_datetime(df_schedule['end_time'])
                    
                    # Format times for display
                    df_schedule['time_range'] = df_schedule.apply(
                        lambda x: f"{x['start_time'].strftime('%H:%M')} - {x['end_time'].strftime('%H:%M')}", axis=1)
                    
                    for idx, item in df_schedule.iterrows():
                        with st.container():
                            st.markdown(f"### 📅 {item['title']}")
                            st.markdown(f"**Time:** {item['time_range']} | **Duration:** {item['duration']} min")
                            st.progress(min(item['duration']/60, 1.0))  # Progress bar based on duration
                            st.divider()
                else:
                    st.info("No scheduled tasks for this day.")
            else:
                st.info("No scheduled tasks for this day.")
        else:
            st.error(f"Failed to fetch schedule: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

elif page == "Analytics":
    st.header("Productivity Analytics")
    
    days = st.slider("Days to analyze", 1, 30, 7)
    
    try:
        response = requests.get(f"{API_BASE_URL}/analytics/productivity?days={days}")
        if response.status_code == 200:
            report = response.json()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Period", report['period'])
            col2.metric("Total Tasks", report['total_tasks'])
            col3.metric("Completion Rate", f"{report['productivity_percentage']:.1f}%")
            
            # Insights
            if report['insights']:
                st.subheader("Insights")
                for insight in report['insights']:
                    st.info(insight)
            
            # Recommendations
            if report['recommendations']:
                st.subheader("Recommendations")
                for rec in report['recommendations']:
                    st.success(rec)
            
            # If we have tasks, show a chart
            if report['total_tasks'] > 0:
                # Create a simple bar chart showing completed vs pending
                data = {
                    'Status': ['Completed', 'Pending'],
                    'Count': [report['completed_tasks'], report['total_tasks'] - report['completed_tasks']]
                }
                df = pd.DataFrame(data)
                
                fig = px.bar(df, x='Status', y='Count', color='Status',
                           title='Task Completion Overview',
                           color_discrete_map={'Completed': '#00FF00', 'Pending': '#FFA500'})
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Failed to fetch analytics: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

elif page == "Pomodoro":
    st.header("🍅 Pomodoro Timer")
    
    # Timer controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Start"):
            pomodoro_manager.start_timer()
            st.rerun()
    
    with col2:
        if st.button("⏸️ Pause"):
            pomodoro_manager.pause_timer()
            st.rerun()
    
    with col3:
        if st.button("⏹️ Stop"):
            pomodoro_manager.stop_timer()
            st.rerun()
    
    with col4:
        if st.button("🔄 Reset"):
            pomodoro_manager.reset_timer()
            st.rerun()
    
    # Display timer
    timer_status = pomodoro_manager.get_status()
    
    # Calculate minutes and seconds
    minutes = timer_status.remaining_time // 60
    seconds = timer_status.remaining_time % 60
    
    # Display large timer
    timer_display = f"{minutes:02d}:{seconds:02d}"
    
    if timer_status.is_working:
        st.markdown(f"<h1 style='text-align: center; color: red;'>WORK: {timer_display}</h1>", unsafe_allow_html=True)
        st.progress((timer_status.work_duration * 60 - timer_status.remaining_time) / (timer_status.work_duration * 60))
    else:
        st.markdown(f"<h1 style='text-align: center; color: green;'>BREAK: {timer_display}</h1>", unsafe_allow_html=True)
        if timer_status.current_session % timer_status.sessions_before_long_break == 0:
            st.progress((timer_status.long_break_duration * 60 - timer_status.remaining_time) / (timer_status.long_break_duration * 60))
        else:
            st.progress((timer_status.break_duration * 60 - timer_status.remaining_time) / (timer_status.break_duration * 60))
    
    # Show session info
    st.write(f"Session: {timer_status.current_session}/{timer_status.sessions_before_long_break}")
    st.write(f"Mode: {'Working' if timer_status.is_working else 'Break'}")
    st.write(f"Status: {'Active' if timer_status.is_active else 'Inactive'}")