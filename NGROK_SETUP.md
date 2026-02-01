# 🚀 Deploy AroundU Backend with ngrok

## Why ngrok?
- ✅ Works in 5 minutes
- ✅ No code changes needed
- ✅ Free
- ✅ Your Flutter developer can access from anywhere

---

## Step 1: Download ngrok

1. Go to: https://ngrok.com/download
2. Download for Windows
3. Extract the zip file
4. Put `ngrok.exe` somewhere easy (like Desktop)

---

## Step 2: Create ngrok Account (Optional but Recommended)

1. Go to: https://dashboard.ngrok.com/signup
2. Sign up (free)
3. Copy your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
4. Run this command (one time only):
   ```bash
   ngrok authtoken YOUR_AUTH_TOKEN_HERE
   ```

---

## Step 3: Start Your Backend

```bash
cd c:\Users\Mega Store\Desktop\AroundU_Backend
python src/main.py
```

Keep this terminal open!

---

## Step 4: Start ngrok (in a NEW terminal)

```bash
ngrok http 8000
```

You'll see something like:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:8000
```

**Copy this URL!** (the https one)

---

## Step 5: Test It

Open in browser:
```
https://abc123.ngrok.io/docs
```

If you see Swagger UI, it's working! ✅

---

## Step 6: Send to Flutter Developer

### Base URL for Flutter:
```dart
static const String baseUrl = 'https://abc123.ngrok.io/api';
```

### Full API URLs:
- Swagger: `https://abc123.ngrok.io/docs`
- Login: `https://abc123.ngrok.io/api/auth/login`
- Places: `https://abc123.ngrok.io/api/places`
- etc.

---

## ⚠️ Important Notes

### 1. Keep Both Terminals Open
- Terminal 1: Backend (`python src/main.py`)
- Terminal 2: ngrok (`ngrok http 8000`)

### 2. URL Changes Every Time
- Every time you restart ngrok, you get a NEW URL
- Send the new URL to your Flutter developer
- **Solution**: Use a free ngrok account for a static domain (optional)

### 3. Free Limits
- Free plan: 1 ngrok process at a time
- 40 connections/minute
- Good enough for development!

---

## 🎯 Quick Commands

### Start Backend:
```bash
cd c:\Users\Mega Store\Desktop\AroundU_Backend
python src/main.py
```

### Start ngrok (in new terminal):
```bash
ngrok http 8000
```

### Stop ngrok:
Press `Ctrl+C`

---

## 🔧 Troubleshooting

### Problem: "command not found: ngrok"
**Solution**: Make sure ngrok.exe is in your PATH or run it from the folder where you extracted it

### Problem: "ERR_NGROK_108"
**Solution**: You need to sign up and add your authtoken (see Step 2)

### Problem: Backend not responding
**Solution**: Make sure your backend is running on port 8000

### Problem: CORS errors
**Solution**: Already fixed! Your backend has CORS enabled.

---

## 📱 For Your Flutter Developer

Send them:
1. The ngrok URL (e.g., `https://abc123.ngrok.io`)
2. Tell them to use: `https://abc123.ngrok.io/api` as base URL
3. Send them `FLUTTER_INTEGRATION.md` for API documentation

---

## 🎉 That's It!

Your backend is now accessible from anywhere in the world! 🌍

**Next Steps:**
1. Download ngrok
2. Run the commands above
3. Send the URL to your Flutter developer
4. Start building! 🚀
