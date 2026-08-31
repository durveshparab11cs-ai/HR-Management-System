# Coordinator Two-Factor Authentication Implementation

## Overview

Successfully implemented a secure two-step password + OTP authentication flow for the Smart HRMS Coordinator Portal with multi-recipient email verification.

**Implementation Date:** August 24, 2026  
**Status:** ✅ Complete and Ready for Testing

---

## Architecture

### Authentication Flow

```
Step 1: Password Validation
├─ User enters: CS creative solution (fixed username)
├─ User enters: CSCS@hr2013 (fixed password)
├─ Backend validates credentials
└─ If valid:
    ├─ Generate 6-digit OTP (cryptographically secure)
    ├─ Create OTP challenge in database (bcrypt hashed)
    ├─ Send OTP to 3 authorized recipients
    ├─ Store challenge token in session
    └─ Redirect to OTP verification screen

Step 2: OTP Verification
├─ Display 6-digit OTP input with countdown timer
├─ User obtains OTP from authorized HR contacts
├─ User enters OTP
├─ Backend verifies OTP against challenge
└─ If valid:
    ├─ Mark OTP as used
    ├─ Invalidate challenge
    ├─ Create authenticated session
    └─ Grant access to Coordinator Portal

Security Features:
├─ OTP stored as bcrypt hash (never plaintext)
├─ 5-minute expiration
├─ Maximum 5 verification attempts
├─ 60-second resend cooldown
├─ Maximum 3 resend requests
├─ Challenge invalidation on limits
├─ Session-based challenge tracking
└─ No bypass possible - OTP required for authentication
```

---

## Modified Files

### 1. Database Model
**File:** `app/models/coordinator_otp.py` (NEW)

- `CoordinatorOTP` model with secure OTP hash storage
- Tracks: expiration, attempts, resends, usage, invalidation
- Helper methods: `is_valid()`, `is_expired()`, `can_resend()`, `mark_used()`, `invalidate()`

**File:** `app/models/__init__.py`
- Registered `CoordinatorOTP` model for SQLAlchemy discovery

### 2. Service Layer
**File:** `app/services/coordinator_otp_service.py` (NEW)

Key methods:
- `generate_otp()` - Secure 6-digit OTP generation using `secrets`
- `create_challenge()` - Create OTP challenge with bcrypt hashing
- `send_otp_email()` - Send professional security email to multiple recipients
- `verify_otp()` - Verify OTP with attempt tracking and rate limiting
- `resend_otp()` - Generate new OTP with cooldown enforcement
- `cleanup_expired_challenges()` - Remove old challenges
- `invalidate_challenge()` - Manually invalidate challenge

Email template features:
- Professional HTML and plaintext formats
- Purple gradient Smart HRMS branding
- Clear security warnings
- OTP expiration notice
- Instructions for coordinator contact

### 3. Authentication Routes
**File:** `app/blueprints/authentication/routes.py`

Updated coordinator authentication flow:
- **Password validation** - No longer creates session immediately
- **OTP generation** - Creates challenge and sends emails
- **Session storage** - Stores challenge token (temporary, not authenticated)
- **New route:** `/auth/coordinator/verify-otp` - OTP verification page
- **New route:** `/auth/coordinator/cancel-otp` - Cancel verification

Security measures:
- Session expires if challenge token missing
- Challenge validated before OTP verification
- Authenticated session created ONLY after successful OTP verification
- No bypass possible

### 4. User Interface
**File:** `app/templates/authentication/coordinator_otp_verify.html` (NEW)

Features:
- 6-digit OTP input with auto-focus and auto-advance
- Paste support (full 6-digit paste)
- 5-minute countdown timer (visual warning at 1 minute)
- Resend OTP button with loading state
- Cancel button returns to login
- Error and success message display
- Loading states for all actions
- Responsive design matching Smart HRMS styling
- Purple gradient theme consistency

JavaScript functionality:
- Auto-focus next input on digit entry
- Backspace navigation
- Clipboard paste handling
- Real-time countdown timer
- Form validation (6 digits required)
- Loading state management

### 5. Environment Configuration
**File:** `.env.production`

New configuration variables:
```env
# Coordinator OTP Recipients (2FA)
COORDINATOR_OTP_RECIPIENTS=executivehr00013@gmail.com,durveshparab11cs@gmail.com,assistanthrmanager22@gmail.com
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=5
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_MAX_RESENDS=3
```

Existing email configuration (must be configured):
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=Smart HRMS <noreply@smarthrms.online>
```

---

## Database Schema

### Table: `coordinator_otp_challenges`

```sql
CREATE TABLE coordinator_otp_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    otp_hash VARCHAR(255) NOT NULL,              -- Bcrypt hash of OTP
    challenge_token VARCHAR(64) UNIQUE NOT NULL, -- Session identifier
    attempt_count INTEGER DEFAULT 0,             -- Failed attempts
    max_attempts INTEGER DEFAULT 5,              -- Max allowed attempts
    is_used BOOLEAN DEFAULT FALSE,               -- OTP verified
    is_invalidated BOOLEAN DEFAULT FALSE,        -- Challenge cancelled
    created_at DATETIME NOT NULL,                -- Challenge creation
    expires_at DATETIME NOT NULL,                -- OTP expiration
    used_at DATETIME,                            -- Verification time
    invalidated_at DATETIME,                     -- Cancellation time
    last_resend_at DATETIME,                     -- Last resend time
    resend_count INTEGER DEFAULT 0,              -- Number of resends
    ip_address VARCHAR(45),                      -- Client IP
    user_agent VARCHAR(500)                      -- Client user agent
);
```

The table is created automatically when the application starts via `db.create_all()`.

---

## Security Features

### ✅ Password Security
- Fixed coordinator credentials stored server-side
- Password validated before OTP generation
- No OTP generated on incorrect password
- Password never logged or exposed

### ✅ OTP Security
- Cryptographically secure generation (`secrets.randbelow()`)
- Stored as bcrypt hash, never plaintext
- 6-digit format (1,000,000 possibilities)
- 5-minute expiration
- Single-use only (marked as used after verification)
- Invalidated on expiration or max attempts

### ✅ Rate Limiting
- **Verification attempts:** Maximum 5 failed attempts per challenge
- **Resend cooldown:** 60 seconds between resend requests
- **Resend limit:** Maximum 3 resends per challenge
- **Challenge invalidation:** Automatic on limit breach
- **Cleanup:** Expired challenges removed after 24 hours

### ✅ Session Security
- Challenge token stored in Flask session (server-side)
- Session cleared after successful verification
- Session cleared on cancellation
- No authenticated session until OTP verified
- HttpOnly, SameSite=Lax cookies

### ✅ Email Security
- SMTP credentials stored in environment variables
- Never exposed to frontend
- Professional security notification format
- Sent to 3 authorized recipients simultaneously
- Same OTP to all recipients

### ✅ Protection Against Attacks
- **Brute force:** Limited attempts + cooldown
- **Replay:** Single-use OTPs
- **Bypass:** No session without OTP verification
- **Direct access:** Coordinator portal checks authentication
- **Session hijacking:** HttpOnly cookies
- **CSRF:** CSRF tokens on all forms

---

## Configuration Requirements

### Required Email Setup

To enable email delivery, configure these environment variables in `.env.production`:

```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
```

**For Gmail:**
1. Enable 2-Factor Authentication on your Google Account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character app password in `MAIL_PASSWORD`

**Alternative SMTP Providers:**
- Update `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS` as needed
- Ensure firewall allows outbound SMTP connections

### OTP Recipients

Update if needed:
```env
COORDINATOR_OTP_RECIPIENTS=email1@example.com,email2@example.com,email3@example.com
```

**Important:** Do not expose these emails in frontend code. They remain server-side only.

---

## Testing Guide

### Test 1: Correct Password → OTP Generation
1. Go to `smarthrms.online/auth/login`
2. Click "Coordinator" tab
3. Username: CS creative solution (pre-filled, locked)
4. Password: CSCS@hr2013
5. Click "Access Coordinator Portal"
6. **Expected:** Redirect to OTP verification screen
7. **Expected:** 3 emails sent to authorized recipients
8. **Expected:** 5-minute countdown timer visible

### Test 2: Incorrect Password
1. Enter wrong password
2. Click "Access Coordinator Portal"
3. **Expected:** Error message
4. **Expected:** No OTP generated
5. **Expected:** No emails sent
6. **Expected:** Stay on login page

### Test 3: Correct OTP
1. Complete Test 1
2. Check email for OTP (or use generated OTP from logs in development)
3. Enter correct 6-digit OTP
4. Click "Verify OTP"
5. **Expected:** Login successful
6. **Expected:** Redirect to Coordinator Dashboard
7. **Expected:** Can mark employee attendance

### Test 4: Incorrect OTP
1. Complete Test 1
2. Enter wrong OTP
3. Click "Verify OTP"
4. **Expected:** Error message with remaining attempts
5. **Expected:** OTP input cleared
6. **Expected:** Can try again

### Test 5: OTP Expiration
1. Complete Test 1
2. Wait 5 minutes
3. **Expected:** Timer shows "EXPIRED"
4. **Expected:** Verify button disabled
5. **Expected:** Must use "Resend OTP"

### Test 6: OTP Resend
1. Complete Test 1
2. Click "Resend OTP"
3. **Expected:** New OTP generated
4. **Expected:** New emails sent
5. **Expected:** Old OTP no longer valid
6. **Expected:** Timer reset to 5 minutes
7. **Expected:** 60-second cooldown before next resend

### Test 7: Max Attempts
1. Complete Test 1
2. Enter wrong OTP 5 times
3. **Expected:** Challenge invalidated after 5th attempt
4. **Expected:** Error: "Maximum attempts reached"
5. **Expected:** Must restart login process

### Test 8: Cancel Verification
1. Complete Test 1
2. Click "Cancel and Return to Login"
3. **Expected:** Challenge invalidated
4. **Expected:** Redirect to login page
5. **Expected:** Must restart login process

### Test 9: Direct Portal Access
1. Without logging in, go to: `smarthrms.online/coordinator/`
2. **Expected:** Redirect to login page
3. **Expected:** No access granted

### Test 10: Session Expiration
1. Complete Test 1 (reach OTP screen)
2. Close browser
3. Reopen browser
4. Go to OTP verification URL
5. **Expected:** Redirect to login (session expired)

---

## Production Checklist

Before enabling in production:

- [ ] Configure `MAIL_USERNAME` and `MAIL_PASSWORD` in `.env.production`
- [ ] Test email delivery to all 3 recipients
- [ ] Verify SMTP server connectivity
- [ ] Confirm firewall allows outbound SMTP (port 587)
- [ ] Test complete authentication flow end-to-end
- [ ] Verify OTP emails arrive promptly (< 30 seconds)
- [ ] Test resend functionality
- [ ] Verify rate limiting works
- [ ] Test max attempts invalidation
- [ ] Confirm coordinator portal access after OTP verification
- [ ] Test session security (no bypass possible)
- [ ] Verify mobile responsiveness of OTP screen
- [ ] Check email spam/junk folders if emails not arriving
- [ ] Document process for authorized HR contacts
- [ ] Train coordinator on new login flow

---

## Troubleshooting

### Emails Not Received

**Check:**
1. `MAIL_USERNAME` and `MAIL_PASSWORD` configured correctly
2. Gmail App Password (not regular password)
3. Firewall allows outbound SMTP on port 587
4. Check spam/junk folders
5. Verify recipient emails are correct in config
6. Check server logs for SMTP errors

**Server logs location:** `logs/smart_hrms.log`

### OTP Screen Not Loading

**Check:**
1. Password validation successful (check server logs)
2. Challenge token in session (use browser dev tools)
3. Database table `coordinator_otp_challenges` exists
4. No JavaScript errors (browser console)

### OTP Verification Failing

**Check:**
1. OTP entered correctly (6 digits, no spaces)
2. OTP not expired (5-minute limit)
3. Not exceeded max attempts (5)
4. Challenge not invalidated
5. Server time synchronized

### Development Testing Without Email

For development/testing without email:

1. Check server logs for generated OTP:
   ```
   [coordinator_otp_service] Created OTP challenge...
   ```

2. Or temporarily add logging in `coordinator_otp_service.py`:
   ```python
   logger.info(f"DEVELOPMENT OTP: {otp}")
   ```

3. Use logged OTP for verification

**Important:** Remove logging before production!

---

## API Endpoints

### POST `/auth/login` (action=coordinator)
**Step 1: Password Validation**

Request:
```
action=coordinator
employee_code=CS creative solution
password=CSCS@hr2013
```

Success Response:
- Redirect to `/auth/coordinator/verify-otp`
- Challenge token stored in session
- OTP emails sent

Error Response:
- Error message displayed
- Stays on login page

### GET/POST `/auth/coordinator/verify-otp`
**Step 2: OTP Verification**

GET: Display OTP input form

POST (action=verify):
```
action=verify
otp=123456
```

Success Response:
- Authenticated session created
- Redirect to coordinator dashboard

Error Response:
- Error message with remaining attempts
- OTP input cleared

POST (action=resend):
```
action=resend
```

Success Response:
- New OTP generated and sent
- Success message displayed
- Timer reset

### POST `/auth/coordinator/cancel-otp`
**Cancel Verification**

Request: (no parameters)

Response:
- Challenge invalidated
- Session cleared
- Redirect to login

---

## Maintenance

### Cleanup Expired Challenges

Run periodically (daily recommended):

```python
from app.services.coordinator_otp_service import CoordinatorOTPService
from app.extensions.mail import mail

otp_service = CoordinatorOTPService(mail=mail)
deleted_count = otp_service.cleanup_expired_challenges(hours=24)
print(f"Cleaned up {deleted_count} expired challenges")
```

Consider adding to scheduled tasks or cron job.

### Monitoring

Monitor these metrics:
- OTP email delivery success rate
- Average time to OTP verification
- Failed verification attempts
- Resend request frequency
- Challenge expiration rate

Log entries to watch:
- `OTP email sent successfully`
- `OTP verified successfully`
- `Invalid OTP for challenge`
- `Failed to send OTP email`

---

## Future Enhancements

Potential improvements:
- SMS OTP delivery option
- Authenticator app integration (TOTP)
- Backup codes for emergency access
- OTP verification history/audit log
- Configurable OTP length
- Custom email templates per environment
- Multi-language support
- IP-based rate limiting
- Geographic anomaly detection

---

## Support Contacts

**Authorized OTP Recipients:**
1. executivehr00013@gmail.com
2. durveshparab11cs@gmail.com
3. assistanthrmanager22@gmail.com

**Process for Coordinator:**
1. Login with fixed credentials
2. OTP sent to all 3 authorized contacts
3. Call HR contacts to obtain OTP
4. Enter OTP within 5 minutes
5. Access granted to Attendance Kiosk

---

## Implementation Summary

**Status:** ✅ **COMPLETE**

All requirements from the specification have been implemented:

✅ Two-step authentication (password + OTP)  
✅ Secure OTP generation (cryptographic)  
✅ Multi-recipient email (3 authorized addresses)  
✅ Bcrypt OTP hashing  
✅ 5-minute expiration  
✅ 6-digit OTP format  
✅ Professional security emails  
✅ OTP verification UI with timer  
✅ Resend functionality with cooldown  
✅ Rate limiting (attempts, resends)  
✅ Session security (no bypass)  
✅ Cancel verification option  
✅ Responsive UI matching Smart HRMS style  
✅ Server-side validation  
✅ Environment-based configuration  
✅ No credentials in frontend code  
✅ Single-use OTP enforcement  
✅ Existing portal functionality preserved  

**Ready for testing and deployment.**

---

**Implementation completed by Kiro AI**  
**Date: August 24, 2026**
