
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
import numpy as np

# Set up Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("your-google-service-account.json", scope)
gc = gspread.authorize(credentials)

# Load Google Sheets
spreadsheet = gc.open("Daily_Check_Sheet_KPI_Report")
daily_check_sheet = spreadsheet.worksheet("Daily Check Sheet")
kpi_report_sheet = spreadsheet.worksheet("KPI Report")

# Streamlit UI
st.title("Test Line Management Dashboard")

# User Authentication
st.sidebar.subheader("User Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
role = st.sidebar.selectbox("Role", ["Assistant Manager", "Group Leader", "Team Leader", "Line Support"])

if st.sidebar.button("Login"):
    st.session_state["authenticated"] = True

if "authenticated" in st.session_state and st.session_state["authenticated"]:
    
    # Daily Check Sheet
    st.header("📋 Daily Check Sheet")
    checklist_items = [
        "Review previous shift’s production, defects, and downtime data",
        "Confirm test equipment is operational",
        "Conduct Shift Startup Meeting",
        "Assign downtime tracking responsibilities",
        "Ensure 5S area check is completed",
        "Monitor production efficiency and defect rates",
        "Review defect and downtime data mid-shift",
        "Meet with main/sub-line assistant managers",
        "Update KPI dashboard with key performance data",
        "Ensure shift handover meeting is conducted"
    ]
    
    checklist_status = {item: st.checkbox(item) for item in checklist_items}

    if st.button("Submit Daily Check"):
        data = [list(checklist_status.keys()), list(checklist_status.values())]
        daily_check_sheet.append_rows(data)

    # KPI Report Section
    st.header("📊 KPI Dashboard")
    kpi_data = kpi_report_sheet.get_all_records()
    df_kpi = pd.DataFrame(kpi_data)

    st.write("### Key Performance Indicators")
    st.dataframe(df_kpi)

    # KPI Visualization
    fig, ax = plt.subplots()
    kpis = df_kpi["Key KPI"]
    values = df_kpi["Current Value"].astype(float)
    targets = df_kpi["Target Value"].astype(float)

    ax.barh(kpis, targets, color="lightgray", label="Target")
    ax.barh(kpis, values, color="blue", label="Actual")

    plt.xlabel("Performance")
    plt.ylabel("KPI Metrics")
    plt.title("KPI Performance vs Target")
    plt.legend()
    st.pyplot(fig)

    # AI-Driven Alerts
    st.subheader("⚠️ AI-Powered Risk Alerts")
    df_kpi["Risk Level"] = np.where(df_kpi["Current Value"].astype(float) > df_kpi["Target Value"].astype(float) * 1.2, "🔴 Critical",
                                    np.where(df_kpi["Current Value"].astype(float) > df_kpi["Target Value"].astype(float) * 1.1, "🟠 Warning", "🟢 Normal"))

    st.dataframe(df_kpi[["Key KPI", "Current Value", "Target Value", "Risk Level"]])

    # Email KPI Report
    st.header("📩 Send KPI Report")
    if st.button("Send Daily KPI Report"):
        email_content = df_kpi.to_html()
        msg = MIMEText(email_content, "html")
        msg["Subject"] = "Test Line Daily KPI Report"
        msg["From"] = "your-email@example.com"
        msg["To"] = "your-email@example.com"

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("your-email@example.com", "your-email-password")
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())

        st.success("Daily KPI Report Sent!")

else:
    st.warning("Please log in to access the dashboard.")
