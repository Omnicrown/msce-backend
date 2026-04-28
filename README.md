# msce-backend
# ✦ MSCE Past Papers App — Setup Guide

A complete system for MSCE students in Malawi to access past papers, 
marking schemes, and study notes — with view-only access (no downloading).

---

## 📁 Project Structure

```
msce_app/
├── backend/
│   └── app.py            ← Flask server (handles files, API, auth)
├── admin/
│   └── index.html        ← Admin web panel (upload/manage papers)
└── android_app/
    ├── main.py           ← Kivy Android student app
    └── buildozer.spec    ← APK build config
```

---

## 🖥️ 1. Setup the Backend Server

### Install dependencies
```bash
pip install flask flask-cors werkzeug
```

### Run the server
```bash
cd backend
python app.py
```
Server starts at: `http://localhost:5000`

### Change the admin password
Open `backend/app.py` and edit line:
```python
ADMIN_PASS = generate_password_hash('msce@admin2025')  # ← your password
```

---

## 🌐 2. Use the Admin Panel

1. Open `admin/index.html` in any browser
2. Login with:
   - Username: `admin`
   - Password: `msce@admin2025` (or what you set above)
3. Upload PDFs — choose subject, year, type (Past Paper / Marking Scheme / Study Note)
4. Manage and delete papers from the "Manage Papers" tab

---

## 📱 3. Build the Android App

### Step 1 — Set your server IP
Open `android_app/main.py` and update:
```python
SERVER = "http://YOUR_SERVER_IP:5000"
# Example: SERVER = "http://192.168.1.50:5000"
# For production: SERVER = "https://yourwebsite.com"
```

### Step 2 — Install Buildozer (Linux/macOS recommended)
```bash
pip install buildozer
```

### Step 3 — Build the APK
```bash
cd android_app
buildozer android debug         # debug APK (~15 min first run)
buildozer android release       # release APK for Play Store
```

APK output: `android_app/bin/mscepastpapers-1.0.0-debug.apk`

---

## 🔒 Security — View Only, No Download

The server streams PDFs with:
```
Content-Disposition: inline      ← shows in viewer, not saved
Cache-Control: no-store          ← not cached
```
Students can VIEW papers but cannot download them.

---

## ☁️ Deploy to Production (Optional)

To make the app available over the internet for all students in Malawi:

1. Get a cheap VPS (e.g. DigitalOcean, Hetzner ~$5/month)
2. Install Flask + Nginx on the server
3. Update `SERVER` in `main.py` to your domain/IP
4. Rebuild the APK with the new server URL

---

## 📚 Default Subjects Included
Mathematics, English, Biology, Chemistry, Physics, History,
Geography, Chichewa, Agriculture, Computer Studies, Business Studies, French

More subjects can be added from the Admin Panel → Subjects tab.
