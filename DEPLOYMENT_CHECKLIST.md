# 🚀 Firebase Cloud Messaging - Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Code Review
- [ ] All 17 files modified are reviewed
- [ ] No syntax errors in Python files
- [ ] No console errors in JavaScript files
- [ ] All imports are correct
- [ ] No hardcoded credentials in code

### 2. Firebase Setup
- [ ] Firebase project created
- [ ] Web app registered in Firebase
- [ ] Cloud Messaging enabled
- [ ] VAPID key generated and saved
- [ ] Service account key downloaded (JSON file)
- [ ] Firebase credentials JSON file secured (not in Git)

### 3. Environment Configuration

#### Local (.env)
- [ ] `FIREBASE_API_KEY` added
- [ ] `FIREBASE_AUTH_DOMAIN` added
- [ ] `FIREBASE_PROJECT_ID` added
- [ ] `FIREBASE_STORAGE_BUCKET` added
- [ ] `FIREBASE_MESSAGING_SENDER_ID` added
- [ ] `FIREBASE_APP_ID` added
- [ ] `FIREBASE_VAPID_KEY` added
- [ ] `FIREBASE_CREDENTIALS_PATH` points to JSON file

#### Production (Render)
- [ ] All Firebase environment variables added to Render
- [ ] Service account JSON uploaded as Secret File
- [ ] `FIREBASE_CREDENTIALS_PATH=/etc/secrets/firebase-credentials.json`

### 4. Frontend Configuration
- [ ] `firebase-messaging-sw.js` updated with real Firebase config
- [ ] Verify file is accessible at `/static/firebase-messaging-sw.js`
- [ ] `manifest.json` has correct app name and URLs

### 5. Dependencies
- [ ] `firebase-admin>=6.5.0` added to requirements/base.txt
- [ ] All dependencies installed locally: `pip install -r requirements.txt`
- [ ] No dependency conflicts

### 6. Database
- [ ] Migration created: `flask db migrate -m "Add FCM support"`
- [ ] Migration file reviewed
- [ ] Migration applied locally: `flask db upgrade`
- [ ] Verify `notification` table has new columns
- [ ] Verify `fcm_token` table created
- [ ] Check table structure: `\d notification` and `\d fcm_token` (PostgreSQL)

### 7. Security
- [ ] `.gitignore` includes `firebase-credentials.json`
- [ ] `.gitignore` includes `.env`
- [ ] No credentials in Git history
- [ ] CSRF protection enabled
- [ ] HTML escaping in place
- [ ] SQL injection prevention (using ORM)

---

## 🧪 Local Testing Checklist

### Database Tests
```bash
flask shell
```

```python
# Test 1: Check models are loaded
>>> from app.models.notification import Notification, FCMToken
>>> print(Notification.query.count())
>>> print(FCMToken.query.count())

# Test 2: Create test notification
>>> from app.blueprints.notifications.service import NotificationService
>>> svc = NotificationService()
>>> notif = svc.create(
...     user_id=1,
...     title="Test Notification",
...     message="This is a test",
...     module="system"
... )
>>> print(f"Notification ID: {notif.id}")

# Test 3: Check notification in database
>>> from app.models.notification import Notification
>>> notif = Notification.query.first()
>>> print(f"Title: {notif.title}")
>>> print(f"Message: {notif.message}")
>>> print(f"Module: {notif.module}")
```

### API Tests
```bash
# Start Flask app
flask run

# In another terminal:
# Test 1: Get Firebase config
curl http://localhost:5000/api/notifications/firebase-config

# Test 2: Get unread count (requires login)
curl http://localhost:5000/api/notifications/unread-count \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Test 3: Get recent notifications (requires login)
curl http://localhost:5000/api/notifications/recent?limit=5 \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### Frontend Tests
- [ ] Open browser to `http://localhost:5000`
- [ ] Login to Smart HRMS
- [ ] Check browser console for errors
- [ ] Verify Firebase initialized: Look for "Firebase initialized successfully"
- [ ] Check if permission modal appears (first login)
- [ ] Grant notification permission
- [ ] Verify FCM token registered: Look for "FCM token registered successfully"
- [ ] Check notification bell appears in navbar
- [ ] Click bell → Dropdown should open
- [ ] Verify no console errors

### Service Worker Tests
- [ ] Open DevTools → Application tab → Service Workers
- [ ] Verify `firebase-messaging-sw.js` is registered
- [ ] Status should be "activated and running"
- [ ] No errors in service worker console

### Notification Tests
```python
flask shell

# Test: Send notification to your user
>>> from app.blueprints.notifications.service import NotificationService
>>> svc = NotificationService()
>>> svc.send_to_employee(
...     employee_code="YOUR_EMPLOYEE_CODE",
...     title="Test Push Notification",
...     message="Testing browser push",
...     module="system"
... )
```

- [ ] In-app notification appears in bell dropdown
- [ ] Badge count increments
- [ ] Browser push notification appears (if app closed)
- [ ] Click notification → Opens Smart HRMS
- [ ] Notification marked as read/clicked

### Module Integration Tests

#### Attendance
- [ ] Mark attendance check-in
- [ ] Receive "Attendance Marked" notification
- [ ] If late, receive late warning notification
- [ ] Mark check-out
- [ ] Receive "Checkout Recorded" notification

#### Leave
- [ ] Submit leave request
- [ ] Reporting manager receives notification
- [ ] Manager approves leave
- [ ] Employee receives "Leave Approved" notification
- [ ] Test rejection with mandatory reason

#### Shift Change
- [ ] Submit shift change request
- [ ] Manager receives notification
- [ ] Admin assigns shift directly
- [ ] Employee receives "New Shift Assigned" notification

---

## 🚀 Deployment Checklist (Render)

### Pre-Deployment
- [ ] All local tests passed
- [ ] Code committed to Git
- [ ] Commit message follows convention
- [ ] `.gitignore` updated
- [ ] No credentials in repository

### Render Configuration
- [ ] Firebase environment variables added
- [ ] Service account JSON uploaded to Secret Files
- [ ] Database migration plan ready
- [ ] Backup of production database taken (if applicable)

### Deploy
```bash
# Push to Git repository
git add .
git commit -m "feat(notifications): implement FCM push notification system"
git push origin main
```

- [ ] Render auto-deploys successfully
- [ ] Build logs show no errors
- [ ] Check "firebase-admin" installed in logs

### Post-Deployment
- [ ] Run database migration on production
```bash
# Via Render shell or Flask CLI
flask db upgrade
```

- [ ] Verify tables created:
```sql
SELECT * FROM notification LIMIT 1;
SELECT * FROM fcm_token LIMIT 1;
```

- [ ] Check application logs for errors
- [ ] Verify Firebase credentials loaded
- [ ] Test notification endpoint

---

## ✅ Production Testing Checklist

### Smoke Tests
- [ ] Open production URL (HTTPS required!)
- [ ] Login works
- [ ] No JavaScript errors in console
- [ ] Firebase initializes
- [ ] Permission modal appears (first login)
- [ ] FCM token registers
- [ ] Notification bell visible

### Functional Tests
- [ ] Create test notification via API
- [ ] In-app notification appears
- [ ] Browser push notification received
- [ ] Click notification → Navigates correctly
- [ ] Mark as read works
- [ ] Mark all as read works
- [ ] Delete notification works

### Cross-Browser Tests
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Safari (latest) - macOS only
- [ ] Mobile Chrome
- [ ] Mobile Safari

### Real-World Scenario Tests
- [ ] Employee marks attendance → Notification received
- [ ] Employee submits leave → Manager notified
- [ ] Manager approves leave → Employee notified
- [ ] Manager rejects leave → Employee notified with reason
- [ ] Employee requests shift change → Manager notified
- [ ] Admin assigns shift → Employee notified

---

## 📊 Monitoring Checklist

### Firebase Console
- [ ] Login to Firebase Console
- [ ] Go to Cloud Messaging
- [ ] Check notification delivery stats
- [ ] Monitor error rates
- [ ] Check token refresh rates

### Database Monitoring
```sql
-- Check FCM token registration
SELECT COUNT(*) as total_tokens FROM fcm_token WHERE is_active = TRUE;

-- Check notifications sent today
SELECT COUNT(*) as today_notifications 
FROM notification 
WHERE DATE(created_at) = CURRENT_DATE;

-- Check unread notifications by module
SELECT module, COUNT(*) as unread_count 
FROM notification 
WHERE is_read = FALSE 
GROUP BY module;

-- Check notification click rate
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked,
    ROUND(100.0 * COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) / COUNT(*), 2) as click_rate
FROM notification
WHERE created_at > NOW() - INTERVAL '7 days';
```

### Application Logs
- [ ] Check Flask logs for FCM errors
- [ ] Monitor notification creation logs
- [ ] Check for token registration failures
- [ ] Review Firebase Admin SDK logs

---

## 🐛 Troubleshooting Checklist

### If Notifications Don't Appear

**Check Browser:**
- [ ] Notification permission granted? (Settings → Site settings → Notifications)
- [ ] Service worker registered? (DevTools → Application → Service Workers)
- [ ] FCM token in localStorage?
- [ ] Any console errors?

**Check Backend:**
```python
flask shell
>>> from app.models import FCMToken, Notification
>>> from app.blueprints.notifications.service import NotificationService

# Check if user has FCM token
>>> token = FCMToken.query.filter_by(user_id=YOUR_USER_ID, is_active=True).first()
>>> print(f"Token: {token.token[:20]}..." if token else "No token found")

# Check if notification was created
>>> notifs = Notification.query.filter_by(user_id=YOUR_USER_ID).all()
>>> print(f"Total notifications: {len(notifs)}")

# Test FCM sending
>>> svc = NotificationService()
>>> svc._send_fcm_notification(
...     user_id=YOUR_USER_ID,
...     notification_id=1,
...     title="Test",
...     body="Test message",
...     module="system"
... )
```

**Check Firebase:**
- [ ] Firebase credentials valid?
- [ ] Cloud Messaging enabled?
- [ ] VAPID key correct?
- [ ] Service account key not expired?

### If Push Notifications Don't Work Offline

- [ ] Service worker running? (DevTools → Application → Service Workers)
- [ ] HTTPS enabled? (Push requires HTTPS)
- [ ] Browser supports push? (Check caniuse.com)
- [ ] Notification permission granted?

### If Badge Count Not Updating

- [ ] Check `/api/notifications/unread-count` returns correct count
- [ ] Auto-refresh working? (every 30 seconds)
- [ ] No JavaScript errors blocking execution?
- [ ] Network tab shows API calls succeeding?

---

## 📋 Final Verification

### Before Marking Complete:
- [ ] All code changes deployed
- [ ] Database migration completed
- [ ] Firebase fully configured
- [ ] All tests passed
- [ ] Monitoring in place
- [ ] Documentation reviewed
- [ ] Team trained (if applicable)

### Success Criteria:
- [ ] Employees receive attendance notifications
- [ ] Managers receive leave request notifications
- [ ] Employees receive leave approval/rejection notifications
- [ ] Shift change workflow notifications working
- [ ] Push notifications work when browser closed
- [ ] Multi-device support verified
- [ ] No errors in production logs
- [ ] Firebase Console shows successful deliveries

---

## 🎉 Go-Live Checklist

- [ ] All production tests passed
- [ ] Stakeholders notified
- [ ] Documentation shared with team
- [ ] Monitoring dashboard reviewed
- [ ] Support team briefed
- [ ] Rollback plan ready (if needed)

---

## 📞 Emergency Contacts

**If something goes wrong:**

1. **Check logs immediately**
   - Flask logs: `/logs/app.log`
   - Browser console (F12)
   - Firebase Console

2. **Quick rollback (if critical)**
   ```bash
   # Revert to previous version
   git revert HEAD
   git push origin main
   ```

3. **Disable notifications temporarily**
   ```python
   # In notification service, set:
   _firebase_initialized = False
   ```

4. **Database rollback**
   ```bash
   flask db downgrade
   ```

---

## ✅ Deployment Complete!

Once all checklist items are completed:

```
╔══════════════════════════════════════════════╗
║  🎉 FCM NOTIFICATION SYSTEM DEPLOYED         ║
║                                              ║
║  ✅ Code: Deployed                          ║
║  ✅ Database: Migrated                      ║
║  ✅ Firebase: Configured                    ║
║  ✅ Testing: Passed                         ║
║  ✅ Monitoring: Active                      ║
║                                              ║
║  🚀 Status: LIVE IN PRODUCTION              ║
╚══════════════════════════════════════════════╝
```

**Congratulations! Your Smart HRMS now has live push notifications!** 🎊

---

*Checklist Version: 1.0.0*
*Last Updated: $(date)*
