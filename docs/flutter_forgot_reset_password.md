# Forgot & Reset Password — Flutter Integration Guide

Base URL: `https://7waleek.site`

---

## Full Flow Overview

```
1. User enters email → POST /auth/forgot-password
2. User receives email with deep link → aroundu://reset-password?token=xxx
3. App opens → extract token from deep link
4. App verifies token is still valid → POST /auth/verify-reset-token
5. Show "Enter new password" screen
6. User submits new password → POST /auth/reset-password
7. All existing sessions are logged out automatically
8. Redirect user to login screen
```

---

## Endpoints

### 1. Forgot Password
**POST** `/auth/forgot-password`

Request:
```json
{
  "email": "user@example.com"
}
```

Response (always 200, even if email not found — security):
```json
{
  "message": "If that email is registered, a reset link has been sent"
}
```

> Rate limited: 5 requests per minute per IP.

---

### 2. Verify Reset Token
**POST** `/auth/verify-reset-token`

Call this immediately after the app opens from the deep link, **before** showing the new password form.

Request:
```json
{
  "token": "the_token_from_deep_link"
}
```

Response `200` — token is valid:
```json
{
  "message": "Token is valid"
}
```

Response `400` — token is expired or already used:
```json
{
  "detail": "Invalid or expired reset token"
}
```

---

### 3. Reset Password
**POST** `/auth/reset-password`

Request:
```json
{
  "token": "the_token_from_deep_link",
  "new_password": "newpassword123"
}
```

- `new_password`: min 8 characters, max 100 characters

Response `200`:
```json
{
  "message": "Password reset successfully. Please log in."
}
```

Response `400` — token expired/used:
```json
{
  "detail": "Invalid, used, or expired reset token"
}
```

> After a successful reset, **all active sessions are invalidated**. The user must log in again with the new password.

---

## Deep Link Handling

The reset email contains a deep link in this format:
```
aroundu://reset-password?token=TOKEN_VALUE
```

In Flutter, extract the token like this:
```dart
final uri = Uri.parse(deepLink);
final token = uri.queryParameters['token']; // e.g. "abc123xyz..."
```

Make sure `aroundu` is registered as a custom URL scheme in:
- **Android**: `AndroidManifest.xml`
- **iOS**: `Info.plist`

---

## Token Rules

| Rule | Value |
|------|-------|
| Expiry | 30 minutes from request time |
| One-time use | Yes — token is invalidated after successful reset |
| Multiple requests | Each new request invalidates the previous token |

---

## Recommended Flutter Screen Flow

```
ForgotPasswordScreen
  └── EnterEmailScreen
        └── [POST /forgot-password]
              └── CheckEmailScreen ("We sent you a link")

[User taps link in email → app opens via deep link]

  └── [POST /verify-reset-token]
        ├── 400 → ShowExpiredTokenScreen ("Link has expired, request a new one")
        └── 200 → NewPasswordScreen
                    └── [POST /reset-password]
                          ├── 400 → ShowErrorScreen
                          └── 200 → LoginScreen ("Password changed successfully")
```

---

## Error Handling Summary

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Proceed to next step |
| 400 | Token invalid/expired/used | Show error, offer to resend |
| 429 | Too many requests | Show "Try again in a minute" |
| 500 | Server error | Show generic error |
