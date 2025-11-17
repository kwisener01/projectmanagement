# Setup Guide

## Quick Start (No Configuration Required) ⭐

The **easiest and fastest** way to get started:

```bash
pip install streamlit pandas
streamlit run PMapp_sqlite.py
```

**Login:** `admin` / `admin123`

That's it! No configuration needed.

---

## Google Sheets Version Setup

If you want to use the Google Sheets version (PMapp.py), follow these steps:

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Note your project ID

### Step 2: Enable APIs

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable:
   - **Google Sheets API**
   - **Google Drive API**

### Step 3: Create Service Account

1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Enter a name (e.g., "streamlit-pm-app")
4. Click "Create and Continue"
5. Skip the optional steps, click "Done"

### Step 4: Generate Credentials

1. Click on your newly created service account
2. Go to the "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose **JSON** format
5. Click "Create" - a JSON file will download

### Step 5: Share Google Sheet

1. Open or create your Google Sheet named "Project Management"
2. Create two worksheets:
   - **Users** with columns: `Username`, `Password`, `Name`
   - **Tasks** with columns: `Task ID`, `Task Name`, `Priority`, `Due Date`, `Status`, `Assigned To`
3. Click "Share" button
4. Add the service account email (from the JSON file, field `client_email`)
5. Give it **Editor** access

### Step 6: Configure Secrets

#### For Local Development:

1. Create a `.streamlit` folder in your project directory:
   ```bash
   mkdir -p .streamlit
   ```

2. Create `.streamlit/secrets.toml` file:
   ```bash
   touch .streamlit/secrets.toml
   ```

3. Open the downloaded JSON key file and copy its contents

4. Edit `.streamlit/secrets.toml` and add:
   ```toml
   [google]
   credentials = '''
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key_id": "key-id-here",
     "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
     "client_email": "your-service-account@project.iam.gserviceaccount.com",
     "client_id": "123456789",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
     "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
   }
   '''
   ```

5. **Important:** Add `.streamlit/secrets.toml` to `.gitignore`:
   ```bash
   echo ".streamlit/secrets.toml" >> .gitignore
   ```

#### For Streamlit Cloud:

1. Deploy your app to Streamlit Cloud
2. Go to your app's dashboard
3. Click "⚙️ Settings" (gear icon)
4. Click "Secrets" in the left sidebar
5. Paste the same TOML content from above
6. Click "Save"
7. Your app will automatically restart with the new secrets

### Step 7: Run the App

```bash
streamlit run PMapp.py
```

---

## Troubleshooting

### Error: "Google Sheets credentials not configured"
- Make sure `.streamlit/secrets.toml` exists
- Check that the TOML syntax is correct
- Verify the JSON is properly formatted within the triple quotes

### Error: "Authentication error"
- Verify the service account JSON is complete
- Check that you've enabled Google Sheets API and Drive API
- Make sure the private key includes the full `-----BEGIN PRIVATE KEY-----` block

### Error: "Spreadsheet not found"
- Verify your Google Sheet is named exactly "Project Management"
- Check that you've shared the sheet with the service account email
- Ensure the service account has Editor access

### Error: "Worksheet not found"
- Create worksheets named "Users" and "Tasks" (case-sensitive)
- Verify the column headers match exactly

### Permission Denied
- Re-share the Google Sheet with the service account email
- Make sure you gave Editor (not Viewer) access
- Check that the APIs are enabled in your Google Cloud project

---

## Comparison: SQLite vs Google Sheets

| Feature | SQLite | Google Sheets |
|---------|--------|---------------|
| **Setup Time** | 30 seconds | 15-30 minutes |
| **Speed** | 5-10ms | 300-500ms |
| **Configuration** | None | Complex |
| **Offline** | Yes | No |
| **Collaboration** | Manual export/import | Real-time |
| **Best For** | Single user, local dev | Team collaboration |

---

## Recommendation

**For most users:** Use `PMapp_sqlite.py` - it's faster, easier, and works immediately.

**Use Google Sheets version if:**
- You need real-time collaboration
- You want to edit data directly in Google Sheets
- You're already using Google Workspace
- You need cloud-based storage

---

## Security Best Practices

### Local Development
- ✅ Never commit `.streamlit/secrets.toml` to git
- ✅ Add it to `.gitignore`
- ✅ Use environment-specific secrets

### Production
- ✅ Use Streamlit Cloud secrets management
- ✅ Rotate service account keys periodically
- ✅ Give minimum required permissions (not Owner)
- ✅ Enable 2FA on your Google account
- ✅ Monitor API usage in Google Cloud Console

---

## Next Steps

After setup:
1. Add your team members to the Users sheet
2. Start creating tasks
3. Customize priority levels and statuses
4. Read [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) for advanced features

---

## Support

If you encounter issues:
1. Check this guide first
2. Review error messages carefully
3. Verify each step was completed
4. Check [Streamlit documentation](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
5. Review [gspread documentation](https://docs.gspread.org/)

For the SQLite version, no setup is needed - it just works! 🚀
