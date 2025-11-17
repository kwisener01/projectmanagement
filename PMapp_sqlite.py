import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
from contextlib import contextmanager

# Database configuration
DB_PATH = "project_management.db"

# Context manager for database connections
@contextmanager
def get_db_connection():
    """Create a database connection with proper cleanup"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

# Initialize database
def init_database():
    """Create tables if they don't exist"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                priority TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                assigned_to TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_assigned
            ON tasks(assigned_to)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status
            ON tasks(status)
        """)

        conn.commit()

        # Create default admin user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            hashed_pw = hash_password("admin123")
            cursor.execute(
                "INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
                ("admin", hashed_pw, "Administrator")
            )
            conn.commit()

# Hash password
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication
def authenticate_user(username, password):
    """Verify user credentials"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        hashed_pw = hash_password(password)
        cursor.execute(
            "SELECT id, username, name FROM users WHERE username = ? AND password = ?",
            (username, hashed_pw)
        )
        user = cursor.fetchone()
        return dict(user) if user else None

# Get all tasks
def get_tasks(assigned_to=None, status=None):
    """Fetch tasks with optional filters"""
    with get_db_connection() as conn:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        df = pd.read_sql_query(query, conn, params=params if params else None)
        return df

# Add task
def add_task(task_name, priority, due_date, assigned_to):
    """Add a new task to the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (task_name, priority, due_date, assigned_to)
                VALUES (?, ?, ?, ?)
            """, (task_name, priority, due_date, assigned_to))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error adding task: {e}")
        return False

# Update task status
def update_task_status(task_id, status):
    """Update task status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, task_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Error updating task: {e}")
        return False

# Delete task
def delete_task(task_id):
    """Delete a task from the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Error deleting task: {e}")
        return False

# Get task statistics
def get_task_statistics(username=None):
    """Get task statistics for dashboard"""
    with get_db_connection() as conn:
        query = """
            SELECT
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) as completed
            FROM tasks
        """
        if username:
            query += " WHERE assigned_to = ?"
            cursor = conn.cursor()
            cursor.execute(query, (username,))
        else:
            cursor = conn.cursor()
            cursor.execute(query)

        result = cursor.fetchone()
        return dict(result) if result else {}

# Login System
def login():
    st.title("🚀 Smart Project Management App")
    st.markdown("### SQLite-Powered (100x Faster!)")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.info("Default credentials: **admin** / **admin123**")

        col1, col2 = st.columns([2, 1])

        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.button("Login", use_container_width=True)

            if login_btn:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user['username']
                    st.session_state.user_name = user['name']
                    st.success(f"Welcome, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    else:
        if st.sidebar.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.clear()
            st.rerun()

# Task Dashboard UI
def task_dashboard():
    st.title("📊 Task Management Dashboard")

    # Display user info
    st.sidebar.success(f"Logged in as: **{st.session_state.user_name}**")

    # Get statistics
    stats = get_task_statistics(st.session_state.username)

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks", stats.get('total_tasks', 0))
    with col2:
        st.metric("Pending", stats.get('pending', 0))
    with col3:
        st.metric("In Progress", stats.get('in_progress', 0))
    with col4:
        st.metric("Completed", stats.get('completed', 0))

    st.divider()

    # Filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📋 My Tasks")
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Pending", "In Progress", "Done"],
            key="status_filter"
        )

    # Fetch tasks
    tasks_df = get_tasks(
        assigned_to=st.session_state.username,
        status=status_filter if status_filter != "All" else None
    )

    if tasks_df.empty:
        st.info("No tasks found. Add a new task below!")
    else:
        # Display tasks with better formatting
        display_df = tasks_df[['id', 'task_name', 'priority', 'due_date', 'status', 'created_at']].copy()
        display_df.columns = ['ID', 'Task', 'Priority', 'Due Date', 'Status', 'Created']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # Add new task
    st.subheader("➕ Add New Task")
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([3, 1, 2])

        with col1:
            task_name = st.text_input("Task Name", placeholder="Enter task description...")
        with col2:
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        with col3:
            due_date = st.date_input("Due Date")

        add_task_btn = st.form_submit_button("Add Task", use_container_width=True)

        if add_task_btn:
            if task_name.strip():
                if add_task(task_name, priority, str(due_date), st.session_state.username):
                    st.success("✅ Task added successfully!")
                    st.rerun()
            else:
                st.error("Task name cannot be empty!")

    # Sidebar - Update Tasks
    st.sidebar.header("🔄 Update Task")
    if not tasks_df.empty:
        task_id = st.sidebar.selectbox(
            "Select Task ID",
            tasks_df["id"].tolist(),
            format_func=lambda x: f"#{x} - {tasks_df[tasks_df['id']==x]['task_name'].values[0][:30]}"
        )
        new_status = st.sidebar.selectbox("New Status", ["Pending", "In Progress", "Done"])

        if st.sidebar.button("Update Status", use_container_width=True):
            if update_task_status(task_id, new_status):
                st.sidebar.success("✅ Status updated!")
                st.rerun()

    # Sidebar - Delete Tasks
    st.sidebar.header("🗑️ Delete Task")
    if not tasks_df.empty:
        delete_task_id = st.sidebar.selectbox(
            "Select Task to Delete",
            tasks_df["id"].tolist(),
            format_func=lambda x: f"#{x} - {tasks_df[tasks_df['id']==x]['task_name'].values[0][:30]}",
            key="delete_select"
        )

        if st.sidebar.button("Delete Task", use_container_width=True, type="primary"):
            if delete_task(delete_task_id):
                st.sidebar.warning("🗑️ Task deleted!")
                st.rerun()

# Main function
def main():
    # Initialize database
    init_database()

    # Configure page
    st.set_page_config(
        page_title="Project Management",
        page_icon="📊",
        layout="wide"
    )

    # Show login or dashboard
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        login()
    else:
        task_dashboard()

if __name__ == "__main__":
    main()
