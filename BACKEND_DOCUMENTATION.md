# توثيق الباك اند - مشروع AroundU

> **آخر تحديث:** يونيو 2026  
> **الإصدار:** 1.0.0  
> **الإطار:** FastAPI + PostgreSQL + PostGIS

---

## جدول المحتويات

1. [نظرة عامة على المشروع](#1-نظرة-عامة-على-المشروع)
2. [التقنيات المستخدمة](#2-التقنيات-المستخدمة)
3. [هيكل المجلدات](#3-هيكل-المجلدات)
4. [الإعدادات والمتغيرات البيئية](#4-الإعدادات-والمتغيرات-البيئية)
5. [قاعدة البيانات](#5-قاعدة-البيانات)
6. [جميع الموديلات](#6-جميع-الموديلات)
7. [جميع الـ Schemas](#7-جميع-الـ-schemas)
8. [المصادقة والتحقق](#8-المصادقة-والتحقق)
9. [طبقة الخدمات](#9-طبقة-الخدمات)
10. [طبقة المستودعات](#10-طبقة-المستودعات)
11. [جميع الـ API Endpoints](#11-جميع-الـ-api-endpoints)
12. [نظام الأوردرات والكارت](#12-نظام-الأوردرات-والكارت)
13. [التكاملات الخارجية](#13-التكاملات-الخارجية)
14. [الـ Middleware وإدارة الأخطاء](#14-الـ-middleware-وإدارة-الأخطاء)
15. [Logging والمراقبة](#15-logging-والمراقبة)

---

## 1. نظرة عامة على المشروع

**AroundU** هو تطبيق لاكتشاف الأماكن بناءً على الموقع الجغرافي، مع نظام تجارة إلكترونية وشات بوت ذكاء اصطناعي.

### أبرز المميزات
- اكتشاف الأماكن القريبة باستخدام PostGIS
- شات بوت ذكاء اصطناعي مع Arabic/English support
- نظام أوردرات ومشتريات كامل
- لوحة تحكم للأصحاب والأدمن
- إشعارات Push عبر Firebase Cloud Messaging
- تحليل مشاعر التقييمات (Sentiment Analysis)
- توصيات مخصصة بخوارزمية Bayesian
- نظام عقارات (Properties)
- Full-text search مع تحليل الاتجاهات

---

## 2. التقنيات المستخدمة

### Core Framework
| الحزمة | الإصدار | الاستخدام |
|--------|---------|-----------|
| `fastapi` | >=0.104.1 | إطار العمل الأساسي |
| `uvicorn[standard]` | >=0.24.0 | ASGI Server |
| `gunicorn` | >=21.2.0 | Production Server |

### قاعدة البيانات
| الحزمة | الإصدار | الاستخدام |
|--------|---------|-----------|
| `sqlalchemy` | >=2.0.23 | ORM |
| `psycopg[binary]` | >=3.1.13 | PostgreSQL driver |
| `asyncpg` | >=0.29.0 | Async PostgreSQL |
| `geoalchemy2` | >=0.14.0 | PostGIS / Spatial queries |
| `alembic` | >=1.12.1 | Database Migrations |

### المصادقة والأمان
| الحزمة | الإصدار | الاستخدام |
|--------|---------|-----------|
| `pyjwt` | >=2.8.0 | JWT tokens |
| `passlib[bcrypt]` | >=1.7.4 | تشفير كلمات المرور |
| `python-jose[cryptography]` | >=3.3.0 | JOSE tokens |
| `firebase-admin` | >=6.3.0 | Firebase Auth SDK |

### API والبيانات
| الحزمة | الإصدار | الاستخدام |
|--------|---------|-----------|
| `pydantic[email]` | >=2.5.0 | Data validation |
| `pydantic-settings` | >=2.1.0 | Settings management |
| `httpx` | >=0.25.2 | Async HTTP client |
| `requests` | >=2.31.0 | HTTP client |

### الأداء والبنية التحتية
| الحزمة | الإصدار | الاستخدام |
|--------|---------|-----------|
| `slowapi` | >=0.1.9 | Rate limiting |
| `redis` | >=5.0.1 | Cache / Queues |
| `hiredis` | >=2.2.3 | Redis parser سريع |

### الوسائط والملفات
| الحزمة | الإصدار | الاستخدام |
|--------|---------|-----------|
| `Pillow` | >=10.1.0 | معالجة الصور |
| `cloudinary` | >=1.36.0 | Cloud storage للصور |
| `python-multipart` | >=0.0.6 | Form/File upload |

### أدوات أخرى
| الحزمة | الاستخدام |
|--------|-----------|
| `python-dotenv` | إدارة Environment Variables |
| `aiosmtplib` | Async Email |
| `python-json-logger` | JSON structured logging |

---

## 3. هيكل المجلدات

```
Around/
├── src/                          # الباك اند الرئيسي
│   ├── main.py                   # نقطة دخول التطبيق
│   ├── api/                      # جميع الـ API Routes
│   │   ├── mobile/               # APIs للموبايل
│   │   │   ├── auth.py
│   │   │   ├── places.py
│   │   │   ├── categories.py
│   │   │   ├── search.py
│   │   │   ├── favorites.py
│   │   │   ├── reviews.py
│   │   │   ├── items.py
│   │   │   ├── interactions.py
│   │   │   ├── recommendations.py
│   │   │   ├── properties.py
│   │   │   ├── notifications.py
│   │   │   └── ai.py
│   │   ├── dashboard/            # APIs للداشبورد
│   │   │   ├── places.py
│   │   │   ├── items.py
│   │   │   ├── categories.py
│   │   │   ├── upload.py
│   │   │   ├── admin.py
│   │   │   ├── admin_notifications.py
│   │   │   └── owner_notifications.py
│   │   ├── routes/               # Menu Management Routes
│   │   │   ├── categories.py
│   │   │   ├── subcategories.py
│   │   │   └── items.py
│   │   └── external/             # External AI Data API
│   │       └── ai_data.py
│   ├── models/                   # SQLAlchemy Models (29 موديل)
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── device.py
│   │   ├── password_reset_token.py
│   │   ├── audit_log.py
│   │   ├── api_key.py
│   │   ├── place.py
│   │   ├── place_image.py
│   │   ├── category.py
│   │   ├── subcategory.py
│   │   ├── item.py
│   │   ├── sub_item.py
│   │   ├── review.py
│   │   ├── favorite.py
│   │   ├── property.py
│   │   ├── property_image.py
│   │   ├── property_review.py
│   │   ├── property_favorite.py
│   │   ├── interaction.py
│   │   ├── ai_interaction.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── chat_message.py
│   │   ├── search_history.py
│   │   ├── search_trend.py
│   │   ├── notification.py
│   │   ├── notification_request.py
│   │   └── notification_audit.py
│   ├── schemas/                  # Pydantic Schemas
│   ├── services/                 # Business Logic (25+ service)
│   ├── repositories/             # Data Access Layer (19 repo)
│   └── core/                     # Core utilities
│       ├── config.py             # App settings
│       ├── database.py           # DB setup
│       ├── security.py           # Password & JWT
│       ├── dependencies.py       # DI providers
│       ├── permissions.py        # RBAC functions
│       ├── exceptions.py         # Custom exceptions
│       ├── unit_of_work.py       # UoW pattern
│       └── logger.py             # Logging setup
├── app/                          # نظام الأوردرات
│   └── orders/
│       ├── models/
│       │   └── order_models.py   # Order, OrderItem, Cart, CartItem
│       ├── services/
│       │   ├── order_service.py
│       │   └── cart_service.py
│       └── api/
│           ├── user/
│           │   ├── cart_api.py
│           │   └── order_api.py
│           ├── owner/
│           │   └── order_api.py
│           └── admin/
│               └── order_api.py
├── alembic/                      # Database Migrations
│   └── versions/                 # 20+ migration files
├── uploads/                      # Local file storage
├── requirements.txt
└── .env
```

---

## 4. الإعدادات والمتغيرات البيئية

**الملف:** `src/core/config.py`

### متغيرات بيئية إجبارية

| المتغير | الوصف |
|---------|-------|
| `SECRET_KEY` | مفتاح توقيع JWT (مطلوب في الإنتاج) |
| `DATABASE_URL` | رابط قاعدة البيانات PostgreSQL |
| `CLOUDINARY_CLOUD_NAME` | اسم حساب Cloudinary |
| `CLOUDINARY_API_KEY` | مفتاح Cloudinary |
| `CLOUDINARY_API_SECRET` | سر Cloudinary |
| `BREVO_API_KEY` | مفتاح خدمة البريد الإلكتروني |

### متغيرات Firebase
| المتغير | الوصف |
|---------|-------|
| `FIREBASE_SERVICE_ACCOUNT_JSON` | محتوى ملف الـ credentials كـ JSON string |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | مسار ملف الـ credentials |

### إعدادات الـ Tokens
| المتغير | القيمة الافتراضية | الوصف |
|---------|------------------|-------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 480 (8 ساعات) | مدة Access Token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 30 يوم | مدة Refresh Token |

### روابط خدمات الذكاء الاصطناعي
| المتغير | القيمة الافتراضية | الوصف |
|---------|------------------|-------|
| `AI_SERVICE_URL` | http://ai_service:8001 | خدمة الـ AI الرئيسية |
| `AI_TIMEOUT_SECONDS` | 3.0 | timeout للـ AI |
| `CHATBOT_SERVICE_URL` | https://youmnaaaa-gp-chatbot.hf.space | خدمة الشات بوت |
| `CHATBOT_TIMEOUT_SECONDS` | 15.0 | timeout للشات بوت |
| `AI_SENTIMENT_URL` | https://mazenmaher26-aroundu-sentiment.hf.space | تحليل المشاعر |

### إعدادات Rate Limiting
| المتغير | القيمة الافتراضية | الوصف |
|---------|------------------|-------|
| `RATE_LIMIT_ANON` | 30 req/min | الزوار غير المسجلين |
| `RATE_LIMIT_AUTH` | 120 req/min | المستخدمين المسجلين |

### إعدادات الملفات
| المتغير | القيمة الافتراضية | الوصف |
|---------|------------------|-------|
| `UPLOAD_FOLDER` | ./uploads | مجلد الرفع المحلي |
| `MAX_UPLOAD_SIZE` | 5MB | أقصى حجم للملف |
| `ALLOWED_EXTENSIONS` | jpg, jpeg, png, webp | الامتدادات المسموحة |

### إعدادات CORS
| المتغير | القيمة | الوصف |
|---------|-------|-------|
| `CORS_ORIGINS` | localhost:5173, localhost:3000, localhost:8501, dashboard.vercel.app | النطاقات المسموحة |

### إعدادات Connection Pool
| المتغير | القيمة | الوصف |
|---------|-------|-------|
| `DB_POOL_SIZE` | 5 | حجم الـ Pool الأساسي |
| `DB_MAX_OVERFLOW` | 10 | connections إضافية |
| `DB_POOL_TIMEOUT` | 30s | timeout للـ connection |
| `DB_POOL_RECYCLE` | 1800s (30 دقيقة) | تجديد الـ connections |
| `DB_QUERY_TIMEOUT_MS` | 5000ms | timeout للاستعلامات |

---

## 5. قاعدة البيانات

### التقنية
- **DBMS:** PostgreSQL
- **امتداد Spatial:** PostGIS (للبحث الجغرافي)
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic

### نظام الـ Unit of Work
**الملف:** `src/core/unit_of_work.py`

يدير دورة حياة الـ transactions ويضمن atomic operations:
- يفتح connection عند الدخول للـ context
- يشغل `commit()` عند النجاح
- يشغل `rollback()` عند الفشل
- يُهيئ 18 repository في نفس الوقت

### Auto-migrations عند الـ Startup

عند بدء التطبيق (`src/main.py → on_startup`) يتم تنفيذ ~15 migration تلقائية:

| الـ Migration | الوصف |
|--------------|-------|
| إضافة `owner_type` لـ users | إذا لم يكن موجوداً |
| إضافة `request_id` لـ notifications | ربط الإشعارات بطلباتها |
| إضافة `is_free_delivery` لـ places | إعداد التوصيل المجاني |
| إنشاء جدول `ai_interactions` | تسجيل محادثات الـ AI |
| إنشاء جدول `service_api_keys` | مفاتيح الخدمات الخارجية |
| إضافة أعمدة Firebase لـ users | `firebase_uid`, `provider`, `is_deleted`, `deleted_at` |
| إنشاء جدول `password_reset_tokens` | استعادة كلمة المرور |
| إنشاء جدول `property_favorites` | مفضلة العقارات |
| تعديل جدول `subcategories` | إعادة تسمية `category_id` → `place_id` |
| تعديل جدول `items` | إضافة `sub_category_id`, `image_url`, `is_available`, soft-delete columns |
| إنشاء جدول `sub_items` | variants للعناصر |
| تعديل جدول `properties` | إضافة `owner_name` |
| تعديل جدول `places` | إضافة `delivery_price`, `working_hours`, `is_accepting_orders`, `accepts_delivery`, `accepts_takeaway`, `delivery_zones` |
| إنشاء جداول الأوردرات | `orders`, `order_items`, `carts`, `cart_items` |
| إنشاء جدول `refresh_tokens` | Token rotation |

---

## 6. جميع الموديلات

### 6.1 موديلات المستخدمين

#### User — `src/models/user.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK, autoincrement | المعرف |
| `firebase_uid` | String | unique, nullable | معرف Firebase |
| `provider` | String | default="local" | طريقة التسجيل (local/google) |
| `full_name` | String | required | الاسم الكامل |
| `email` | String | unique, nullable | البريد الإلكتروني |
| `password_hash` | String | nullable | كلمة المرور مشفرة |
| `role` | String | default="USER" | الدور (USER/OWNER/ADMIN) |
| `owner_type` | String | nullable | نوع المالك (COMMERCIAL/RESIDENTIAL) |
| `is_active` | Boolean | default=True | هل الحساب نشط |
| `is_verified` | Boolean | default=False | هل الإيميل متحقق |
| `verification_token` | String | nullable | رمز التحقق من الإيميل |
| `reset_token` | String | nullable | رمز استعادة كلمة المرور (قديم) |
| `reset_token_expires` | DateTime | nullable | انتهاء رمز الاستعادة |
| `is_deleted` | Boolean | default=False | Soft delete |
| `deleted_at` | DateTime | nullable | تاريخ الحذف |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | on_update | تاريخ آخر تعديل |

**Properties:** `is_admin`, `is_owner`

**العلاقات:** places, subcategories, search_history, chat_messages, favorites, reviews, property_reviews, property_favorites, refresh_tokens, device_tokens, audit_logs, password_reset_tokens, ai_interactions

---

#### RefreshToken — `src/models/token.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users, indexed | المستخدم |
| `device_id` | Integer | FK→device_tokens, nullable | الجهاز |
| `token_hash` | String | unique, indexed | هاش الـ token |
| `family_id` | String | indexed | معرف العائلة (لكشف الهجمات) |
| `is_revoked` | Boolean | default=False | هل ملغي |
| `expires_at` | DateTime | required | تاريخ الانتهاء |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | on_update | تاريخ آخر تعديل |

---

#### DeviceToken — `src/models/device.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users, indexed | المستخدم |
| `fcm_token` | String | unique, indexed | رمز Firebase Cloud Messaging |
| `device_model` | String | nullable | موديل الجهاز |
| `os_version` | String | nullable | إصدار نظام التشغيل |
| `ip_address` | String | nullable | عنوان IP |
| `is_active` | Boolean | default=True | هل الجهاز نشط |
| `last_active_at` | DateTime | server_default | آخر نشاط |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |

---

#### PasswordResetToken — `src/models/password_reset_token.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | UUID | PK, default=uuid4 | المعرف |
| `user_id` | Integer | FK→users, indexed | المستخدم |
| `token_hash` | String | unique, indexed | هاش الرمز |
| `expires_at` | DateTime | required | تاريخ الانتهاء (30 دقيقة) |
| `is_used` | Boolean | default=False | هل استُخدم |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |

---

#### AuditLog — `src/models/audit_log.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users, nullable, indexed | المستخدم |
| `action` | String | indexed | الإجراء المنفذ |
| `ip_address` | String | nullable | عنوان IP |
| `device_info` | String | nullable | معلومات الجهاز |
| `metadata_info` | JSON | nullable | بيانات إضافية |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |

---

#### ServiceAPIKey — `src/models/api_key.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | UUID | PK, default=uuid4 | المعرف |
| `service_name` | String | required | اسم الخدمة |
| `api_key_hash` | String | unique, indexed | هاش المفتاح |
| `permissions` | JSON | required | الصلاحيات مثل ["read:places"] |
| `allowed_ips` | JSON | nullable | قائمة IPs المسموحة |
| `is_active` | Boolean | default=True | هل المفتاح نشط |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `last_used_at` | DateTime | nullable | آخر استخدام |

---

### 6.2 موديلات الأماكن

#### Place — `src/models/place.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `name` | String | indexed, required | اسم المكان |
| `description` | Text | nullable | وصف المكان |
| `address` | String | nullable | العنوان |
| `phone` | ARRAY(String) | nullable | أرقام الهاتف |
| `website` | String | nullable | الموقع الإلكتروني |
| `instagram_url` | String | nullable | رابط Instagram |
| `facebook_url` | String | nullable | رابط Facebook |
| `whatsapp_number` | String | nullable | رقم WhatsApp |
| `tiktok_url` | String | nullable | رابط TikTok |
| `rating` | Float | default=0.0, range: 0-5 | متوسط التقييم |
| `review_count` | Integer | default=0 | عدد التقييمات |
| `favorite_count` | Integer | default=0 | عدد المفضلة |
| `search_vector` | TSVECTOR | — | Full-text search index |
| `latitude` | Float | range: -90 to 90 | خط العرض |
| `longitude` | Float | range: -180 to 180 | خط الطول |
| `location` | Geography POINT | srid=4326 | نقطة PostGIS |
| `category_id` | Integer | FK→categories | الفئة |
| `owner_id` | Integer | FK→users, indexed | المالك |
| `parent_id` | Integer | FK→places, nullable | الفرع الأصلي (self-ref) |
| `is_active` | Boolean | default=True | هل المكان نشط |
| `delivery_price` | Float | default=0.0 | سعر التوصيل |
| `is_free_delivery` | Boolean | default=False | توصيل مجاني |
| `delivery_zones` | JSONB | nullable | مناطق التوصيل |
| `is_accepting_orders` | Boolean | default=True | يقبل أوردرات |
| `accepts_delivery` | Boolean | default=True | يقبل توصيل |
| `accepts_takeaway` | Boolean | default=True | يقبل تيك أواي |
| `working_hours` | String | nullable | مثال: "9:00 AM - 11:00 PM" |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | on_update | تاريخ آخر تعديل |

**العلاقات:** category, owner, images, favorites, reviews, subcategories, branches (self-referential)

---

#### PlaceImage — `src/models/place_image.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `place_id` | Integer | FK→places, indexed | المكان |
| `image_url` | String | required | رابط الصورة |
| `image_type` | String(20) | 'place' or 'menu' | نوع الصورة |
| `caption` | Text | nullable | وصف الصورة |
| `created_at` | DateTime | server_default | تاريخ الرفع |

---

#### Category — `src/models/category.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `name` | String | unique, indexed | اسم الفئة |
| `icon` | String | nullable | أيقونة (URL أو emoji) |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |

---

#### SubCategory — `src/models/subcategory.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `name` | String | indexed | اسم التصنيف الفرعي |
| `place_id` | Integer | FK→places | المكان (كان category_id سابقاً) |
| `owner_id` | Integer | FK→users | المالك |
| `is_deleted` | Boolean | default=False | Soft delete |
| `deleted_at` | DateTime | nullable | تاريخ الحذف |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | on_update | تاريخ آخر تعديل |

---

#### Item — `src/models/item.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `name` | String | indexed | اسم العنصر |
| `description` | Text | nullable | الوصف |
| `price` | Numeric(10,2) | required | السعر |
| `image_url` | String | nullable | رابط الصورة |
| `is_available` | Boolean | default=True | متاح للطلب |
| `sub_category_id` | Integer | FK→subcategories | التصنيف الفرعي |
| `is_deleted` | Boolean | default=False | Soft delete |
| `deleted_at` | DateTime | nullable | تاريخ الحذف |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | on_update | تاريخ آخر تعديل |

---

#### SubItem — `src/models/sub_item.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `name` | String | required | الاسم (مثل: Large, Extra Cheese) |
| `description` | Text | nullable | الوصف |
| `price` | Numeric(10,2) | required | السعر |
| `is_available` | Boolean | default=True | متاح |
| `item_id` | Integer | FK→items | العنصر الأصلي |
| `is_deleted` | Boolean | default=False | Soft delete |
| `deleted_at` | DateTime | nullable | تاريخ الحذف |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | on_update | تاريخ آخر تعديل |

---

### 6.3 موديلات التقييمات والمفضلة

#### Review — `src/models/review.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users | المستخدم |
| `place_id` | Integer | FK→places | المكان |
| `rating` | Float | range: 1-5 | التقييم |
| `comment` | Text | nullable | التعليق |
| `sentiment` | String(20) | nullable | المشاعر (positive/negative/neutral) |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | on_update | تاريخ آخر تعديل |

**Unique Constraint:** (user_id, place_id) — مستخدم واحد يقيّم مرة واحدة

---

#### Favorite — `src/models/favorite.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users | المستخدم |
| `place_id` | Integer | FK→places | المكان |
| `created_at` | DateTime | server_default | تاريخ الإضافة |
| `updated_at` | DateTime | nullable | تاريخ التعديل |

**Unique Constraint:** (user_id, place_id)

---

### 6.4 موديلات العقارات

#### Property — `src/models/property.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `title` | String | indexed | عنوان العقار |
| `description` | Text | nullable | الوصف |
| `price` | Float | indexed | السعر |
| `latitude` | Float | required | خط العرض |
| `longitude` | Float | required | خط الطول |
| `main_image_url` | String | nullable | الصورة الرئيسية |
| `contact_number` | ARRAY(String) | nullable | أرقام التواصل |
| `whatsapp_number` | String | nullable | رقم WhatsApp |
| `is_available` | Boolean | default=True | متاح |
| `owner_name` | String | nullable | اسم المالك |
| `owner_id` | Integer | FK→users, indexed | المالك في النظام |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | server_default | تاريخ آخر تعديل |

---

#### PropertyImage — `src/models/property_image.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `property_id` | Integer | FK→properties, indexed | العقار |
| `image_url` | String | required | رابط الصورة |
| `created_at` | DateTime | server_default | تاريخ الرفع |

---

#### PropertyReview — `src/models/property_review.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users | المستخدم |
| `property_id` | Integer | FK→properties | العقار |
| `rating` | Float | range: 1-5 | التقييم |
| `comment` | Text | nullable | التعليق |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |
| `updated_at` | DateTime | on_update | تاريخ التعديل |

---

#### PropertyFavorite — `src/models/property_favorite.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users | المستخدم |
| `property_id` | Integer | FK→properties | العقار |
| `created_at` | DateTime | server_default | تاريخ الإضافة |
| `updated_at` | DateTime | nullable | تاريخ التعديل |

**Unique Constraint:** (user_id, property_id)

---

### 6.5 موديلات التفاعل والذكاء الاصطناعي

#### Interaction — `src/models/interaction.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users, nullable | المستخدم (اختياري) |
| `place_id` | Integer | FK→places | المكان |
| `type` | String | required | نوع التفاعل: visit/call/direction/order/save |
| `user_lat` | Float | nullable | موقع المستخدم - خط عرض |
| `user_lon` | Float | nullable | موقع المستخدم - خط طول |
| `cluster_id` | Integer | nullable | مجموعة تجميع المواقع |
| `created_at` | DateTime | server_default | تاريخ التفاعل |

---

#### AIInteraction — `src/models/ai_interaction.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users, indexed | المستخدم |
| `session_id` | String(64) | indexed | معرف الجلسة |
| `message` | Text | required | رسالة المستخدم |
| `message_source` | String(10) | nullable | مصدر الرسالة: text/voice |
| `user_lat` | Float | nullable | موقع المستخدم - خط عرض |
| `user_lon` | Float | nullable | موقع المستخدم - خط طول |
| `reply` | Text | nullable | رد الـ AI |
| `intent` | String(128) | nullable | نية المستخدم |
| `confidence` | Float | nullable | درجة الثقة |
| `entities` | JSON | nullable | كيانات مستخرجة |
| `best_place` | JSON | nullable | أفضل مكان مقترح |
| `latency_ms` | Integer | nullable | زمن الاستجابة |
| `is_fallback` | Integer | default=0 | 1 إذا كان الـ AI غير متاح |
| `created_at` | DateTime | server_default, indexed | تاريخ الإنشاء |

---

### 6.6 موديلات الاتصالات والمحادثات

#### Conversation — `src/models/conversation.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users | المستخدم |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |

---

#### Message — `src/models/message.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `conversation_id` | Integer | FK→conversations | المحادثة |
| `sender` | String | required | المرسل: user/ai |
| `content` | Text | required | محتوى الرسالة |
| `timestamp` | DateTime | server_default | وقت الإرسال |

---

#### ChatMessage — `src/models/chat_message.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users | المستخدم |
| `message` | Text | required | رسالة المستخدم |
| `reply` | Text | required | رد الـ AI |
| `created_at` | DateTime | server_default | تاريخ الإنشاء |

---

### 6.7 موديلات البحث والاتجاهات

#### SearchHistory — `src/models/search_history.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users | المستخدم |
| `query` | String | required | نص البحث |
| `created_at` | DateTime | server_default | تاريخ البحث |
| `updated_at` | DateTime | on_update | آخر تكرار |

**Unique Constraint:** (user_id, query) — لا تكرار نفس البحث

---

#### SearchTrend — `src/models/search_trend.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `query` | String | PK, indexed | نص البحث |
| `count` | Integer | default=1 | عدد مرات البحث |
| `last_searched_at` | DateTime | server_default, on_update | آخر بحث |

---

### 6.8 موديلات الإشعارات

#### Notification — `src/models/notification.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `user_id` | Integer | FK→users | المستخدم |
| `request_id` | Integer | FK→notification_requests, nullable | ربط بطلب الإشعار |
| `title` | String | required | عنوان الإشعار |
| `message` | String | required | نص الإشعار |
| `type` | Enum | required | النوع (انظر أدناه) |
| `priority` | Enum | default=NORMAL | الأولوية (HIGH/NORMAL) |
| `is_read` | Boolean | default=False, indexed | هل قُرئ |
| `data` | JSON | nullable | بيانات إضافية |
| `created_at` | DateTime | server_default, indexed | تاريخ الإنشاء |

**NotificationType Enum:** NEW_REVIEW, NEW_PROPERTY_REVIEW, PROPERTY_APPROVED, PROPERTY_REJECTED, SYSTEM_ALERT, ORDER_STATUS

**Indexes:** (user_id, is_read), created_at DESC

---

#### NotificationRequest — `src/models/notification_request.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `sender_id` | Integer | FK→users | المرسل |
| `target_type` | Enum | required | ALL_USERS / ALL_OWNERS / SPECIFIC_OWNER / SPECIFIC_USER |
| `target_user_id` | Integer | FK→users, nullable | المستخدم المستهدف |
| `title` | String | required | العنوان |
| `message` | Text | required | الرسالة |
| `data` | JSON | nullable | بيانات إضافية |
| `status` | Enum | default=PENDING | PENDING / APPROVED / REJECTED |
| `is_archived` | Boolean | default=False | هل محفوظ |
| `approved_by` | Integer | FK→users, nullable | الأدمن الموافق |
| `approved_at` | DateTime | nullable | تاريخ الموافقة |
| `created_at` | DateTime | default=utcnow | تاريخ الإنشاء |

---

#### NotificationAudit — `src/models/notification_audit.py`
| الحقل | النوع | القيود | الوصف |
|-------|------|--------|-------|
| `id` | Integer | PK | المعرف |
| `request_id` | Integer | FK→notification_requests | الطلب |
| `admin_id` | Integer | FK→users | الأدمن |
| `action` | Enum | APPROVED / REJECTED | الإجراء |
| `timestamp` | DateTime | default=utcnow | وقت الإجراء |

---

## 7. جميع الـ Schemas

### 7.1 User Schemas — `src/schemas/user.py`

| Schema | الحقول |
|--------|--------|
| `UserBase` | email (optional) |
| `UserCreate` | email, password (min 8), full_name, owner_type (optional) |
| `UserLogin` | email, password |
| `SocialLogin` | id_token, device_model, os_version |
| `DeviceTokenCreate` | fcm_token, device_model, os_version |
| `UserUpdate` | full_name, email, owner_type (all optional) |
| `PasswordChange` | current_password, new_password |
| `PasswordResetRequest` | email |
| `PasswordReset` | token, new_password |
| `VerifyTokenRequest` | token |
| `UserResponse` | id, full_name, email, role, owner_type, is_active, is_verified, created_at |
| `Token` | access_token, token_type, refresh_token (optional) |
| `TokenRefresh` | refresh_token |
| `AuthResponse` | access_token, refresh_token, token_type, user (UserResponse) |
| `RefreshTokenRequest` | refresh_token |

---

### 7.2 Place Schemas — `src/schemas/place.py`

| Schema | الحقول الأساسية |
|--------|----------------|
| `PlaceBase` | name, description, address, phone[], website, latitude, longitude, category_id, parent_id, instagram_url, facebook_url, whatsapp_number, tiktok_url, delivery_price, is_free_delivery, is_accepting_orders, accepts_delivery, accepts_takeaway, working_hours |
| `PlaceCreate` | يرث من PlaceBase |
| `PlaceCreateRequest` | place_data (PlaceCreate), owner_user_id |
| `PlaceUpdate` | كل الحقول اختيارية |
| `PlaceResponse` | يرث من PlaceBase + id, rating, review_count, is_active, created_at, distance_km, images[], branches[], is_favorited |
| `NearbyPlaceResponse` | id, name, category, description, distance_km, delivery_price, is_free_delivery, working_hours, is_favorited |
| `NearbyPlaceListResponse` | total, page, page_size, total_pages, items[] |
| `PlaceListResponse` | total, page, page_size, total_pages, items[] |

---

### 7.3 Category Schemas — `src/schemas/category.py`

| Schema | الحقول |
|--------|--------|
| `CategoryBase` | name, icon (optional) |
| `CategoryCreate` | يرث من CategoryBase |
| `CategoryUpdate` | name (optional), icon (optional) |
| `CategoryResponse` | id, name, icon, created_at |

---

### 7.4 Item Schemas — `src/schemas/item.py`

| Schema | الحقول |
|--------|--------|
| `ItemBase` | name, description, price (>0), image_url, is_available, sub_category_id |
| `ItemCreate` | يرث من ItemBase |
| `ItemUpdate` | كل الحقول اختيارية |
| `ItemResponse` | يرث من ItemBase + id, subcategory_name, sub_items[], created_at, updated_at |
| `ItemPaginationResponse` | items[], total, page, size, pages |

---

### 7.5 SubCategory Schemas — `src/schemas/subcategory.py`

| Schema | الحقول |
|--------|--------|
| `SubCategoryBase` | name, place_id |
| `SubCategoryCreate` | يرث من SubCategoryBase |
| `SubCategoryUpdate` | name (optional), place_id (optional) |
| `SubCategoryResponse` | يرث من SubCategoryBase + id, owner_id, created_at |

---

### 7.6 SubItem Schemas — `src/schemas/sub_item.py`

| Schema | الحقول |
|--------|--------|
| `SubItemCreate` | name, description, price, is_available |
| `SubItemUpdate` | كل الحقول اختيارية |
| `SubItemResponse` | id, name, description, price, is_available, created_at, updated_at |

---

### 7.7 Review Schemas — `src/schemas/review.py`

| Schema | الحقول |
|--------|--------|
| `ReviewBase` | rating (1-5), comment (max 1000) |
| `ReviewCreate` | يرث من ReviewBase + place_id |
| `ReviewUpdate` | rating (optional), comment (optional) |
| `ReviewResponse` | يرث من ReviewBase + id, user_id, user_name, place_id, sentiment, created_at, updated_at |
| `ReviewListResponse` | items[], total, page, page_size |

---

### 7.8 Favorite Schemas — `src/schemas/favorite.py`

| Schema | الحقول |
|--------|--------|
| `FavoriteCreate` | place_id |
| `FavoriteResponse` | id, user_id, place_id, created_at |
| `FavoriteWithPlace` | id, place_id, created_at, place (dict, optional) |

---

### 7.9 Property Schemas — `src/schemas/property.py`

| Schema | الحقول |
|--------|--------|
| `PropertyBase` | title, description, price, latitude, longitude, contact_number[], whatsapp_number, owner_name |
| `PropertyCreate` | يرث من PropertyBase |
| `PropertyUpdate` | كل الحقول اختيارية + is_available, main_image_url, image_ids_to_delete[] |
| `PropertyImageResponse` | id, image_url, created_at |
| `PropertyReviewCreate` | rating (1-5), comment |
| `PropertyReviewResponse` | id, user_name, rating, comment, created_at |
| `PropertyMyResponse` | يرث من PropertyBase + id, main_image_url, is_available, owner_id, created_at, updated_at, images[], review_count, favorite_count |
| `PropertyResponse` | يرث من PropertyBase + id, images[], reviews[], review_count, favorite_count, is_favorited |
| `PropertyShortResponse` | id, title, price, main_image_url, review_count, favorite_count, is_favorited |
| `PropertyListResponse` | total, page, page_size, total_pages, items[] |

---

### 7.10 Interaction Schemas — `src/schemas/interaction.py`

| Schema | الحقول |
|--------|--------|
| `InteractionCreate` | place_id, type (visit/call/direction/order/save), user_lat, user_lon |
| `InteractionResponse` | id, user_id, place_id, type, user_lat, user_lon, cluster_id, created_at |

---

### 7.11 Notification Schemas — `src/schemas/notification.py`

| Schema | الحقول |
|--------|--------|
| `NotificationCreate` | user_id, title, message, type, priority, data (dict, optional) |
| `NotificationUpdate` | is_read |
| `NotificationResponse` | id, user_id, title, message, type, priority, is_read, data, created_at, sender_name, sender_id |
| `PaginatedNotificationResponse` | items[], total, page, page_size, total_pages |
| `NotificationRequestCreate` | target_type, target_user_id (optional), title, message, data |
| `FCMTokenUpdate` | fcm_token |

---

### 7.12 AI Schemas — `src/schemas/ai_schemas.py`

| Schema | الحقول |
|--------|--------|
| `AIInteractionResponse` | user_id, event_type, place_id, rating_value, timestamp |
| `AIPlaceResponse` | place_id, name, category, rating, review_count, lat, lng, sub_category, address, phone[], opening_hours, description, price_range, image_url, menu_items[], tags[], is_open |
| `AIAnalyticsResponse` | top_rated_places[], most_visited_places[], trending_categories[] |
| `AITrainingDataRow` | user_id, event_type, place_category, rating_value, timestamp |

---

### 7.13 Search Schemas — `src/schemas/search.py`

| Schema | الحقول |
|--------|--------|
| `SearchResponse` | places[], total, metadata (execution_time, count, fallback) |
| `TrendingSearch` | query, count |

---

### 7.14 AI Chat Schemas — `src/api/mobile/ai.py`

| Schema | الحقول |
|--------|--------|
| `ChatRequest` | message, session_id (optional), user_lat, user_lon, message_source (text/voice) |
| `ChatResponse` | reply, intent, confidence, entities, best_place, session_id, is_fallback |
| `HealthResponse` | status, models_loaded |

---

## 8. المصادقة والتحقق

**الملف:** `src/core/security.py`

### تشفير كلمات المرور
- **الخوارزمية:** PBKDF2-SHA256
- **عدد التكرارات:** 30,000 (عالي للأمان)
- **الدوال:**
  - `verify_password(plain, hashed) → bool`
  - `get_password_hash(password) → str`

### أنواع الـ Tokens

#### Access Token
- **الخوارزمية:** HS256
- **المدة:** 480 دقيقة (8 ساعات)
- **المحتوى:** `{exp, sub: user_id, type: "access", ...extra_data}`

#### Refresh Token
- **المدة:** 30 يوم (Rolling window)
- **المحتوى:** `{exp, sub: user_id, type: "refresh"}`
- **Token Rotation:** عند الاستخدام يُحذف القديم ويُنشأ جديد بنفس `family_id`

### طرق التسجيل والدخول

#### 1. Local Authentication
```
POST /api/mobile/auth/register → يتحقق من عدم تكرار الإيميل → يشفر كلمة المرور → ينشئ المستخدم → يرجع Access + Refresh tokens
POST /api/mobile/auth/login → يتحقق من الإيميل/كلمة المرور → يرجع tokens
```

#### 2. Firebase Social Authentication
```
POST /api/mobile/auth/social-login → يرسل ID Token → يتحقق منه عبر Firebase SDK → يبحث عن مستخدم بـ firebase_uid أو email → ينشئ مستخدم جديد إذا لم يوجد → يرجع tokens
```

#### 3. Token Refresh
```
POST /api/mobile/auth/refresh-token → يتحقق من الـ refresh token → يحذف القديم → ينشئ جديد بنفس family_id → يرجع tokens جديدة
```

### نظام الأدوار (RBAC)

| الدور | الصلاحيات |
|-------|----------|
| `USER` | تصفح الأماكن، التقييم، المفضلة، الأوردرات، الشات بوت |
| `OWNER` | إدارة أماكنه، القائمة، الأوردرات، الداشبورد التحليلي |
| `ADMIN` | كل شيء + إدارة المستخدمين، الإحصاءات، الإشراف |

### Permission Functions — `src/core/permissions.py`

```python
require_admin(user)                        # يرفع PermissionError إذا لم يكن ADMIN
require_owner_or_admin(user)               # يرفع PermissionError إذا لم يكن ADMIN أو OWNER
require_place_owner_or_admin(user, place)  # يتحقق من ملكية المكان أو ADMIN
require_dashboard_access(user)             # ADMIN أو OWNER فقط
```

### Service API Keys
- تُستخدم للوصول من الخدمات الخارجية (AI service)
- مخزنة كـ Hash في قاعدة البيانات
- تدعم IP whitelist
- تحدد الصلاحيات: مثل `["read:places", "read:interactions"]`

---

## 9. طبقة الخدمات

### 9.1 Auth Service — `src/services/auth_service.py`

| الدالة | الوصف |
|--------|-------|
| `register_user(uow, user_in)` | تسجيل مستخدم جديد، تحقق من تكرار الإيميل، تشفير كلمة المرور، إنشاء tokens |
| `authenticate_user(uow, user_in)` | تسجيل الدخول بالإيميل وكلمة المرور |
| `refresh_access_token(uow, user_id, token)` | تحديث الـ access token بعد التحقق من الـ refresh token |
| `social_login(uow, data)` | تسجيل/دخول عبر Firebase ID Token |
| `verify_email(uow, token)` | تأكيد البريد الإلكتروني |
| `request_password_reset(uow, email, bg_tasks)` | طلب استعادة كلمة المرور (يرسل إيميل في الخلفية) |
| `verify_reset_token(uow, token)` | التحقق من صلاحية رمز الاستعادة |
| `reset_password(uow, raw_token, new_password)` | تغيير كلمة المرور + إلغاء كل الـ refresh tokens |

---

### 9.2 Chatbot Service — `src/services/chatbot_service.py`

**أهم خدمة في المشروع** — تجمع بين قاعدة البيانات والذكاء الاصطناعي.

| الدالة | الوصف |
|--------|-------|
| `check_health()` | فحص جاهزية خدمة الـ AI |
| `chat(db, user_id, user_role, message, session_id, user_lat, user_lon, message_source, background_tasks)` | المنطق الأساسي للشات بوت |
| `clear_chat_history(db, user_id)` | حذف كل محادثات المستخدم |

**منطق `chat()`:**
1. ينشئ `session_id` تلقائياً إذا لم يُرسل
2. يجلب سياق المستخدم (آخر تفاعلاته ومفضلاته)
3. **RAG:** يجلب أفضل 5 أماكن ذات صلة من قاعدة البيانات ويحقنها في الـ prompt
4. يرسل الرسالة للخدمة الخارجية مع timeout 15 ثانية
5. **Grounding:** يطابق اقتراح الـ AI مع أماكن حقيقية في قاعدة البيانات
6. يسجل التفاعل بشكل غير متزامن (Background Task)
7. يرسل إشعار توصية إذا كانت الثقة عالية
8. **Fallback:** يرجع رد ودي إذا كان الـ AI غير متاح
9. عند فشل المطابقة يبحث في قاعدة البيانات مباشرة

---

### 9.3 Place Service — `src/services/place_service.py`

| الدالة | الوصف |
|--------|-------|
| `get_places(db, page, page_size, category_id, sort_by, sort_order)` | قائمة الأماكن مع pagination وفلتر |
| `get_place_by_id(db, place_id, current_user)` | تفاصيل مكان واحد |
| `get_nearby_places(db, lat, lng, radius_km, category_id, page, page_size)` | البحث الجغرافي (PostGIS) |
| `get_trending_places(db, page, page_size)` | أشهر الأماكن بتقييم مرجح |
| `create_place(uow, place_data, owner_user_id)` | إنشاء مكان جديد (Admin فقط) + ترقية المستخدم لـ OWNER |
| `update_place(uow, place_id, update_data, current_user)` | تحديث بيانات المكان |
| `delete_place(uow, place_id, current_user)` | حذف المكان |

---

### 9.4 Search Service — `src/services/search_service.py`

| الدالة | الوصف |
|--------|-------|
| `search_places(uow, query, lat, lng, user_id, limit)` | بحث متقدم مع Full-text + proximity |
| `get_recent_searches(repo, user_id, limit)` | آخر عمليات بحث للمستخدم |
| `get_trending_searches(repo, limit)` | أشهر عمليات البحث عالمياً |

**منطق البحث:**
1. يتحقق من وجود query (يرجع trending إذا كانت فارغة)
2. يستخدم `search_v2()` مع ترتيب بالصلة
3. Fallback: إذا لم تكن نتائج يرجع `get_popular_nearby()`
4. يسجل البحث في التاريخ ويحدث عداد الـ trends

---

### 9.5 Recommendation Service — `src/services/recommendation_service.py`

| الدالة | الوصف |
|--------|-------|
| `get_recommendations(session, lat, lng, radius_km, category_id, limit)` | توصيات مخصصة بـ Bayesian scoring |

**معادلة الترتيب:**
```
final_score = 0.5 × bayesian_rating + 0.3 × distance_score + 0.2 × favorite_score

bayesian_rating:  يراعي عدد التقييمات (أماكن بتقييمات قليلة تأخذ نقطة محايدة)
distance_score:   1 / (1 + distance_km)  ← يتناقص بزيادة المسافة
favorite_score:   log(1 + favorite_count) مُعيَّر على [0, 1]
```

---

### 9.6 Review Service — `src/services/review_service.py`

| الدالة | الوصف |
|--------|-------|
| `create_review(uow, user_id, review_data)` | إنشاء تقييم جديد مع تحليل المشاعر |
| `update_review(uow, review_id, user_id, update_data)` | تعديل التقييم |
| `delete_review(uow, review_id, user_id)` | حذف التقييم |

**منطق `create_review()`:**
1. يتحقق من وجود المكان
2. يتحقق من عدم التكرار (مستخدم/مكان)
3. يستدعي `sentiment_service` بشكل غير متزامن
4. ينشئ الـ Review
5. يعيد حساب متوسط تقييم المكان
6. يرسل إشعار للمالك في الخلفية

---

### 9.7 Notification Service — `src/services/notification_service.py`

| الدالة | الوصف |
|--------|-------|
| `create_notification(uow, user_id, title, message, type, data, priority, background_tasks, ...)` | إنشاء إشعار + FCM push |
| `create_bulk_notifications(uow, user_ids, ...)` | إشعارات جماعية (chunks of 500) |
| `send_push_notification(token, title, message, payload, priority)` | إرسال FCM notification |

**ملاحظة:** الإشعار يُحفظ في قاعدة البيانات دائماً حتى لو فشل الـ FCM.

---

### 9.8 AI Service — `src/services/ai_service.py`

| الدالة | الوصف |
|--------|-------|
| `send_chat_message(message, session_id, ...)` | إرسال رسالة للـ AI microservice |
| `get_recommendations(user_id)` | طلب توصيات من الـ AI |

---

### 9.9 Sentiment Service — `src/services/sentiment_service.py`

| الدالة | الوصف |
|--------|-------|
| `analyze_sentiment(text)` | تحليل مشاعر نص التقييم → "positive" / "negative" / None |

يستدعي: `POST https://mazenmaher26-aroundu-sentiment.hf.space/predict`

---

### 9.10 Base AI Service — `src/services/base_ai.py`

| الدالة | الوصف |
|--------|-------|
| `_request_with_retry(method, path, **kwargs)` | HTTP request مع exponential backoff |

**منطق الـ Retry:**
- خطأ 422 (Schema error): لا retry
- أخطاء الشبكة: exponential backoff
- يفشل بعد N محاولات

---

### 9.11 Admin Service — `src/services/admin_service.py`

| الدالة | الوصف |
|--------|-------|
| `get_db_tables(db)` | قائمة كل جداول قاعدة البيانات |
| `get_table_data(db, table_name)` | بيانات جدول معين (بدون حقول حساسة) |
| `execute_db_operation(db, table, op, data)` | INSERT/UPDATE/DELETE مباشر |
| `promote_user(uow, user_id, new_role)` | تغيير دور المستخدم |
| `create_owner_account(uow, user_data)` | إنشاء حساب owner جديد |
| `create_place_with_owner(uow, data)` | إنشاء مكان + ترقية المالك تلقائياً |
| `create_property_with_owner(uow, data)` | إنشاء عقار + ترقية المالك |
| `upload_property_images(db, property_id, files)` | رفع صور العقار |
| `get_platform_stats(db)` | إحصاءات المنصة الكاملة (users, places, orders, revenue) |
| `get_platform_trending(db)` | اتجاهات يومية |

---

### 9.12 Cloudinary Service — `src/services/cloudinary_service.py`

| الدالة | الوصف |
|--------|-------|
| `upload_image(file, folder)` | رفع صورة على Cloudinary (max 800×800) → يرجع secure_url |
| `delete_image(image_url)` | حذف صورة من Cloudinary |

---

### 9.13 Favorite Service — `src/services/favorite_service.py`

| الدالة | الوصف |
|--------|-------|
| `add_favorite(uow, user_id, place_id)` | إضافة لمفضلة + زيادة `favorite_count` |
| `remove_favorite(uow, user_id, place_id)` | حذف من مفضلة + تقليل `favorite_count` |
| `get_user_favorites(uow, user_id)` | قائمة مفضلات المستخدم |

---

### 9.14 User Service — `src/services/user_service.py`

| الدالة | الوصف |
|--------|-------|
| `update_user_profile(uow, user_id, update_data)` | تحديث بيانات الملف الشخصي |
| `change_password(uow, user_id, current_password, new_password)` | تغيير كلمة المرور |

---

### 9.15 Property Service — `src/services/property_service.py`

| الدالة | الوصف |
|--------|-------|
| `get_properties(db, page, page_size)` | قائمة العقارات |
| `get_property_by_id(db, property_id, user)` | تفاصيل عقار واحد |
| `get_my_properties(db, user_id)` | عقارات المستخدم |
| `create_property(uow, user_id, property_data)` | إنشاء عقار جديد |
| `update_property(uow, property_id, user_id, update_data)` | تحديث عقار |
| `delete_property(uow, property_id, user_id)` | حذف عقار |
| `add_property_review(uow, property_id, user_id, review_data)` | إضافة تقييم |
| `toggle_property_favorite(uow, property_id, user_id)` | إضافة/حذف من مفضلة |

---

## 10. طبقة المستودعات

**Pattern:** كل repository يرث من `BaseRepository[T]`

### BaseRepository — `src/repositories/base_repository.py`

```python
get_by_id(id) → Optional[T]
get_all(skip, limit) → List[T]
create(obj_in) → T
update(db_obj, obj_in) → T
delete(db_obj) → T
```

### repositories المتخصصة

#### place_repository — `src/repositories/place_repository.py`
| الدالة | الوصف |
|--------|-------|
| `get_by_id_with_details(place_id)` | تفاصيل المكان مع eager loading (Category + Branches) |
| `get_by_owner_id(owner_id)` | مكان المالك الأول |
| `get_all_by_owner_id(owner_id)` | كل أماكن المالك |
| `get_nearby(lat, lng, radius_km, category_id, limit, offset)` | **PostGIS** `ST_DWithin` + ترتيب بـ `<->` operator |
| `get_paginated(page, page_size, category_id, is_active, sort_by, sort_order)` | قائمة مرقمة مع فلاتر |
| `search_v2(q, lat, lng, limit)` | Full-text search مع ترتيب بالصلة |
| `get_trending(lat, lng, limit)` | أشهر الأماكن بدرجة مرجحة |
| `get_popular_nearby(lat, lng, limit)` | Fallback search للنتائج القريبة الشائعة |

---

#### user_repository — `src/repositories/user_repository.py`
| الدالة | الوصف |
|--------|-------|
| `get_by_email(email)` | بحث case-insensitive (يراعي الـ soft delete) |
| `get_by_verification_token(token)` | للتحقق من الإيميل |
| `get_by_reset_token(token)` | لاستعادة كلمة المرور |
| `get_by_firebase_uid(uid)` | للـ social login (يراعي الـ soft delete) |

---

#### review_repository — `src/repositories/review_repository.py`
| الدالة | الوصف |
|--------|-------|
| `get_user_review_for_place(user_id, place_id)` | فحص التكرار |
| `get_place_reviews(place_id, page, page_size)` | تقييمات المكان مع pagination |
| `get_user_reviews(user_id, page, page_size)` | تقييمات المستخدم |

---

#### favorite_repository — `src/repositories/favorite_repository.py`
| الدالة | الوصف |
|--------|-------|
| `get_user_favorite(user_id, place_id)` | فحص وجود المفضلة |
| `get_user_favorites(user_id)` | كل مفضلات المستخدم |
| `create_favorite(user_id, place_id)` | إضافة مفضلة |
| `delete_favorite(user_id, place_id)` | حذف مفضلة |

---

#### search_repository — `src/repositories/search_repository.py`
| الدالة | الوصف |
|--------|-------|
| `get_recent(user_id, limit)` | آخر N عمليات بحث للمستخدم |
| `get_trending(limit)` | أشهر N بحث عالمياً |
| `upsert_search(query, user_id)` | تسجيل بحث + زيادة العداد |
| `get_search_trends()` | سجل الاتجاهات التاريخي |

---

#### notification_repository — `src/repositories/notification_repository.py`
| الدالة | الوصف |
|--------|-------|
| `create(notification_data)` | إنشاء إشعار واحد |
| `bulk_create(notifications_data)` | إنشاء إشعارات متعددة |
| `get_by_id(notification_id)` | إشعار واحد |
| `mark_as_read(notification_id)` | تعليم كمقروء |
| `get_user_notifications(user_id, page, page_size)` | قائمة إشعارات المستخدم |

---

#### interaction_repository — `src/repositories/interaction_repository.py`
| الدالة | الوصف |
|--------|-------|
| `create_interaction(interaction_data)` | تسجيل تفاعل |
| `get_recent_interactions(user_id, limit)` | آخر تفاعلات المستخدم (للسياق في الـ chatbot) |

---

## 11. جميع الـ API Endpoints

### 11.1 Mobile Auth API — `/api/mobile/auth`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/register` | — | تسجيل مستخدم جديد |
| POST | `/login` | — | تسجيل الدخول |
| POST | `/social-login` | — | دخول بـ Firebase (Google/Apple) |
| POST | `/refresh-token` | — | تجديد الـ access token |
| GET | `/profile` | ✅ | عرض الملف الشخصي |
| PUT | `/profile` | ✅ | تعديل الملف الشخصي |
| POST | `/change-password` | ✅ | تغيير كلمة المرور |
| GET | `/verify-email` | — | تأكيد البريد الإلكتروني (link في الإيميل) |
| POST | `/forgot-password` | — | طلب استعادة كلمة المرور |
| POST | `/verify-reset-token` | — | التحقق من صلاحية رمز الاستعادة |
| POST | `/reset-password` | — | تعيين كلمة مرور جديدة |

**Rate Limits:** register: 5/min — login: 10/min

---

### 11.2 Mobile Places API — `/api/mobile/places`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/` | اختياري | قائمة الأماكن (page, page_size, category_id, sort_by, sort_order) |
| GET | `/nearby` | اختياري | أماكن قريبة (?latitude, ?longitude, ?radius_km, ?category_id, ?page, ?page_size) |
| GET | `/trending` | اختياري | أشهر الأماكن |
| GET | `/search-by-item` | اختياري | بحث بواسطة اسم عنصر (?item_name) |
| GET | `/{place_id}` | اختياري | تفاصيل مكان |
| GET | `/{place_id}/menu` | اختياري | قائمة الطعام |
| GET | `/{place_id}/images` | اختياري | صور المكان |

---

### 11.3 Mobile Categories API — `/api/mobile/categories`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/` | — | كل الفئات |
| GET | `/{category_id}` | — | تفاصيل فئة |

---

### 11.4 Mobile Search API — `/api/mobile/search`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/` | اختياري | بحث متقدم (?q, ?lat, ?lng, ?limit) |
| GET | `/recent` | ✅ | آخر عمليات بحث المستخدم |
| GET | `/trending` | — | أشهر عمليات البحث |

---

### 11.5 Mobile Favorites API — `/api/mobile/favorites`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/` | ✅ | قائمة المفضلة |
| POST | `/` | ✅ | إضافة لمفضلة (body: place_id) |
| DELETE | `/{place_id}` | ✅ | حذف من مفضلة |

---

### 11.6 Mobile Reviews API — `/api/mobile/reviews`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/place` | اختياري | كل التقييمات (paginated) |
| GET | `/place/{place_id}` | اختياري | تقييمات مكان |
| GET | `/me` | ✅ | تقييماتي |
| GET | `/{review_id}` | اختياري | تقييم واحد |
| POST | `/` | ✅ | إضافة تقييم جديد |
| PUT | `/{review_id}` | ✅ | تعديل تقييم |
| DELETE | `/{review_id}` | ✅ | حذف تقييم |

---

### 11.7 Mobile Items API — `/api/mobile/items`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/place/{place_id}` | اختياري | عناصر المكان |
| GET | `/{item_id}` | اختياري | تفاصيل عنصر |

---

### 11.8 Mobile Interactions API — `/api/mobile/interactions`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/` | اختياري | تسجيل تفاعل (visit/call/direction/order/save) |

---

### 11.9 Mobile Properties API — `/api/mobile/properties`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/` | اختياري | قائمة العقارات |
| GET | `/my` | ✅ | عقاراتي |
| GET | `/{id}` | اختياري | تفاصيل عقار |
| POST | `/` | ✅ | إضافة عقار جديد |
| PUT | `/{id}` | ✅ | تعديل عقار |
| DELETE | `/{id}` | ✅ | حذف عقار |
| POST | `/{id}/reviews` | ✅ | إضافة تقييم للعقار |
| GET | `/{id}/reviews` | اختياري | تقييمات عقار |
| GET | `/my-reviews` | ✅ | تقييماتي للعقارات |
| PUT | `/reviews/{review_id}` | ✅ | تعديل تقييم |
| DELETE | `/reviews/{review_id}` | ✅ | حذف تقييم |
| POST | `/{id}/favorites` | ✅ | إضافة عقار للمفضلة |
| DELETE | `/{id}/favorites` | ✅ | حذف عقار من المفضلة |

---

### 11.10 Mobile Notifications API — `/api/mobile/notifications`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/fcm-token` | ✅ | تسجيل جهاز للإشعارات |
| GET | `/` | ✅ | قائمة الإشعارات |
| PATCH | `/{notification_id}/read` | ✅ | تعليم كمقروء |
| POST | `/read-all` | ✅ | تعليم الكل كمقروء |
| GET | `/unread-count` | ✅ | عدد الإشعارات غير المقروءة |
| DELETE | `/clear-all` | ✅ | حذف كل الإشعارات |
| DELETE | `/{notification_id}` | ✅ | حذف إشعار واحد |

---

### 11.11 Mobile AI Chatbot API — `/api/mobile/ai`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/health` | — | فحص جاهزية الـ AI |
| POST | `/chat` | ✅ | محادثة مع الـ AI |
| DELETE | `/history` | ✅ | مسح تاريخ المحادثات |

**طلب `/chat`:**
```json
{
  "message": "عايز مطعم حواليا فيه كشري",
  "session_id": "abc123",
  "user_lat": 30.0444,
  "user_lon": 31.2357,
  "message_source": "text"
}
```

**استجابة `/chat`:**
```json
{
  "reply": "قريباً منك في مصر الجديدة...",
  "intent": "restaurant",
  "confidence": 0.92,
  "entities": {"cuisine": "koshary"},
  "best_place": {"id": 5, "name": "أبو طارق"},
  "session_id": "abc123",
  "is_fallback": false
}
```

---

### 11.12 Mobile Recommendations API — `/api/mobile/recommendations`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/` | — | توصيات (?lat, ?lng, ?radius_km, ?category_id, ?limit) |

---

### 11.13 Dashboard Categories API — `/api/dashboard/categories`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/` | Admin | إنشاء فئة جديدة |
| PUT | `/{category_id}` | Admin | تعديل فئة |
| DELETE | `/{category_id}` | Admin | حذف فئة |

---

### 11.14 Dashboard Places API — `/api/dashboard/places`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/` | Admin | إنشاء مكان جديد |
| PUT | `/{place_id}` | Admin | تعديل مكان |
| DELETE | `/{place_id}` | Admin | حذف مكان |

---

### 11.15 Dashboard Items API — `/api/dashboard/items`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/` | Owner/Admin | إنشاء عنصر |
| PUT | `/{item_id}` | Owner/Admin | تعديل عنصر |
| DELETE | `/{item_id}` | Owner/Admin | حذف عنصر (soft) |
| GET | `/place/{place_id}/top` | Owner/Admin | أشهر عناصر المكان |
| POST | `/{item_id}/image` | Owner/Admin | رفع صورة للعنصر |

---

### 11.16 Dashboard Upload API — `/api/dashboard/upload`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/place-image` | Owner/Admin | رفع صورة مكان |
| GET | `/place/{place_id}/images` | Owner/Admin | صور المكان |
| DELETE | `/image/{image_id}` | Owner/Admin | حذف صورة |

---

### 11.17 Owner Dashboard API — `/api/owner`

**البيانات الأساسية:**

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/my-place` | Owner | بيانات مكانه الأساسي |
| GET | `/my-places` | Owner | كل أماكنه |
| POST | `/add-branch` | Owner | إضافة فرع |
| PATCH | `/branches/{branch_id}` | Owner | تعديل فرع |
| DELETE | `/branches/{branch_id}` | Owner | حذف فرع |
| GET | `/customers` | Owner | بيانات العملاء |
| GET | `/{place_id}` | Owner | نظرة عامة على المكان |

**التحليلات والإحصاءات:**

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/dashboard` | Owner | بيانات الداشبورد الرئيسية |
| GET | `/analytics` | Owner | تحليلات مفصلة |
| GET | `/chatbot-stats` | Owner | إحصاءات الشات بوت |
| GET | `/reviews` | Owner | تقييمات مكانه |
| GET | `/location-heatmap` | Owner | خريطة حرارية للزيارات |
| GET | `/active-visitors` | Owner | الزوار النشطين حالياً |
| GET | `/peak-hour` | Owner | أوقات الذروة |
| GET | `/location-summary` | Owner | ملخص جغرافي |
| GET | `/opportunities` | Owner | فرص تجارية بالذكاء الاصطناعي |
| GET | `/interactions-locations` | Owner | مواقع تفاعلات المستخدمين |
| GET | `/clusters` | Owner | تجميعات المواقع |
| GET | `/anomalies` | Owner | كشف الشذوذات |
| GET | `/anomalies/summary` | Owner | ملخص الشذوذات |
| GET | `/place-anomalies` | Owner | شذوذات المكان |

**الإعدادات:**

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/my-place/delivery-price` | Owner | سعر التوصيل |
| PUT | `/my-place/delivery-price` | Owner | تعديل سعر التوصيل |
| GET | `/my-place/working-hours` | Owner | ساعات العمل |
| PUT | `/my-place/working-hours` | Owner | تعديل ساعات العمل |
| GET | `/my-place/order-settings` | Owner | إعدادات الأوردرات |
| PUT | `/my-place/order-settings` | Owner | تعديل إعدادات الأوردرات |
| PUT | `/my-place/status` | Owner | تغيير حالة قبول الطلبات |

**المراجعات والصور:**

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/places/{place_id}/reviews` | Owner | تقييمات مكانه |
| DELETE | `/reviews/{review_id}` | Owner | حذف تقييم |
| GET | `/places/{place_id}/items` | Owner | عناصر مكانه |
| POST | `/place-images` | Owner | رفع صور |
| DELETE | `/place-images/{image_id}` | Owner | حذف صورة |
| GET | `/reviews/list` | Owner | قائمة التقييمات |

---

### 11.18 Admin Dashboard API — `/api/dashboard/admin`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/promote/{user_id}` | Admin | ترقية مستخدم (تغيير دوره) |
| POST | `/owners` | Admin | إنشاء حساب مالك |
| POST | `/places` | Admin | إنشاء مكان |
| POST | `/properties` | Admin | إنشاء عقار |
| POST | `/properties/{property_id}/images` | Admin | رفع صور للعقار |
| GET | `/stats/overview` | Admin | إحصاءات عامة للمنصة |
| GET | `/stats/trending` | Admin | الاتجاهات اليومية |
| GET | `/stats/places` | Admin | إحصاءات الأماكن |
| GET | `/stats/users` | Admin | إحصاءات المستخدمين |
| GET | `/stats/categories` | Admin | إحصاءات الفئات |
| GET | `/stats/properties` | Admin | إحصاءات العقارات |
| GET | `/moderation/pending` | Admin | العناصر المعلقة للمراجعة |
| GET | `/interactions/recent` | Admin | آخر تفاعلات المستخدمين |
| DELETE | `/reviews/{review_id}` | Admin | حذف تقييم (إشراف) |
| POST | `/owners/{owner_id}/verify` | Admin | التحقق من مالك |
| GET | `/db/tables` | Admin | قائمة كل جداول قاعدة البيانات |
| GET | `/db/table/{table_name}` | Admin | بيانات جدول كامل |
| POST | `/db/table/{table_name}` | Admin | إضافة صف |
| PUT | `/db/table/{table_name}/{row_id}` | Admin | تعديل صف |
| DELETE | `/db/table/{table_name}/{row_id}` | Admin | حذف صف |
| POST | `/places/{place_id}/status` | Admin | تغيير حالة مكان |
| POST | `/users/{user_id}/status` | Admin | تغيير حالة مستخدم |

---

### 11.19 Admin Notifications API — `/api/dashboard/admin/notifications`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/requests` | Admin | طلبات الإشعارات المعلقة |
| POST | `/requests/{request_id}/approve` | Admin | الموافقة على طلب |
| POST | `/requests/{request_id}/reject` | Admin | رفض طلب |
| POST | `/requests/{request_id}/archive` | Admin | أرشفة طلب |
| POST | `/send` | Admin | إرسال إشعار جماعي |
| GET | `/all` | Admin | كل الإشعارات المرسلة |

---

### 11.20 Owner Notifications API — `/api/owner/notifications`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/request` | Owner | طلب إرسال إشعار |
| GET | `/requests` | Owner | طلباتي للإشعارات |

---

### 11.21 Menu Management API — `/api/v1`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/categories` | — | قائمة الفئات |
| POST | `/categories` | Owner/Admin | إنشاء فئة |
| PUT | `/categories/{id}` | Owner/Admin | تعديل فئة |
| DELETE | `/categories/{id}` | Owner/Admin | حذف فئة |
| GET | `/items` | — | قائمة عناصر (?subcategory_id, ?page, ?size) |
| GET | `/items/subcategory/{id}` | — | عناصر حسب التصنيف الفرعي |
| POST | `/items` | Owner/Admin | إنشاء عنصر |
| PUT | `/items/{id}` | Owner/Admin | تعديل عنصر |
| DELETE | `/items/{id}` | Owner/Admin | حذف عنصر |
| POST | `/subcategories` | Owner/Admin | إنشاء تصنيف فرعي |
| PUT | `/subcategories/{id}` | Owner/Admin | تعديل تصنيف فرعي |
| DELETE | `/subcategories/{id}` | Owner/Admin | حذف تصنيف فرعي |

---

### 11.22 External AI Data API — `/api/v1/ai/data`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/interactions` | API Key | تفاعلات المستخدمين للتدريب (?skip, ?limit) |
| GET | `/places` | API Key | بيانات الأماكن (?category, ?skip, ?limit) |
| GET | `/analytics` | API Key | تحليلات محسوبة مسبقاً |

---

### 11.23 Health Check

| HTTP | Endpoint | الوصف |
|------|----------|-------|
| GET | `/api/health` | فحص صحة النظام (DB, Redis, AI service) |

**الاستجابة:**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ai_service": "healthy"
  }
}
```
يرجع **503** إذا كانت أي خدمة أساسية غير متاحة.

---

## 12. نظام الأوردرات والكارت

**الملف:** `app/orders/`

### الموديلات

#### Order — `app/orders/models/order_models.py`
| الحقل | النوع | الوصف |
|-------|------|-------|
| `id` | Integer PK | المعرف |
| `user_id` | Integer indexed | المستخدم |
| `place_id` | Integer FK→places | المكان |
| `order_type` | Enum | CASH_ON_DELIVERY / TAKE_AWAY |
| `status` | Enum | PENDING / CONFIRMED / PREPARING / READY_FOR_PICKUP / OUT_FOR_DELIVERY / COMPLETED / CANCELLED |
| `full_name` | String | اسم المستلم |
| `phone_number` | String | رقم التليفون |
| `address` | String nullable | عنوان التوصيل |
| `notes` | String nullable | ملاحظات |
| `total_price` | Float | السعر الإجمالي |
| `created_at` | DateTime | تاريخ الأوردر |

---

#### OrderItem — `app/orders/models/order_models.py`
| الحقل | النوع | الوصف |
|-------|------|-------|
| `id` | Integer PK | المعرف |
| `order_id` | Integer FK→orders | الأوردر |
| `item_id` | Integer | معرف العنصر (Snapshot) |
| `sub_item_id` | Integer nullable | معرف الـ variant (Snapshot) |
| `item_name` | String | اسم العنصر وقت الشراء |
| `image_url` | String nullable | صورة العنصر |
| `unit_price` | Float | سعر الوحدة وقت الشراء |
| `quantity` | Integer | الكمية |
| `total_price` | Float | السعر الإجمالي للبند |

---

#### Cart — (من startup migration)
| الحقل | النوع | الوصف |
|-------|------|-------|
| `id` | Integer PK | المعرف |
| `user_id` | Integer FK→users | المستخدم |
| `owner_id` | Integer FK→users | مالك المكان |
| `total_price` | Float default=0 | السعر الكلي |
| `created_at` | DateTime | تاريخ الإنشاء |

**ملاحظة:** الكارت مرتبط بمكان واحد فقط — لا يمكن خلط أوردرات من أماكن مختلفة.

---

#### CartItem — (من startup migration)
| الحقل | النوع | الوصف |
|-------|------|-------|
| `id` | Integer PK | المعرف |
| `cart_id` | Integer FK→carts | الكارت |
| `item_id` | Integer | معرف العنصر |
| `quantity` | Integer default=1 | الكمية |
| `unit_price` | Float | سعر الوحدة |

---

### Cart Service — `app/orders/services/cart_service.py`

| الدالة | الوصف |
|--------|-------|
| `get_or_create_cart(user_id, place_id)` | جلب أو إنشاء كارت خاص بالمكان |
| `add_item(user_id, place_id, item_data)` | إضافة عنصر (يجلب السعر من DB لا من الـ request) |
| `get_cart(user_id, place_id)` | جلب الكارت مع كل عناصره |
| `update_item(user_id, place_id, cart_item_id, quantity)` | تحديث الكمية |
| `delete_item(user_id, place_id, cart_item_id)` | حذف عنصر |
| `clear_cart(user_id, place_id)` | تفريغ الكارت |

---

### Order Service — `app/orders/services/order_service.py`

| الدالة | الوصف |
|--------|-------|
| `checkout(user_id, order_data)` | إنشاء أوردر جديد |
| `get_order(user_id, order_id)` | تفاصيل أوردر (المستخدم يشوف أوردراته فقط) |
| `get_my_orders(user_id)` | كل أوردرات المستخدم |
| `cancel_order(user_id, order_id)` | إلغاء أوردر |
| `update_order_status(order_id, new_status)` | تغيير حالة (Owner/Admin) |

**منطق `checkout()`:**
1. يتحقق من وجود المكان وأنه يقبل طلبات
2. يتحقق من نوع الأوردر (DELIVERY يتطلب عنوان)
3. يحل بيانات العناصر من قاعدة البيانات (حماية من التلاعب بالأسعار)
4. يتحقق من توفر كل عنصر (`is_available = true`)
5. يحسب الإجمالي بدقة
6. ينشئ Order + OrderItems بشكل atomic
7. يفرّغ الكارت
8. يرسل إشعار للمالك في الخلفية

---

### Cart API — `/api/user/cart`

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/{place_id}` | ✅ | جلب الكارت |
| POST | `/{place_id}/items` | ✅ | إضافة عنصر |
| PATCH | `/{place_id}/items/{cart_item_id}` | ✅ | تعديل الكمية |
| DELETE | `/{place_id}/items/{cart_item_id}` | ✅ | حذف عنصر |
| DELETE | `/clear/{place_id}` | ✅ | تفريغ الكارت |

---

### Orders APIs

**User Orders — `/api/user/orders`:**

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| POST | `/checkout` | ✅ | إنشاء أوردر |
| GET | `/my` | ✅ | أوردراتي |
| GET | `/{order_id}` | ✅ | تفاصيل أوردر |
| PATCH | `/{order_id}/status` | Owner/Admin | تغيير الحالة |
| DELETE | `/{order_id}` | ✅ | إلغاء أوردر |

**Owner Orders — `/api/owner/orders`:**

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/place/{place_id}` | Owner/Admin | أوردرات المكان (?status, ?page, ?page_size) |
| PATCH | `/{order_id}/status` | Owner/Admin | تحديث حالة الأوردر |

**Admin Orders — `/api/admin/orders`:**

| HTTP | Endpoint | Auth | الوصف |
|------|----------|------|-------|
| GET | `/` | Admin | كل الأوردرات (?status, ?page, ?page_size) |
| GET | `/{order_id}` | Admin | تفاصيل أوردر |

---

## 13. التكاملات الخارجية

### 13.1 Firebase Authentication
- **SDK:** `firebase-admin`
- **الاستخدام:** التحقق من ID Tokens من Google/Apple
- **الإعداد:** `src/utils/firebase.py`
  - أولوية 1: JSON string من `FIREBASE_SERVICE_ACCOUNT_JSON`
  - أولوية 2: مسار ملف من `FIREBASE_SERVICE_ACCOUNT_PATH`
  - أولوية 3: البحث التلقائي عن `firebase-credentials.json`

### 13.2 Firebase Cloud Messaging (FCM)
- **الاستخدام:** إشعارات Push للموبايل
- **التنفيذ:** `src/services/notification_service.py`
- يرسل Multicast لـ 500 جهاز في المرة الواحدة

### 13.3 Cloudinary
- **الاستخدام:** تخزين الصور في السحابة
- **التنفيذ:** `src/services/cloudinary_service.py`
- **التحويل:** resize تلقائي لـ 800×800 pixels
- **الحذف:** استخراج `public_id` من URL ثم `destroy()`

### 13.4 Brevo Email Service
- **API:** `POST https://api.brevo.com/v3/smtp/email`
- **المصادقة:** `api-key` header
- **التنفيذ:** `src/utils/email.py`
- **البريد المرسل:**
  - تأكيد البريد الإلكتروني (link صالح 24 ساعة)
  - استعادة كلمة المرور (link صالح 30 دقيقة)

### 13.5 Chatbot AI Service (Beni Suef University)
- **URL:** `https://youmnaaaa-gp-chatbot.hf.space`
- **Endpoint:** `POST /chat`
- **Timeout:** 15 ثانية
- **Request:** `{message, session_id, user_lat, user_lon}`
- **Response:** `{reply, intent, confidence, entities, best_place}`
- **Fallback:** رد ودي إذا كانت الخدمة غير متاحة

### 13.6 Sentiment Analysis Service
- **URL:** `https://mazenmaher26-aroundu-sentiment.hf.space`
- **Endpoint:** `POST /predict`
- **Request:** `{text: review_comment}`
- **Response:** `{sentiment: "positive"|"negative"}`

### 13.7 Main AI Microservice
- **URL:** `AI_SERVICE_URL` env var (default: http://ai_service:8001)
- **Timeout:** 3 ثواني
- **Endpoints:**
  - `POST /chat/` — محادثة
  - `GET /recommendations/{user_id}` — توصيات

---

## 14. الـ Middleware وإدارة الأخطاء

### CORS Configuration
```
Development: Allow all origins (["*"])
Production:  localhost:5173, localhost:3000, localhost:8501, 
             dashboard-7waleek.vercel.app, 7waleek.com
```

### Rate Limiting
- **Library:** slowapi
- **Backend:** Redis (أو in-memory fallback)
- Anonymous: **30 req/min**
- Authenticated: **120 req/min**
- Per-endpoint custom: مثلاً `5/min` للتسجيل

### Response Format العام
كل ردود الـ API بالصيغة التالية:
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### Exception Handlers

| Exception | الـ Handler | الاستجابة |
|-----------|------------|----------|
| `APIException` | `api_exception_handler` | JSON مع message + code |
| `FastAPIHTTPException` | `http_exception_handler` | نفس status code |
| `StarletteHTTPException` | `http_exception_handler` | نفس status code |
| `RequestValidationError` | `validation_exception_handler` | 422 مع تفاصيل |
| `RateLimitExceeded` | `rate_limit_handler` | 429 Too Many Requests |
| `PermissionError` | `permission_exception_handler` | 403 Forbidden |
| `Exception` | `global_exception_handler` | 500 Internal Server Error |

### Static Files
```
/uploads → ./uploads (Local file storage)
```

---

## 15. Logging والمراقبة

**الملف:** `src/core/logger.py`

### الإعداد
- **المكتبة:** Python logging + `python-json-logger`
- **الصيغة:** JSON structured logs
- **الإخراج:** stdout (12-factor app pattern)
- **المستوى:** متحكم به بـ `LOG_LEVEL` env var (default: INFO)

### الأحداث المسجلة
| المكان | الحدث |
|--------|------|
| `app.main.on_startup` | بدء التطبيق، الـ migrations التلقائية |
| `chatbot_service` | Health checks، محادثات الـ AI، الأخطاء |
| `search_service` | وقت تنفيذ البحث، استخدام الـ fallback |
| `auth_service` | طلبات استعادة كلمة المرور، إرسال الإيميلات |
| `exceptions` | كل paths معالجة الأخطاء |

### نموذج Log
```json
{
  "timestamp": "2026-06-05T10:30:00Z",
  "level": "INFO",
  "action": "search",
  "query": "مطعم",
  "results_count": 12,
  "execution_time_ms": 45
}
```

---

## ملخص عددي

| العنصر | العدد |
|--------|------|
| **موديلات قاعدة البيانات** | 29 |
| **API Endpoints** | 120+ |
| **Pydantic Schemas** | 60+ |
| **Services** | 25+ |
| **Repositories** | 19 |
| **جداول قاعدة البيانات** | 30+ |
| **خدمات خارجية مدمجة** | 7 |
| **أدوار المستخدمين** | 3 (USER, OWNER, ADMIN) |
| **طرق المصادقة** | 3 (Local, Firebase, API Key) |
| **أنواع الإشعارات** | 6 |
| **حالات الأوردر** | 7 |

---

*هذا الملف يوثق كل ما تم بناؤه في الباك اند حتى تاريخ إنشائه.*
