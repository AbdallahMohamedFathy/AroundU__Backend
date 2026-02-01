# AroundU API - Quick Reference

## 🔗 Base URL
```
http://127.0.0.1:8000/api
```

## 🔑 للـ Flutter Developer

### Important URLs:
- **Local (من جهازك)**: `http://127.0.0.1:8000`
- **Android Emulator**: `http://10.0.2.2:8000`
- **Physical Device**: `http://YOUR_IP:8000` (مثال: `http://192.168.1.100:8000`)

### Authentication:
- **Type**: JWT Bearer Token
- **Header**: `Authorization: Bearer YOUR_TOKEN`
- **Token Expiry**: 7 days

---

## 📡 Endpoints Summary

### Auth (`/api/auth`)
- `POST /register` - Register new user
- `POST /login` - Login user
- `GET /profile` - Get user profile (🔒 Auth required)

### Categories (`/api/categories`)
- `GET /` - Get all categories
- `POST /` - Create category

### Places (`/api/places`)
- `GET /` - Get all places
- `GET /?category_id=X` - Get places by category
- `POST /` - Create place

### Search (`/api/search`)
- `GET /?q=query&category=cat` - Search places
- `GET /recent` - Recent searches (🔒 Auth required)
- `GET /trending` - Trending searches

### Chat (`/api/chat`)
- `POST /message` - Send chat message (🔒 Auth required)

---

## 🧪 Test the API

**Swagger UI (Interactive Docs)**:
```
http://127.0.0.1:8000/docs
```

**ReDoc**:
```
http://127.0.0.1:8000/redoc
```

---

## 📝 Example Request (Login)

```dart
final response = await http.post(
  Uri.parse('http://10.0.2.2:8000/api/auth/login'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'email': 'user@example.com',
    'password': 'password123',
  }),
);

final data = jsonDecode(response.body);
String token = data['access_token'];
```

---

## 📚 Full Documentation
See `FLUTTER_INTEGRATION.md` for complete guide with code examples.
