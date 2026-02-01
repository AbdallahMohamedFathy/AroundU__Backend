# 🚀 AroundU API - Flutter Integration Guide

## 📋 معلومات الاتصال الأساسية

### Base URL
```
http://127.0.0.1:8000
```

> ⚠️ **ملحوظة مهمة**: لما تشغل الـ Backend على جهازك وتحب تتصل بيه من الموبايل/إيميوليتور:
> - **Android Emulator**: استخدم `http://10.0.2.2:8000`
> - **iOS Simulator**: استخدم `http://127.0.0.1:8000`
> - **Physical Device**: استخدم IP address بتاع جهازك على الشبكة (مثال: `http://192.168.1.100:8000`)

### API Version
```
/api
```

### Full Base URL
```
http://127.0.0.1:8000/api
```

---

## 🔐 Authentication

الـ API بيستخدم **JWT (JSON Web Tokens)** للـ authentication.

### Secret Key (للمعلومية فقط - مش هتحتاجها في Flutter)
```
supersecretkey
```

### Authentication Flow

1. **Register** أو **Login** عشان تحصل على `access_token`
2. استخدم الـ `access_token` في كل الـ requests اللي محتاجة authentication
3. حط الـ token في الـ header بالشكل ده:
   ```
   Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
   ```

---

## 📡 API Endpoints

### 1️⃣ Authentication (`/api/auth`)

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Ahmed Mohamed"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Ahmed Mohamed"
  }
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Ahmed Mohamed"
  }
}
```

#### Get Profile (🔒 Requires Auth)
```http
GET /api/auth/profile
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Ahmed Mohamed"
}
```

---

### 2️⃣ Categories (`/api/categories`)

#### Get All Categories
```http
GET /api/categories?skip=0&limit=100
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Restaurants",
    "description": "Food and dining places",
    "icon": "restaurant"
  },
  {
    "id": 2,
    "name": "Cafes",
    "description": "Coffee shops and cafes",
    "icon": "cafe"
  }
]
```

#### Create Category
```http
POST /api/categories
Content-Type: application/json

{
  "name": "Parks",
  "description": "Public parks and gardens",
  "icon": "park"
}
```

---

### 3️⃣ Places (`/api/places`)

#### Get All Places
```http
GET /api/places?skip=0&limit=100
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Cairo Tower",
    "description": "Famous landmark in Cairo",
    "latitude": 30.0444,
    "longitude": 31.2357,
    "address": "Zamalek, Cairo",
    "category_id": 1,
    "rating": 4.5,
    "image_url": "https://example.com/image.jpg"
  }
]
```

#### Get Places by Category
```http
GET /api/places?category_id=1
```

#### Create Place
```http
POST /api/places
Content-Type: application/json

{
  "name": "New Restaurant",
  "description": "Amazing food",
  "latitude": 30.0444,
  "longitude": 31.2357,
  "address": "Downtown, Cairo",
  "category_id": 1,
  "rating": 4.0,
  "image_url": "https://example.com/image.jpg"
}
```

---

### 4️⃣ Search (`/api/search`)

#### Search Places (🔒 Optional Auth)
```http
GET /api/search?q=restaurant&category=food
Authorization: Bearer YOUR_ACCESS_TOKEN (optional)
```

**Query Parameters:**
- `q`: Search query (optional)
- `category`: Category filter (optional)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Cairo Tower",
    "description": "Famous landmark",
    "latitude": 30.0444,
    "longitude": 31.2357,
    "address": "Zamalek, Cairo",
    "category_id": 1,
    "rating": 4.5
  }
]
```

#### Get Recent Searches (🔒 Requires Auth)
```http
GET /api/search/recent
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
["restaurant", "cafe", "park"]
```

#### Get Trending Searches
```http
GET /api/search/trending
```

**Response:**
```json
{
  "trending": ["cairo tower", "egyptian museum", "khan el khalili"]
}
```

---

### 5️⃣ Chat (`/api/chat`)

#### Send Chat Message (🔒 Requires Auth)
```http
POST /api/chat/message
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "message": "What are the best restaurants nearby?"
}
```

**Response:**
```json
{
  "response": "Here are some great restaurants near you...",
  "suggestions": ["Restaurant A", "Restaurant B"]
}
```

---

## 💻 Flutter Integration Example

### 1. Setup Dependencies

أضف ده في `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.1.0
  shared_preferences: ^2.2.2
```

### 2. Create API Service Class

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // غير الـ Base URL ده حسب environment بتاعك
  static const String baseUrl = 'http://10.0.2.2:8000/api';
  
  // Get stored token
  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }
  
  // Save token
  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
  }
  
  // Register
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String fullName,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'full_name': fullName,
      }),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await saveToken(data['access_token']);
      return data;
    } else {
      throw Exception('Registration failed: ${response.body}');
    }
  }
  
  // Login
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await saveToken(data['access_token']);
      return data;
    } else {
      throw Exception('Login failed: ${response.body}');
    }
  }
  
  // Get Profile
  Future<Map<String, dynamic>> getProfile() async {
    final token = await getToken();
    
    final response = await http.get(
      Uri.parse('$baseUrl/auth/profile'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get profile: ${response.body}');
    }
  }
  
  // Get Categories
  Future<List<dynamic>> getCategories() async {
    final response = await http.get(
      Uri.parse('$baseUrl/categories'),
      headers: {'Content-Type': 'application/json'},
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get categories: ${response.body}');
    }
  }
  
  // Get Places
  Future<List<dynamic>> getPlaces({int? categoryId}) async {
    String url = '$baseUrl/places';
    if (categoryId != null) {
      url += '?category_id=$categoryId';
    }
    
    final response = await http.get(
      Uri.parse(url),
      headers: {'Content-Type': 'application/json'},
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get places: ${response.body}');
    }
  }
  
  // Search Places
  Future<List<dynamic>> searchPlaces({String? query, String? category}) async {
    String url = '$baseUrl/search?';
    if (query != null) url += 'q=$query&';
    if (category != null) url += 'category=$category';
    
    final token = await getToken();
    
    final response = await http.get(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Search failed: ${response.body}');
    }
  }
  
  // Send Chat Message
  Future<Map<String, dynamic>> sendChatMessage(String message) async {
    final token = await getToken();
    
    final response = await http.post(
      Uri.parse('$baseUrl/chat/message'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({'message': message}),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Chat failed: ${response.body}');
    }
  }
}
```

### 3. Usage Example

```dart
// في الـ widget بتاعك
final apiService = ApiService();

// Register
try {
  final result = await apiService.register(
    email: 'user@example.com',
    password: 'password123',
    fullName: 'Ahmed Mohamed',
  );
  print('Registered successfully: ${result['user']['full_name']}');
} catch (e) {
  print('Error: $e');
}

// Login
try {
  final result = await apiService.login(
    email: 'user@example.com',
    password: 'password123',
  );
  print('Logged in: ${result['user']['full_name']}');
} catch (e) {
  print('Error: $e');
}

// Get Places
try {
  final places = await apiService.getPlaces();
  print('Found ${places.length} places');
} catch (e) {
  print('Error: $e');
}

// Search
try {
  final results = await apiService.searchPlaces(query: 'restaurant');
  print('Found ${results.length} results');
} catch (e) {
  print('Error: $e');
}
```

---

## 🔧 Testing the API

### Using Swagger UI (Recommended)
افتح المتصفح وروح على:
```
http://127.0.0.1:8000/docs
```

هتلاقي واجهة تفاعلية تقدر تجرب كل الـ endpoints منها!

### Using ReDoc
```
http://127.0.0.1:8000/redoc
```

### Using cURL
```bash
# Register
curl -X POST "http://127.0.0.1:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123","full_name":"Test User"}'

# Login
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# Get Categories
curl -X GET "http://127.0.0.1:8000/api/categories"
```

---

## 📝 Important Notes

1. **Token Expiration**: الـ access token بيعيش **7 أيام**، بعد كده هتحتاج تعمل login تاني
2. **HTTPS in Production**: في الـ production لازم تستخدم HTTPS مش HTTP
3. **Error Handling**: كل الـ errors بترجع بـ status codes مناسبة:
   - `200`: Success
   - `201`: Created
   - `400`: Bad Request
   - `401`: Unauthorized
   - `404`: Not Found
   - `500`: Server Error

4. **CORS**: لو هتشتغل من الـ web، ممكن تحتاج تفعل CORS في الـ Backend

---

## 🚀 Quick Start Checklist

- [ ] شغل الـ Backend: `python src/main.py`
- [ ] تأكد إن السيرفر شغال على `http://127.0.0.1:8000`
- [ ] جرب الـ API من Swagger UI: `http://127.0.0.1:8000/docs`
- [ ] غير الـ `baseUrl` في Flutter حسب الـ environment بتاعك
- [ ] جرب الـ register/login endpoints الأول
- [ ] احفظ الـ token في `SharedPreferences`
- [ ] استخدم الـ token في باقي الـ requests

---

## 💡 Tips

1. **Development**: استخدم `http://10.0.2.2:8000` للـ Android Emulator
2. **Production**: غير الـ `baseUrl` للـ production server URL
3. **Token Storage**: استخدم `flutter_secure_storage` بدل `shared_preferences` للـ production
4. **Error Handling**: اعمل proper error handling لكل الـ API calls
5. **Loading States**: استخدم `FutureBuilder` أو state management solution

---

## 📞 Need Help?

لو عندك أي مشكلة أو سؤال، اتواصل معايا! 😊

**Happy Coding! 🚀**
