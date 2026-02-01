# 🚀 Quick Start - ngrok

## 3 Simple Steps:

### 1. Download ngrok
https://ngrok.com/download

### 2. Start Backend
```bash
cd c:\Users\Mega Store\Desktop\AroundU_Backend
python src/main.py
```

### 3. Start ngrok (new terminal)
```bash
ngrok http 8000
```

### 4. Copy the URL
Look for: `https://abc123.ngrok.io`

### 5. Send to Flutter Developer
```dart
static const String baseUrl = 'https://abc123.ngrok.io/api';
```

---

**Full Guide**: See `NGROK_SETUP.md`

**That's it!** 🎉
