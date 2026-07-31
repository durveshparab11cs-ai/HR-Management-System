# Firebase FCM - Quick Reference Card

## 🚀 Quick Setup (5 Minutes)

### 1. Create Firebase Project
```
1. Go to https://console.firebase.google.com/
2. Click "Add project" → Enter name → Create
```

### 2. Register Web App
```
1. Click Web icon (</>) 
2. Enter nickname → Register app
3. Copy firebaseConfig values
```

### 3. Get VAPID Key
```
1. Cloud Messaging → Web Push certificates
2. Click "Generate key pair"
3. Copy the key (starts with B...)
```

### 4. Download Service Account Key
```
1. Project Settings → Service accounts
2. Generate new private key
3. Download JSON file
```

### 5. Add to .env
```env
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=project-id.firebaseapp.com
FIREBASE_PROJECT_ID=project-id
FIREBASE_STORAGE_BUCKET=project-id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abc123
FIREBASE_VAPID_KEY=BC...
FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccount.json
```

### 6. Install & Migrate
```bash
pip install firebase-admin
flask db migrate -m "Add FCM support"
flask db upgrade
```

---

## 📊 Notification Modules Coverage

| Module | Trigger | Status |
|--------|---------|--------|
| **Attendance** | Check-in success | ✅ |
| | Check-in late | ✅ |
| | Check-out success | ✅ |
| | Check-out early | ✅ |
| **Leave** | Request submitted → Manager | ✅ |
| | Request approved → Employee | ✅ |
| | Request rejected → Employee | ✅ |
| | Half-day approved/rejected | ✅ |
| | Early leave approved/rejected | ✅ |
| **Shift Change** | Request submitted → Manager | ✅ |
| | Request approved → Employee | ✅ |
| | Request rejected → Employee | ✅ |
| | Request returned → Employee | ✅ |
| | Request escalated → Next approver | ✅ |
| | Shift assigned → Employee | ✅ |

---

## 🔧 API Endpoints

### Public Endpoints
```
GET  /api/notifications/firebase-config     # Get Firebase config
POST /api/notifications/register-token      # Register FCM token
```

### Protected Endpoints (Require Login)
```
GET  /api/notifications/unread-count        # Get unread count
GET  /api/notifications/recent?limit=10     # Get recent notifications
POST /api/notifications/<id>/read           # Mark as read
POST /api/notifications/<id>/clicked        # Mark as clicked
POST /api/notifications/<id>/delete         # Delete notification
POST /api/notifications/mark-all-read       # Mark all as read
POST /api/notifications/deactivate-token    # Deactivate FCM token
POST /api/notifications/test-push           # Test push notification
```

---

## 🧪 Testing Commands

### Test via Flask Shell
```python
flask shell

# Create test notification
from app.blueprints.notifications.service import NotificationService
svc = NotificationService()

# Send to specific employee
svc.send_to_employee(
    employee_code="E-2510016",
    title="Test Notification",
    message="This is a test",
    module="system"
)

# Send to reporting manager
svc.send_to_reporting_manager(
    manager_name="Manager Name",
    employee_name="Employee Name",
    title="Test Request",
    message="Test message",
    module="leave"
)
```

### Test via API
```bash
curl -X POST http://localhost:5000/api/notifications/test-push \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION" \
  -d '{"title":"Test","message":"Testing FCM"}'
```

---

## 📱 User Flow

### First Login
```
1. User logs in
2. Modal appears: "Enable Notifications"
3. User clicks "Enable" → Browser permission prompt
4. Permission granted → FCM token registered
5. Token stored in database (fcm_token table)
```

### Receiving Notifications

**When app is OPEN:**
- Toast notification appears in top-right
- Bell icon badge updates
- Notification added to dropdown

**When app is CLOSED:**
- Browser push notification appears
- Click → Opens HRMS and navigates to relevant page

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Firebase credentials not found" | Check FIREBASE_CREDENTIALS_PATH in .env |
| "FCM token registration failed" | Verify VAPID key is correct |
| "Notifications not appearing" | Check browser notification permissions |
| "Service worker not registering" | Verify firebase-messaging-sw.js is accessible |
| "HTTPS required error" | Use ngrok for local testing or Render URL |

### Check FCM Tokens in Database
```sql
SELECT * FROM fcm_token WHERE is_active = TRUE;
```

### Check Recent Notifications
```sql
SELECT * FROM notification 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## 📂 Key Files Modified

```
app/
├── models/
│   └── notification.py              ✅ Enhanced with FCM support
├── blueprints/
│   ├── notifications/
│   │   ├── service.py               ✅ FCM methods added
│   │   └── routes.py                ✅ API endpoints added
│   ├── attendance/routes.py         ✅ Check-in/out notifications
│   ├── leave/service.py             ✅ Leave approval notifications
│   ├── shift_change/service.py      ✅ Shift change notifications
│   ├── admin/shift_assignment.py    ✅ Admin shift assignment
│   └── authentication/routes.py     ✅ First-login detection
├── static/
│   ├── firebase-messaging-sw.js     ✅ NEW - Service worker
│   ├── manifest.json                ✅ NEW - PWA manifest
│   └── js/
│       ├── firebase-init.js         ✅ NEW - FCM initialization
│       └── notifications.js         ✅ NEW - Bell functionality
└── templates/
    ├── layouts/base.html            ✅ Firebase scripts added
    └── shared/navbar.html           ✅ Notification bell added
```

---

## 🎯 Notification Features

✅ In-app notifications with bell icon
✅ Real-time badge count updates
✅ Auto-refresh every 30 seconds
✅ Browser push notifications (offline users)
✅ Click-to-navigate functionality
✅ Module-specific icons and colors
✅ Mark as read/clicked tracking
✅ Delete individual notifications
✅ Mark all as read
✅ FCM token management
✅ Multi-device support
✅ Permission prompt on first login
✅ Toast notifications for foreground messages

---

## 💡 Best Practices

1. **Security**
   - Never commit firebase-credentials.json
   - Add to .gitignore
   - Use Render Secret Files for production

2. **Testing**
   - Test on HTTPS (required for push)
   - Test with browser closed (background push)
   - Test on multiple browsers

3. **Monitoring**
   - Check Firebase Console for delivery rates
   - Monitor database for token counts
   - Review notification click-through rates

4. **Maintenance**
   - Rotate service account keys every 90 days
   - Clean up inactive FCM tokens periodically
   - Archive old notifications

---

## 📞 Support

**For Firebase Issues:**
- Firebase Console → Project → Support
- Firebase Documentation: https://firebase.google.com/docs/cloud-messaging

**For App Issues:**
- Check Flask logs: `./logs/app.log`
- Check browser console (F12)
- Check network tab for API errors

---

## ✅ Launch Checklist

Before going live:

- [ ] Firebase project created and configured
- [ ] All environment variables set in Render
- [ ] Service account key uploaded to Render
- [ ] Database migration completed
- [ ] Test notification sent successfully
- [ ] Browser push notification received
- [ ] Notification bell working
- [ ] Multiple browsers tested
- [ ] Mobile browser tested
- [ ] HTTPS enabled on production
- [ ] Credentials not in Git repository
- [ ] Firebase Console monitoring enabled

---

**Status:** ✅ 100% Complete - Ready for Firebase Setup!
