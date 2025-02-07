import streamlit as st
import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# Authenticate with Google Sheets using Streamlit Secrets
def authenticate_gsheets():
    creds_json = json.loads(st.secrets["google"]["credentials"])
    creds = Credentials.from_service_account_info(
        creds_json, 
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    return client

# Fetch user data from Google Sheets
def get_users():
    client = authenticate_gsheets()
    sheet = client.open("Project Management").worksheet("Users")
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Login System
def login():
    users_df = get_users()
    st.title("Smart Project Management App")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")

        if login_btn:
            user = users_df[(users_df["Username"] == username) & (users_df["Password"] == password)]
            if not user.empty:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome, {user.iloc[0]['Name']}!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
    else:
        st.sidebar.button("Logout", on_click=lambda: st.session_state.update(logged_in=False))

# Fetch tasks from Google Sheets
def get_tasks():
    client = authenticate_gsheets()
    sheet = client.open("Project Management").worksheet("Tasks")
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Add a new task
def add_task(task_name, priority, due_date, assigned_to):
    client = authenticate_gsheets()
    sheet = client.open("Project Management").worksheet("Tasks")
    tasks_df = get_tasks()
    new_task_id = len(tasks_df) + 1  # Auto-increment Task ID
    sheet.append_row([new_task_id, task_name, priority, due_date, "Pending", assigned_to])

# Update task status
def update_task_status(task_id, status):
    client = authenticate_gsheets()
    sheet = client.open("Project Management").worksheet("Tasks")
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if row["Task ID"] == task_id:
            sheet.update_cell(i, 5, status)  # Update Status column
            break

# Delete a task
def delete_task(task_id):
    client = authenticate_gsheets()
    sheet = client.open("Project Management").worksheet("Tasks")
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if row["Task ID"] == task_id:
            sheet.delete_rows(i)
            break

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
            add_task(task_name, priority, str(due_date), st.session_state.username)
            st.success("Task added successfully!")
            st.experimental_rerun()

    st.sidebar.header("Update Tasks")
    if not tasks_df.empty:
        task_id = st.sidebar.selectbox("Select Task ID", tasks_df["Task ID"])
        new_status = st.sidebar.selectbox("Update Status", ["Pending", "In Progress", "Done"])
        update_task_btn = st.sidebar.button("Update Status")

        if update_task_btn:
            update_task_status(task_id, new_status)
            st.success("Task updated successfully!")
            st.experimental_rerun()

    st.sidebar.header("Delete Tasks")
    if not tasks_df.empty:
        delete_task_id = st.sidebar.selectbox("Select Task to Delete", tasks_df["Task ID"])
        delete_task_btn = st.sidebar.button("Delete Task")

        if delete_task_btn:
            delete_task(delete_task_id)
            st.warning("Task deleted!")
            st.experimental_rerun()

# Main function
def main():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        login()
    else:
        task_dashboard()

if __name__ == "__main__":
    main()
