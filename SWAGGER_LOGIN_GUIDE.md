# 🔐 How to Login in Swagger UI

## Problem
You can't see your logged-in user in Swagger UI because Swagger requires authentication.

## Solution - Step by Step

### 1. Open Swagger UI
Go to: `http://127.0.0.1:8000/docs`

### 2. Register a Test User (if needed)
- Find `/api/auth/register` endpoint
- Click "Try it out"
- Enter:
```json
{
  "email": "test@test.com",
  "password": "test123",
  "full_name": "Test User"
}
```
- Click "Execute"
- Copy the `access_token` from response

### 3. Login with Existing User
- Find `/api/auth/login` endpoint
- Click "Try it out"
- Enter your credentials:
```json
{
  "email": "abdufathy2004@gmail.com",
  "password": "YOUR_PASSWORD"
}
```
- Click "Execute"
- Copy the `access_token` from response

### 4. Authorize in Swagger
- Click the **"Authorize"** button 🔓 (top right of page)
- In the popup, paste your token like this:
```
Bearer YOUR_ACCESS_TOKEN_HERE
```
Example:
```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzM4MDY...
```
- Click "Authorize"
- Click "Close"

### 5. Test Protected Endpoints
Now you can test endpoints that require authentication:
- `/api/auth/profile` - Get your profile
- `/api/search/recent` - Get recent searches
- `/api/chat/message` - Send chat message

---

## Existing Users in Database

You have these users already:
1. Email: `abdom.611p@gmail.com`
2. Email: `abdufathy2004@gmail.com`

If you don't remember the password, create a new test user using the register endpoint.

---

## Quick Test User

**Email**: `test@test.com`
**Password**: `test123`

Use the register endpoint to create this user, then login with it!

---

## Common Issues

### Issue: "Not authenticated" error
**Solution**: Make sure you clicked "Authorize" and pasted the token with "Bearer " prefix

### Issue: "Invalid token" error
**Solution**: The token might be expired (7 days). Login again to get a new token.

### Issue: Can't see the Authorize button
**Solution**: Scroll to the top of the Swagger UI page, it's in the top right corner.

---

**That's it!** Now you can test all your API endpoints in Swagger UI! 🚀
