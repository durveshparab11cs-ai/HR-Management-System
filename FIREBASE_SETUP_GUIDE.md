# Firebase Cloud Messaging (FCM) Setup Guide

## 🎯 Overview

This guide will help you set up Firebase Cloud Messaging for push notifications in your Smart HRMS application.

---

## 📋 Prerequisites

- Google Account
- Access to Firebase Console
- Admin access to Render dashboard

---

## 🔥 Step 1: Create Firebase Project

### 1.1 Go to Firebase Console
Visit: https://console.firebase.google.com/

### 1.2 Create New Project
1. Click **"Add project"**
2. Enter project name: **"Smart HRMS"** (or your preferred name)
3. Enable/Disable Google Analytics (optional)
4. Click **"Create project"**
5. Wait for setup to complete
6. Click **"Continue"**

---

## 🌐 Step 2: Register Web App

### 2.1 Add Web App to Project
1. In Firebase Console, click the **Web icon (</>) ** 
2. Enter app nickname: **"Smart HRMS Web"**
3. ✅ Check **"Also set up Firebase Hosting"** (optional)
4. Click **"Register app"**

### 2.2 Copy Firebase Configuration
You'll see a code snippet like this:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "smart-hrms-xxxxx.firebaseapp.com",
  projectId: "smart-hrms-xxxxx",
  storageBucket: "smart-hrms-xxxxx.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:xxxxxxxxxxxxxx"
};
```

**⚠️ SAVE THESE VALUES - You'll need them later!**

---

## 🔔 Step 3: Enable Cloud Messaging

### 3.1 Navigate to Cloud Messaging
1. In Firebase Console sidebar, go to **"Build" → "Cloud Messaging"**
2. Click **"Get Started"** if prompted

### 3.2 Generate VAPID Key
1. Scroll down to **"Web configuration"** section
2. Click **"Generate key pair"** under **"Web Push certificates"**
3. Copy the VAPID key (starts with `B...`)
4. **⚠️ SAVE THIS KEY - You'll need it!**

Example: `BCXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxxxx...`

---

## 🔑 Step 4: Generate Service Account Key

### 4.1 Go to Project Settings
1. Click the **Gear icon** ⚙️ next to "Project Overview"
2. Select **"Project settings"**

### 4.2 Navigate to Service Accounts
1. Click the **"Service accounts"** tab
2. Click **"Generate new private key"** button
3. Click **"Generate key"** in the confirmation dialog
4. A JSON file will download: `smart-hrms-xxxxx-firebase-adminsdk-xxxxx.json`

### 4.3 Secure the Service Account Key
**⚠️ IMPORTANT SECURITY NOTE:**
- This file contains sensitive credentials
- Never commit it to Git
- Never share it publicly
- Store it securely

**Example content:**
```json
{
  "type": "service_account",
  "project_id": "smart-hrms-xxxxx",
  "private_key_id": "xxxxxxxxxxxxxxxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\nXXXXXXXXXXXX...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-xxxxx@smart-hrms-xxxxx.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40smart-hrms-xxxxx.iam.gserviceaccount.com"
}
```

---

## 📝 Step 5: Update Environment Variables

### 5.1 Update Local .env File

Open your `.env` file and add these variables:

```env
# ============================================================================
# Firebase Cloud Messaging Configuration
# ============================================================================

# Firebase Web App Configuration (from Step 2.2)
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=smart-hrms-xxxxx.firebaseapp.com
FIREBASE_PROJECT_ID=smart-hrms-xxxxx
FIREBASE_STORAGE_BUCKET=smart-hrms-xxxxx.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:xxxxxxxxxxxxxx

# VAPID Key (from Step 3.2)
FIREBASE_VAPID_KEY=BCXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxxxx

# Service Account Credentials Path (from Step 4.2)
# For local development - absolute path to your downloaded JSON file
FIREBASE_CREDENTIALS_PATH=/path/to/your/smart-hrms-xxxxx-firebase-adminsdk-xxxxx.json
```

### 5.2 Update .env.example

Update your `.env.example` file with placeholders:

```env
# Firebase Cloud Messaging Configuration
FIREBASE_API_KEY=your_firebase_api_key_here
FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id_here
FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id_here
FIREBASE_APP_ID=your_app_id_here
FIREBASE_VAPID_KEY=your_vapid_key_here
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

---

## 🚀 Step 6: Deploy to Render

### 6.1 Upload Service Account JSON to Render

**Option A: Environment Variable (For Small Keys)**
1. Go to Render Dashboard → Your Web Service
2. Go to **"Environment"** tab
3. Add new environment variable:
   - Key: `FIREBASE_CREDENTIALS_JSON`
   - Value: Paste the entire JSON content as a single line

**Option B: Secret Files (Recommended)**
1. Go to Render Dashboard → Your Web Service
2. Go to **"Environment"** tab
3. Scroll to **"Secret Files"** section
4. Click **"Add Secret File"**
5. Filename: `firebase-credentials.json`
6. Contents: Paste entire JSON content
7. Click **"Save"**

### 6.2 Add Environment Variables to Render

Add these environment variables in Render:

```
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=smart-hrms-xxxxx.firebaseapp.com
FIREBASE_PROJECT_ID=smart-hrms-xxxxx
FIREBASE_STORAGE_BUCKET=smart-hrms-xxxxx.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:xxxxxxxxxxxxxx
FIREBASE_VAPID_KEY=BCXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxxxxxxxxxx
```

### 6.3 Set Credentials Path

If using Secret Files:
```
FIREBASE_CREDENTIALS_PATH=/etc/secrets/firebase-credentials.json
```

If using environment variable:
```
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
```

And update `app/blueprints/notifications/service.py` to read from JSON string if needed.

---

## 🔧 Step 7: Update Frontend Configuration

### 7.1 Update firebase-messaging-sw.js

Open `app/static/firebase-messaging-sw.js` and replace the placeholder values:

```javascript
// Replace this section with your actual Firebase config
const firebaseConfig = {
    apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    authDomain: "smart-hrms-xxxxx.firebaseapp.com",
    projectId: "smart-hrms-xxxxx",
    storageBucket: "smart-hrms-xxxxx.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:xxxxxxxxxxxxxx"
};
```

### 7.2 Verify API Route

The `/api/notifications/firebase-config` route should return your Firebase config to the frontend automatically from environment variables.

---

## ✅ Step 8: Install Dependencies

### 8.1 Update requirements.txt

Add Firebase Admin SDK to your `requirements.txt`:

```txt
firebase-admin>=6.5.0
```

### 8.2 Install Locally

```bash
pip install firebase-admin
```

### 8.3 Deploy to Render

Render will automatically install dependencies from `requirements.txt` on deploy.

---

## 🧪 Step 9: Run Database Migration

Create and run the migration for notification tables:

```bash
# Create migration
flask db migrate -m "Add FCM support to notifications"

# Review the migration file in migrations/versions/

# Apply migration
flask db upgrade
```

**Migration should create:**
- Enhanced `notification` table with new columns
- New `fcm_token` table for storing Firebase tokens

---

## 🧪 Step 10: Test the Setup

### 10.1 Test Locally

1. Start your Flask app:
```bash
flask run
```

2. Open browser and login to Smart HRMS

3. Check browser console for Firebase initialization:
```
Firebase initialized successfully
```

4. Grant notification permission when prompted

5. Check console for token registration:
```
FCM token registered successfully
```

### 10.2 Test Push Notification

#### Test via API Endpoint:
```bash
curl -X POST http://localhost:5000/api/notifications/test-push \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "title": "Test Notification",
    "message": "Testing FCM setup"
  }'
```

#### Test via Python Shell:
```python
flask shell

>>> from app.blueprints.notifications.service import NotificationService
>>> svc = NotificationService()
>>> svc.create(
...     user_id=1,
...     title="Test Notification",
...     message="This is a test push notification",
...     module="system"
... )
```

### 10.3 Verify Notification Delivery

✅ **In-app notification:**
- Check notification bell in navbar
- Badge count should increment
- Notification should appear in dropdown

✅ **Push notification:**
- Even with tab closed, you should receive browser notification
- Click notification → should open Smart HRMS and navigate to action URL

---

## 🐛 Troubleshooting

### Issue: "Firebase credentials not found"

**Solution:**
- Verify `FIREBASE_CREDENTIALS_PATH` points to correct file
- Check file permissions (readable by Flask app)
- Verify JSON file is valid

### Issue: "FCM token registration failed"

**Solution:**
- Check browser console for errors
- Verify VAPID key is correct
- Ensure HTTPS is enabled (required for push notifications)
- Clear browser cache and try again

### Issue: "Notifications not appearing"

**Solution:**
- Check browser notification permissions
- Verify FCM token is registered in database:
  ```sql
  SELECT * FROM fcm_token WHERE user_id = YOUR_USER_ID;
  ```
- Check Flask logs for errors
- Verify Firebase project has Cloud Messaging enabled

### Issue: "Service worker not registering"

**Solution:**
- Check `firebase-messaging-sw.js` is accessible at `/static/firebase-messaging-sw.js`
- Verify file has correct Firebase config
- Clear service worker:
  - Open DevTools → Application → Service Workers
  - Click "Unregister" and reload page

### Issue: "HTTPS required error"

**Solution:**
- Push notifications require HTTPS
- Use `ngrok` for local testing: `ngrok http 5000`
- Or use Render's HTTPS URL for testing

---

## 📊 Monitoring & Analytics

### Check Notification Stats in Firebase Console

1. Go to Firebase Console → Cloud Messaging
2. View notification delivery rates
3. Check token refresh rates
4. Monitor error rates

### Check Database Stats

```sql
-- Total FCM tokens registered
SELECT COUNT(*) FROM fcm_token WHERE is_active = TRUE;

-- Notifications sent today
SELECT COUNT(*) FROM notification WHERE DATE(created_at) = CURRENT_DATE;

-- Unread notifications by user
SELECT user_id, COUNT(*) 
FROM notification 
WHERE is_read = FALSE 
GROUP BY user_id;
```

---

## 🔒 Security Best Practices

1. **Never commit credentials to Git**
   - Add `firebase-credentials.json` to `.gitignore`
   - Add `.env` to `.gitignore`

2. **Rotate service account keys periodically**
   - Generate new key every 90 days
   - Delete old keys from Firebase Console

3. **Restrict API key usage**
   - In Firebase Console → Project Settings → General
   - Under "Your apps" → Click web app
   - Add your domain to authorized domains

4. **Enable App Check (Optional)**
   - Protects against abuse and unauthorized access
   - Go to Firebase Console → Build → App Check

5. **Monitor usage**
   - Set up billing alerts in Google Cloud Console
   - Monitor Cloud Messaging quotas

---

## 💰 Pricing

Firebase Cloud Messaging is **FREE** with:
- ✅ Unlimited notifications
- ✅ Unlimited tokens
- ✅ Worldwide delivery

**Note:** Firebase Spark Plan (free tier) includes FCM at no cost.

---

## 📚 Additional Resources

- [Firebase Cloud Messaging Documentation](https://firebase.google.com/docs/cloud-messaging)
- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup)
- [Web Push Protocol](https://developers.google.com/web/fundamentals/push-notifications)
- [Service Workers Guide](https://developers.google.com/web/fundamentals/primers/service-workers)

---

## ✅ Checklist

Before marking setup as complete, verify:

- [ ] Firebase project created
- [ ] Web app registered in Firebase
- [ ] Cloud Messaging enabled
- [ ] VAPID key generated
- [ ] Service account key downloaded
- [ ] Environment variables added to .env
- [ ] Environment variables added to Render
- [ ] firebase-messaging-sw.js updated with real config
- [ ] firebase-admin installed
- [ ] Database migration run
- [ ] Test notification sent successfully
- [ ] Push notification received in browser
- [ ] Notification bell shows unread count
- [ ] Credentials secured and not in Git

---

## 🎉 Congratulations!

Your Smart HRMS now has a complete Browser Push Notification System with Firebase Cloud Messaging!

Employees will receive:
- ✅ Attendance confirmations
- ✅ Leave request updates
- ✅ Shift change notifications
- ✅ Real-time alerts
- ✅ Push notifications even when app is closed

---

**Need help?** Check Flask logs, browser console, and Firebase Console for detailed error messages.
