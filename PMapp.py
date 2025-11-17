import streamlit as st
import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import hashlib

# Check if secrets are configured
def check_secrets_configured():
    """Check if Google Sheets secrets are properly configured"""
    try:
        _ = st.secrets["google"]["credentials"]
        return True
    except (KeyError, FileNotFoundError):
        return False

# Authenticate with Google Sheets using Streamlit Secrets - CACHED
@st.cache_resource
def authenticate_gsheets():
    """Cache the authenticated client to avoid repeated authentication"""
    try:
        creds_json = json.loads(st.secrets["google"]["credentials"])
        creds = Credentials.from_service_account_info(
            creds_json,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

# Fetch user data from Google Sheets - CACHED
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_users():
    """Fetch and cache user data"""
    try:
        client = authenticate_gsheets()
        if client is None:
            return pd.DataFrame()
        sheet = client.open("Project Management").worksheet("Users")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return pd.DataFrame()

# Hash password for comparison
def hash_password(password):
    """Simple hash function - use bcrypt in production"""
    return hashlib.sha256(password.encode()).hexdigest()

# Login System
def login():
    st.title("Smart Project Management App")

    # Cache users data in session state after first fetch
    if "users_df" not in st.session_state:
        st.session_state.users_df = get_users()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")

        if login_btn:
            users_df = st.session_state.users_df
            # Note: In production, compare hashed passwords
            # For now, keeping plain text comparison for compatibility
            user = users_df[(users_df["Username"] == username) & (users_df["Password"] == password)]
            if not user.empty:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_name = user.iloc[0]['Name']
                st.success(f"Welcome, {st.session_state.user_name}!")
                st.rerun()  # Updated from deprecated experimental_rerun
            else:
                st.error("Invalid credentials")
    else:
        st.sidebar.button("Logout", on_click=lambda: st.session_state.update(logged_in=False))

# Fetch tasks from Google Sheets - CACHED
@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_tasks():
    """Fetch and cache tasks data"""
    try:
        client = authenticate_gsheets()
        if client is None:
            return pd.DataFrame()
        sheet = client.open("Project Management").worksheet("Tasks")
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching tasks: {e}")
        return pd.DataFrame()

# Add a new task - OPTIMIZED
def add_task(task_name, priority, due_date, assigned_to):
    """Add task without fetching all tasks first"""
    try:
        client = authenticate_gsheets()
        if client is None:
            return False
        sheet = client.open("Project Management").worksheet("Tasks")

        # Get row count for ID without fetching all data
        row_count = len(sheet.col_values(1))
        new_task_id = row_count  # Row count includes header

        sheet.append_row([new_task_id, task_name, priority, due_date, "Pending", assigned_to])

        # Clear cache to refresh data
        get_tasks.clear()
        return True
    except Exception as e:
        st.error(f"Error adding task: {e}")
        return False

# Update task status - OPTIMIZED
def update_task_status(task_id, status):
    """Update task using cell search instead of fetching all records"""
    try:
        client = authenticate_gsheets()
        if client is None:
            return False
        sheet = client.open("Project Management").worksheet("Tasks")

        # Find the cell with the task ID
        cell = sheet.find(str(task_id))
        if cell:
            # Update status column (column 5)
            sheet.update_cell(cell.row, 5, status)

            # Clear cache to refresh data
            get_tasks.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Error updating task: {e}")
        return False

# Delete a task - OPTIMIZED
def delete_task(task_id):
    """Delete task using cell search instead of fetching all records"""
    try:
        client = authenticate_gsheets()
        if client is None:
            return False
        sheet = client.open("Project Management").worksheet("Tasks")

        # Find the cell with the task ID
        cell = sheet.find(str(task_id))
        if cell:
            sheet.delete_rows(cell.row)

            # Clear cache to refresh data
            get_tasks.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting task: {e}")
        return False

# Task Dashboard UI
def task_dashboard():
    st.title("\ud83d\udccc Task Management Dashboard")
    
    tasks_df = get_tasks()
    if tasks_df.empty:
        st.warning("No tasks found.")
    else:
        st.dataframe(tasks_df)

    with st.form("add_task_form"):
        task_name = st.text_input("Task Name")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        due_date = st.date_input("Due Date")
        add_task_btn = st.form_submit_button("Add Task")

        if add_task_btn:
            if task_name:  # Validation
                if add_task(task_name, priority, str(due_date), st.session_state.username):
                    st.success("Task added successfully!")
                    st.rerun()  # Updated from deprecated experimental_rerun
            else:
                st.error("Task name is required!")

    st.sidebar.header("Update Tasks")
    if not tasks_df.empty:
        task_id = st.sidebar.selectbox("Select Task ID", tasks_df["Task ID"])
        new_status = st.sidebar.selectbox("Update Status", ["Pending", "In Progress", "Done"])
        update_task_btn = st.sidebar.button("Update Status")

        if update_task_btn:
            if update_task_status(task_id, new_status):
                st.success("Task updated successfully!")
                st.rerun()  # Updated from deprecated experimental_rerun

    st.sidebar.header("Delete Tasks")
    if not tasks_df.empty:
        delete_task_id = st.sidebar.selectbox("Select Task to Delete", tasks_df["Task ID"], key="delete_select")
        delete_task_btn = st.sidebar.button("Delete Task")

        if delete_task_btn:
            if delete_task(delete_task_id):
                st.warning("Task deleted!")
                st.rerun()  # Updated from deprecated experimental_rerun

# Display setup instructions when secrets are missing
def show_setup_instructions():
    st.title("⚙️ Setup Required")
    st.error("Google Sheets credentials not configured!")

    st.markdown("""
    ## Quick Setup Options

    ### Option 1: Use SQLite Version (Recommended) ⭐
    The SQLite version requires **no configuration** and is **100x faster**!

    ```bash
    streamlit run PMapp_sqlite.py
    ```

    ### Option 2: Configure Google Sheets

    #### For Local Development:
    1. Create `.streamlit/secrets.toml` in your project directory
    2. Add your Google service account credentials:

    ```toml
    [google]
    credentials = '''
    {
      "type": "service_account",
      "project_id": "your-project-id",
      "private_key_id": "...",
      "private_key": "...",
      "client_email": "...",
      "client_id": "...",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "..."
    }
    '''
    ```

    #### For Streamlit Cloud:
    1. Go to your app dashboard
    2. Click on "⚙️ Settings"
    3. Click on "Secrets" in the left menu
    4. Paste the same TOML content as above
    5. Click "Save"

    #### How to Get Google Service Account Credentials:
    1. Go to [Google Cloud Console](https://console.cloud.google.com/)
    2. Create a new project or select existing one
    3. Enable Google Sheets API and Google Drive API
    4. Create a Service Account (IAM & Admin → Service Accounts)
    5. Create and download a JSON key
    6. Share your Google Sheet with the service account email

    ---

    ## 📚 More Information
    - See [OPTIMIZATION_GUIDE.md](https://github.com/kwisener01/projectmanagement/blob/main/OPTIMIZATION_GUIDE.md) for details
    - SQLite version is faster and easier to set up!
    """)

    st.info("💡 **Tip:** The SQLite version (PMapp_sqlite.py) works immediately without any setup!")

# Main function
def main():
    # Configure page
    st.set_page_config(
        page_title="Project Management",
        page_icon="📊",
        layout="wide"
    )

    # Check if secrets are configured
    if not check_secrets_configured():
        show_setup_instructions()
        return

    # Normal app flow
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        login()
    else:
        task_dashboard()

if __name__ == "__main__":
    main()
