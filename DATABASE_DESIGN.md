# Database Design — AroundU
> PostgreSQL + PostGIS | SQLAlchemy ORM | Alembic Migrations

---

## جدول المحتويات
1. [نظرة عامة](#1-نظرة-عامة)
2. [ERD — مخطط قاعدة البيانات الكامل](#2-erd--مخطط-قاعدة-البيانات-الكامل)
3. [خريطة العلاقات الكاملة](#3-خريطة-العلاقات-الكاملة)
4. [جداول المستخدمين والمصادقة](#4-جداول-المستخدمين-والمصادقة)
5. [جداول الأماكن والقوائم](#5-جداول-الأماكن-والقوائم)
6. [جداول العقارات](#6-جداول-العقارات)
7. [جداول التفاعل والذكاء الاصطناعي](#7-جداول-التفاعل-والذكاء-الاصطناعي)
8. [جداول الإشعارات](#8-جداول-الإشعارات)
9. [جداول الأوردرات والكارت](#9-جداول-الأوردرات-والكارت)
10. [جداول البحث](#10-جداول-البحث)
11. [Indexes الكاملة](#11-indexes-الكاملة)
12. [Constraints وقواعد البيانات](#12-constraints-وقواعد-البيانات)
13. [Enums المستخدمة](#13-enums-المستخدمة)
14. [قرارات التصميم](#14-قرارات-التصميم)
15. [ملخص الجداول](#15-ملخص-الجداول)

---

## 1. نظرة عامة

| المعلومة | القيمة |
|---------|--------|
| **عدد الجداول** | 32 جدول |
| **DBMS** | PostgreSQL |
| **الامتداد الجغرافي** | PostGIS — `geography(Point, 4326)` |
| **ORM** | SQLAlchemy 2.0 |
| **Migrations** | Alembic |
| **Full-Text Search** | TSVECTOR + GIN index مدمج في PostgreSQL |
| **نمط الحذف** | Soft Delete في: `users`, `subcategories`, `items`, `sub_items` |
| **نمط المعرّفات** | `SERIAL` (Integer PK) — ماعدا `service_api_keys` و `password_reset_tokens`: UUID |

---

## 2. ERD — مخطط قاعدة البيانات الكامل

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        AroundU — Full Database ERD                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│  AUTH CLUSTER                                                               │
│                                                                             │
│  ┌─────────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │      USERS          │    │  REFRESH_TOKENS  │    │  DEVICE_TOKENS   │   │
│  │─────────────────────│    │──────────────────│    │──────────────────│   │
│  │PK id                │◄───│FK user_id        │    │FK user_id ───────│──►│
│  │   firebase_uid      │    │FK device_id──────│───►│PK id             │   │
│  │   provider          │    │PK id             │    │   fcm_token      │   │
│  │   full_name         │    │   token_hash     │    │   device_model   │   │
│  │   email             │    │   family_id      │    │   os_version     │   │
│  │   password_hash     │    │   is_revoked     │    │   ip_address     │   │
│  │   role              │    │   expires_at     │    │   is_active      │   │
│  │   owner_type        │    └──────────────────┘    │   last_active_at │   │
│  │   is_active         │                            └──────────────────┘   │
│  │   is_verified       │    ┌──────────────────┐    ┌──────────────────┐   │
│  │   is_deleted        │    │ PASS_RESET_TOKENS│    │   AUDIT_LOGS     │   │
│  │   deleted_at        │◄───│FK user_id        │◄───│FK user_id        │   │
│  │   created_at        │    │PK id (UUID)      │    │PK id             │   │
│  │   updated_at        │    │   token_hash     │    │   action         │   │
│  └─────────────────────┘    │   expires_at     │    │   ip_address     │   │
│           │                 │   is_used        │    │   metadata_info  │   │
│           │                 └──────────────────┘    └──────────────────┘   │
│           │                 ┌──────────────────┐                           │
│           │                 │ SERVICE_API_KEYS  │                           │
│           │                 │──────────────────│                           │
│           │                 │PK id (UUID)      │  (no FK to users)         │
│           │                 │   service_name   │                           │
│           │                 │   api_key_hash   │                           │
│           │                 │   permissions[]  │                           │
│           │                 │   allowed_ips[]  │                           │
│           │                 └──────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           │  owner_id
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLACES CLUSTER                                                             │
│                                                                             │
│  ┌──────────────────┐         ┌────────────────────────────────────────┐   │
│  │    CATEGORIES    │         │                PLACES                  │   │
│  │──────────────────│         │────────────────────────────────────────│   │
│  │PK id             │◄────────│FK category_id                          │   │
│  │   name (unique)  │         │FK owner_id → users                     │   │
│  │   icon           │         │FK parent_id → places (self-ref) ◄──┐   │   │
│  │   created_at     │         │PK id                               │   │   │
│  └──────────────────┘         │   name                             │   │   │
│                               │   description                      │   │   │
│                               │   address                          │   │   │
│                               │   phone[]          ← ARRAY         │   │   │
│                               │   website                          │   │   │
│                               │   instagram_url                    │   │   │
│                               │   facebook_url                     │   │   │
│                               │   whatsapp_number                  │   │   │
│                               │   tiktok_url                       │   │   │
│                               │   rating           ← 0.0–5.0       │   │   │
│                               │   review_count                     │   │   │
│                               │   favorite_count                   │   │   │
│                               │   search_vector    ← TSVECTOR/FTS  │   │   │
│                               │   latitude                         │   │   │
│                               │   longitude                        │   │   │
│                               │   location         ← PostGIS POINT │   │   │
│                               │   is_active                        │   │   │
│                               │   delivery_price                   │   │   │
│                               │   is_free_delivery                 │   │   │
│                               │   delivery_zones   ← JSONB         │   │   │
│                               │   is_accepting_orders              │   │   │
│                               │   accepts_delivery                 │   │   │
│                               │   accepts_takeaway                 │   │   │
│                               │   working_hours                    │   │   │
│                               │   created_at / updated_at          │───┘   │
│                               └────────────────────────────────────┘       │
│                                    │      │      │      │                   │
│            ┌───────────────────────┘      │      │      └────────────────┐  │
│            ▼                             ▼      ▼                       ▼  │
│   ┌──────────────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────────┐│
│   │  PLACE_IMAGES    │  │  REVIEWS   │  │FAVORITES │  │  INTERACTIONS    ││
│   │──────────────────│  │────────────│  │──────────│  │──────────────────││
│   │PK id             │  │PK id       │  │PK id     │  │PK id             ││
│   │FK place_id       │  │FK user_id  │  │FK user_id│  │FK user_id(null.) ││
│   │   image_url      │  │FK place_id │  │FK place_id│ │FK place_id       ││
│   │   image_type     │  │   rating   │  │created_at│  │   type           ││
│   │   caption        │  │   comment  │  │UNIQUE    │  │   user_lat/lon   ││
│   │   created_at     │  │   sentiment│  │(u,p)     │  │   cluster_id     ││
│   └──────────────────┘  │   created_at│ └──────────┘  └──────────────────││
│                         └────────────┘                                    │
│                                                                            │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │  MENU HIERARCHY                                                   │    │
│   │                                                                   │    │
│   │  SUBCATEGORIES ──► ITEMS ──► SUB_ITEMS                           │    │
│   │  (place_id FK)    (sub_cat FK)  (item_id FK)                     │    │
│   │  Soft Delete      Numeric price  Numeric price                   │    │
│   │  owner_id FK      Soft Delete    Soft Delete                     │    │
│   └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROPERTIES CLUSTER                                                         │
│                                                                             │
│  PROPERTIES ──► PROPERTY_IMAGES                                             │
│      │    └───► PROPERTY_REVIEWS (user_id FK)                               │
│      └────────► PROPERTY_FAVORITES (user_id FK, UNIQUE(user,prop))          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  NOTIFICATIONS CLUSTER                                                      │
│                                                                             │
│  NOTIFICATION_REQUESTS ──► NOTIFICATIONS                                    │
│  (sender_id, target_user_id, approved_by → users)   (user_id FK)           │
│       │                                                                     │
│       └──────────────────► NOTIFICATION_AUDITS (admin_id FK)                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ORDERS CLUSTER                                                             │
│                                                                             │
│  ORDERS ──────────────────────────────► ORDER_ITEMS (snapshot pattern)     │
│  (user_id: no FK!, place_id FK→places)  (item_id/sub_item_id: no FK!)      │
│                                                                             │
│  CARTS ────────────────────────────────► CART_ITEMS (cached data)          │
│  (user_id: no FK!, place_id FK→places)  (item_id: no FK!)                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  AI & SEARCH CLUSTER                                                        │
│                                                                             │
│  AI_INTERACTIONS (user_id FK, JSONB entities/best_place)                    │
│  CHAT_MESSAGES   (user_id FK, legacy)                                       │
│  CONVERSATIONS ──► MESSAGES (sender: user|ai)                               │
│  SEARCH_HISTORY  (user_id FK, UNIQUE(user,query))                           │
│  SEARCH_TRENDS   (query as PK, global counter)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. خريطة العلاقات الكاملة

```
USERS (1) ──────────────────────────────────────────────────────────────────
  │  owns many      ── PLACES              (owner_id)   CASCADE DELETE
  │  owns many      ── PROPERTIES          (owner_id)   CASCADE DELETE
  │  owns many      ── SUBCATEGORIES       (owner_id)   CASCADE DELETE
  │  has many       ── REVIEWS             (user_id)    CASCADE DELETE
  │  has many       ── FAVORITES           (place_id)   CASCADE DELETE
  │  has many       ── PROPERTY_REVIEWS    (user_id)    CASCADE DELETE
  │  has many       ── PROPERTY_FAVORITES  (user_id)    CASCADE DELETE
  │  has many       ── SEARCH_HISTORY      (user_id)    CASCADE DELETE
  │  has many       ── CHAT_MESSAGES       (user_id)    CASCADE DELETE
  │  has many       ── AI_INTERACTIONS     (user_id)    CASCADE DELETE
  │  has many       ── INTERACTIONS        (user_id)    CASCADE DELETE (nullable)
  │  has many       ── REFRESH_TOKENS      (user_id)    CASCADE DELETE
  │  has many       ── DEVICE_TOKENS       (user_id)    CASCADE DELETE
  │  has many       ── PASSWORD_RESET_TOKENS (user_id)  CASCADE DELETE
  │  has many       ── NOTIFICATIONS       (user_id)    CASCADE DELETE
  │  has many       ── CONVERSATIONS       (user_id)    CASCADE DELETE
  │  logged in      ── AUDIT_LOGS          (user_id)    SET NULL on delete
  └─────────────────────────────────────────────────────────────────────

PLACES (1) ──────────────────────────────────────────────────────────────────
  │  belongs to     ── CATEGORIES     (category_id)    no cascade
  │  belongs to     ── USERS          (owner_id)       CASCADE DELETE
  │  belongs to     ── PLACES (self)  (parent_id)      SET NULL on delete
  │  has many       ── PLACES (branches) (parent_id)   CASCADE DELETE
  │  has many       ── SUBCATEGORIES  (place_id)       CASCADE DELETE
  │  has many       ── PLACE_IMAGES   (place_id)       CASCADE DELETE
  │  has many       ── FAVORITES      (place_id)       CASCADE DELETE
  │  has many       ── REVIEWS        (place_id)       CASCADE DELETE
  │  has many       ── INTERACTIONS   (place_id)       CASCADE DELETE
  │  has many       ── ORDERS         (place_id)       SET NULL on delete
  │  has many       ── CARTS          (place_id)       CASCADE DELETE
  └─────────────────────────────────────────────────────────────────────

SUBCATEGORIES ──► ITEMS ──► SUB_ITEMS   (all CASCADE DELETE)

PROPERTIES (1) ──────────────────────────────────────────────────────────────
  │  has many       ── PROPERTY_IMAGES    (property_id) CASCADE DELETE
  │  has many       ── PROPERTY_REVIEWS   (property_id) CASCADE DELETE
  │  has many       ── PROPERTY_FAVORITES (property_id) CASCADE DELETE
  └─────────────────────────────────────────────────────────────────────

NOTIFICATION_REQUESTS ──────────────────────────────────────────────────────
  │  belongs to     ── USERS (sender)     CASCADE DELETE
  │  belongs to     ── USERS (target)     CASCADE DELETE (nullable)
  │  belongs to     ── USERS (approver)   SET NULL (nullable)
  │  has many       ── NOTIFICATIONS      SET NULL on delete
  │  has many       ── NOTIFICATION_AUDITS CASCADE DELETE
  └─────────────────────────────────────────────────────────────────────

ORDERS ──► ORDER_ITEMS       CASCADE DELETE
CARTS  ──► CART_ITEMS        CASCADE DELETE
REFRESH_TOKENS ──► (device_id → DEVICE_TOKENS)  SET NULL
CONVERSATIONS  ──► MESSAGES  CASCADE DELETE
```

---

## 4. جداول المستخدمين والمصادقة

### 4.1 `users`
```sql
CREATE TABLE users (
    id                  SERIAL          PRIMARY KEY,
    firebase_uid        VARCHAR         UNIQUE,            -- Google Auth UID
    provider            VARCHAR         DEFAULT 'local',   -- 'local' | 'google'
    full_name           VARCHAR         NOT NULL,
    email               VARCHAR         UNIQUE,            -- nullable للـ social auth
    password_hash       VARCHAR,                           -- nullable للـ social auth
    role                VARCHAR         NOT NULL DEFAULT 'USER',  -- USER|OWNER|ADMIN
    owner_type          VARCHAR,                           -- COMMERCIAL|RESIDENTIAL
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    is_verified         BOOLEAN         NOT NULL DEFAULT FALSE,
    is_deleted          BOOLEAN         NOT NULL DEFAULT FALSE,   -- Soft Delete
    deleted_at          TIMESTAMPTZ,
    verification_token  VARCHAR,
    reset_token         VARCHAR,
    reset_token_expires TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ
);
```
| Index | الحقل | النوع |
|-------|-------|------|
| PK | `id` | btree |
| UNIQUE | `email` | btree |
| UNIQUE | `firebase_uid` | btree |

---

### 4.2 `refresh_tokens`
```sql
CREATE TABLE refresh_tokens (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id   INTEGER     REFERENCES device_tokens(id) ON DELETE SET NULL,
    token_hash  VARCHAR     NOT NULL UNIQUE,    -- SHA-256 hash
    family_id   VARCHAR     NOT NULL,           -- كشف هجمات Token Reuse
    is_revoked  BOOLEAN     NOT NULL DEFAULT FALSE,
    expires_at  TIMESTAMPTZ NOT NULL,           -- 30 يوم
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ
);
```
| Index | الحقل |
|-------|-------|
| `user_id` | btree |
| `token_hash` UNIQUE | btree |
| `family_id` | btree |

---

### 4.3 `device_tokens`
```sql
CREATE TABLE device_tokens (
    id             SERIAL      PRIMARY KEY,
    user_id        INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fcm_token      VARCHAR     NOT NULL UNIQUE,    -- Firebase Cloud Messaging
    device_model   VARCHAR,
    os_version     VARCHAR,
    ip_address     VARCHAR,
    is_active      BOOLEAN     NOT NULL DEFAULT TRUE,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 4.4 `password_reset_tokens`
```sql
CREATE TABLE password_reset_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR     NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,     -- 30 دقيقة
    is_used     BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 4.5 `audit_logs`
```sql
CREATE TABLE audit_logs (
    id            SERIAL      PRIMARY KEY,
    user_id       INTEGER     REFERENCES users(id) ON DELETE SET NULL,
    action        VARCHAR     NOT NULL,     -- 'login' | 'password_reset' | ...
    ip_address    VARCHAR,
    device_info   VARCHAR,
    metadata_info JSONB,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 4.6 `service_api_keys`
```sql
CREATE TABLE service_api_keys (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name  VARCHAR     NOT NULL,
    api_key_hash  VARCHAR     NOT NULL UNIQUE,
    permissions   JSONB       NOT NULL,    -- ["read:places","read:interactions"]
    allowed_ips   JSONB,                   -- ["1.2.3.4"]
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    last_used_at  TIMESTAMPTZ
);
```

---

## 5. جداول الأماكن والقوائم

### 5.1 `categories`
```sql
CREATE TABLE categories (
    id         SERIAL      PRIMARY KEY,
    name       VARCHAR     NOT NULL UNIQUE,
    icon       VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 5.2 `places`
```sql
CREATE TABLE places (
    id                  SERIAL              PRIMARY KEY,
    name                VARCHAR             NOT NULL,
    description         TEXT,
    address             VARCHAR,
    phone               VARCHAR[],                          -- ARRAY
    website             VARCHAR,
    instagram_url       VARCHAR,
    facebook_url        VARCHAR,
    whatsapp_number     VARCHAR,
    tiktok_url          VARCHAR,
    rating              FLOAT               DEFAULT 0.0,
    review_count        INTEGER             DEFAULT 0,
    favorite_count      INTEGER             NOT NULL DEFAULT 0,
    search_vector       TSVECTOR,                           -- Full-Text Search
    latitude            FLOAT               NOT NULL,
    longitude           FLOAT               NOT NULL,
    location            geography(Point,4326),              -- PostGIS
    category_id         INTEGER             NOT NULL REFERENCES categories(id),
    owner_id            INTEGER             NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id           INTEGER             REFERENCES places(id) ON DELETE SET NULL,
    is_active           BOOLEAN             NOT NULL DEFAULT TRUE,
    delivery_price      FLOAT               NOT NULL DEFAULT 0.0,
    is_free_delivery    BOOLEAN             NOT NULL DEFAULT FALSE,
    delivery_zones      JSONB,
    is_accepting_orders BOOLEAN             NOT NULL DEFAULT TRUE,
    accepts_delivery    BOOLEAN             NOT NULL DEFAULT TRUE,
    accepts_takeaway    BOOLEAN             NOT NULL DEFAULT TRUE,
    working_hours       VARCHAR,
    created_at          TIMESTAMPTZ         DEFAULT NOW(),
    updated_at          TIMESTAMPTZ,

    CONSTRAINT check_latitude_range  CHECK (latitude  >= -90  AND latitude  <= 90),
    CONSTRAINT check_longitude_range CHECK (longitude >= -180 AND longitude <= 180),
    CONSTRAINT check_rating_range    CHECK (rating    >= 0    AND rating    <= 5)
);
```

| Index | الحقل | النوع | الغرض |
|-------|-------|------|-------|
| PK | `id` | btree | — |
| | `name` | btree | بحث بالاسم |
| | `owner_id` | btree | أماكن المالك |
| | `parent_id` | btree | الفروع |
| | `location` | GiST | PostGIS spatial |
| | `search_vector` | GIN | Full-text search |

---

### 5.3 `place_images`
```sql
CREATE TABLE place_images (
    id         SERIAL      PRIMARY KEY,
    place_id   INTEGER     NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    image_url  VARCHAR     NOT NULL,
    image_type VARCHAR(20) NOT NULL,    -- 'place' | 'menu'
    caption    TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 5.4 `subcategories`
```sql
CREATE TABLE subcategories (
    id         SERIAL      PRIMARY KEY,
    name       VARCHAR     NOT NULL,
    place_id   INTEGER     NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    owner_id   INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_deleted BOOLEAN     NOT NULL DEFAULT FALSE,    -- Soft Delete
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
```

---

### 5.5 `items`
```sql
CREATE TABLE items (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR         NOT NULL,
    description     TEXT,
    price           NUMERIC(10, 2)  NOT NULL,    -- دقة عشرية للأسعار
    image_url       VARCHAR,
    is_available    BOOLEAN         NOT NULL DEFAULT TRUE,
    sub_category_id INTEGER         NOT NULL REFERENCES subcategories(id) ON DELETE CASCADE,
    is_deleted      BOOLEAN         NOT NULL DEFAULT FALSE,    -- Soft Delete
    deleted_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);
```

---

### 5.6 `sub_items`
```sql
CREATE TABLE sub_items (
    id           SERIAL          PRIMARY KEY,
    name         VARCHAR         NOT NULL,        -- e.g. "Large", "Extra Cheese"
    description  TEXT,
    price        NUMERIC(10, 2)  NOT NULL,
    is_available BOOLEAN         NOT NULL DEFAULT TRUE,
    item_id      INTEGER         NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    is_deleted   BOOLEAN         NOT NULL DEFAULT FALSE,    -- Soft Delete
    deleted_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ     DEFAULT NOW(),
    updated_at   TIMESTAMPTZ
);
```

---

### 5.7 `reviews`
```sql
CREATE TABLE reviews (
    id         SERIAL      PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    place_id   INTEGER     NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    rating     FLOAT       NOT NULL,
    comment    TEXT,
    sentiment  VARCHAR(20),    -- 'positive' | 'negative' | 'neutral'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    CONSTRAINT check_review_rating_range CHECK (rating >= 1 AND rating <= 5)
);
```

---

### 5.8 `favorites`
```sql
CREATE TABLE favorites (
    id         SERIAL      PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    place_id   INTEGER     NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    CONSTRAINT unique_user_place_favorite UNIQUE (user_id, place_id)
);
```

---

## 6. جداول العقارات

### 6.1 `properties`
```sql
CREATE TABLE properties (
    id              SERIAL      PRIMARY KEY,
    title           VARCHAR     NOT NULL,
    description     TEXT,
    price           FLOAT       NOT NULL,
    latitude        FLOAT       NOT NULL,
    longitude       FLOAT       NOT NULL,
    main_image_url  VARCHAR,
    contact_number  VARCHAR[],              -- ARRAY
    whatsapp_number VARCHAR,
    is_available    BOOLEAN     NOT NULL DEFAULT TRUE,
    owner_name      VARCHAR,               -- اسم المالك الحقيقي
    owner_id        INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```
| Index | الحقل |
|-------|-------|
| | `title` |
| | `price` |
| | `owner_id` |

---

### 6.2 `property_images`
```sql
CREATE TABLE property_images (
    id          SERIAL      PRIMARY KEY,
    property_id INTEGER     NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    image_url   VARCHAR     NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 6.3 `property_reviews`
```sql
CREATE TABLE property_reviews (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    property_id INTEGER     NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    rating      FLOAT       NOT NULL,
    comment     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ,

    CONSTRAINT check_property_review_rating_range CHECK (rating >= 1 AND rating <= 5)
);
```

---

### 6.4 `property_favorites`
```sql
CREATE TABLE property_favorites (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    property_id INTEGER     NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ,

    CONSTRAINT unique_user_property_favorite UNIQUE (user_id, property_id)
);
```

---

## 7. جداول التفاعل والذكاء الاصطناعي

### 7.1 `interactions`
```sql
CREATE TABLE interactions (
    id         SERIAL      PRIMARY KEY,
    user_id    INTEGER     REFERENCES users(id) ON DELETE CASCADE,   -- nullable (زوار مجهولون)
    place_id   INTEGER     NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    type       VARCHAR     NOT NULL,    -- 'visit'|'call'|'direction'|'order'|'save'
    user_lat   FLOAT,
    user_lon   FLOAT,
    cluster_id INTEGER,                -- تجميع ML للمواقع
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 7.2 `ai_interactions`
```sql
CREATE TABLE ai_interactions (
    id             SERIAL      PRIMARY KEY,
    user_id        INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id     VARCHAR(64) NOT NULL,
    message        TEXT        NOT NULL,
    message_source VARCHAR(10) DEFAULT 'text',    -- 'text' | 'voice'
    user_lat       FLOAT,
    user_lon       FLOAT,
    reply          TEXT,
    intent         VARCHAR(128),
    confidence     FLOAT,                         -- [0.0 – 1.0]
    entities       JSONB,
    best_place     JSONB,
    latency_ms     INTEGER,
    is_fallback    INTEGER     DEFAULT 0,          -- 1 = AI كان غير متاح
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
```
| Index | الحقل |
|-------|-------|
| | `user_id` |
| | `session_id` |
| | `created_at` |

---

### 7.3 `chat_messages`
```sql
CREATE TABLE chat_messages (
    id         SERIAL      PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message    TEXT        NOT NULL,
    reply      TEXT        NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 7.4 `conversations`
```sql
CREATE TABLE conversations (
    id         SERIAL      PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 7.5 `messages`
```sql
CREATE TABLE messages (
    id              SERIAL      PRIMARY KEY,
    conversation_id INTEGER     NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender          VARCHAR     NOT NULL,    -- 'user' | 'ai'
    content         TEXT        NOT NULL,
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 8. جداول الإشعارات

### 8.1 `notifications`
```sql
CREATE TABLE notifications (
    id         SERIAL      PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id INTEGER     REFERENCES notification_requests(id) ON DELETE SET NULL,
    title      VARCHAR     NOT NULL,
    message    VARCHAR     NOT NULL,
    type       VARCHAR     NOT NULL,    -- NotificationType enum
    priority   VARCHAR     NOT NULL DEFAULT 'NORMAL',
    is_read    BOOLEAN     NOT NULL DEFAULT FALSE,
    data       JSONB,                  -- {place_id, order_id, ...}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Composite index للأداء
CREATE INDEX ix_notifications_user_read    ON notifications (user_id, is_read);
CREATE INDEX ix_notifications_created_desc ON notifications (created_at DESC);
```

---

### 8.2 `notification_requests`
```sql
CREATE TABLE notification_requests (
    id             SERIAL      PRIMARY KEY,
    sender_id      INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type    VARCHAR     NOT NULL,    -- ALL_USERS|ALL_OWNERS|SPECIFIC_OWNER|SPECIFIC_USER
    target_user_id INTEGER     REFERENCES users(id) ON DELETE CASCADE,
    title          VARCHAR     NOT NULL,
    message        TEXT        NOT NULL,
    data           JSONB,
    status         VARCHAR     NOT NULL DEFAULT 'PENDING',  -- PENDING|APPROVED|REJECTED
    is_archived    BOOLEAN     NOT NULL DEFAULT FALSE,
    approved_by    INTEGER     REFERENCES users(id) ON DELETE SET NULL,
    approved_at    TIMESTAMPTZ,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 8.3 `notification_audits`
```sql
CREATE TABLE notification_audits (
    id         SERIAL      PRIMARY KEY,
    request_id INTEGER     NOT NULL REFERENCES notification_requests(id) ON DELETE CASCADE,
    admin_id   INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action     VARCHAR     NOT NULL,    -- 'APPROVED' | 'REJECTED'
    timestamp  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 9. جداول الأوردرات والكارت

### 9.1 `orders`
```sql
CREATE TABLE orders (
    id           SERIAL      PRIMARY KEY,
    user_id      INTEGER     NOT NULL,                                       -- ⚠️ لا FK مقصود
    place_id     INTEGER     REFERENCES places(id) ON DELETE SET NULL,
    order_type   VARCHAR(50) NOT NULL,    -- 'CASH_ON_DELIVERY' | 'TAKE_AWAY'
    status       VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    full_name    VARCHAR     NOT NULL,
    phone_number VARCHAR     NOT NULL,
    address      VARCHAR,
    notes        VARCHAR,
    total_price  FLOAT       NOT NULL DEFAULT 0.0,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

**Order Status Flow:**
```
PENDING ──► CONFIRMED ──► PREPARING ──► READY_FOR_PICKUP ──► OUT_FOR_DELIVERY ──► COMPLETED
       ╲                                                                          ╱
        ╲──────────────────────────── CANCELLED ─────────────────────────────────╱
```

---

### 9.2 `order_items`
```sql
CREATE TABLE order_items (
    id          SERIAL  PRIMARY KEY,
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_id     INTEGER NOT NULL,       -- ⚠️ Snapshot — لا FK مقصود
    sub_item_id INTEGER,               -- ⚠️ Snapshot — nullable
    item_name   VARCHAR NOT NULL,      -- محفوظ حتى لو تغير اسم العنصر
    image_url   VARCHAR,               -- محفوظ
    unit_price  FLOAT   NOT NULL,      -- السعر وقت الشراء
    quantity    INTEGER NOT NULL,
    total_price FLOAT   NOT NULL
);
```

---

### 9.3 `carts`
```sql
CREATE TABLE carts (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL,                                     -- ⚠️ لا FK مقصود
    place_id    INTEGER     NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    total_price FLOAT       NOT NULL DEFAULT 0.0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```
**قاعدة مهمة:** مستخدم واحد له كارت واحد لكل مكان — لا خلط بين أماكن.

---

### 9.4 `cart_items`
```sql
CREATE TABLE cart_items (
    id         SERIAL  PRIMARY KEY,
    cart_id    INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    item_id    INTEGER NOT NULL,    -- ⚠️ لا FK — cached reference
    item_name  VARCHAR,             -- cached للعرض السريع
    image_url  VARCHAR,             -- cached
    quantity   INTEGER NOT NULL DEFAULT 1,
    unit_price FLOAT   NOT NULL
);
```

---

## 10. جداول البحث

### 10.1 `search_history`
```sql
CREATE TABLE search_history (
    id         SERIAL      PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query      VARCHAR     NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_user_query UNIQUE (user_id, query)
);
```

---

### 10.2 `search_trends`
```sql
CREATE TABLE search_trends (
    query            VARCHAR     PRIMARY KEY,    -- البحث نفسه هو الـ PK
    count            INTEGER     NOT NULL DEFAULT 1,
    last_searched_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 11. Indexes الكاملة

### UNIQUE Indexes
| الجدول | الحقل/الحقول | الـ Constraint |
|--------|-------------|--------------|
| `users` | `email` | UNIQUE |
| `users` | `firebase_uid` | UNIQUE |
| `categories` | `name` | UNIQUE |
| `favorites` | `(user_id, place_id)` | `unique_user_place_favorite` |
| `property_favorites` | `(user_id, property_id)` | `unique_user_property_favorite` |
| `search_history` | `(user_id, query)` | `unique_user_query` |
| `refresh_tokens` | `token_hash` | UNIQUE |
| `device_tokens` | `fcm_token` | UNIQUE |
| `password_reset_tokens` | `token_hash` | UNIQUE |
| `service_api_keys` | `api_key_hash` | UNIQUE |
| `search_trends` | `query` | PRIMARY KEY |

### Performance Indexes
| الجدول | الحقل | النوع | السبب |
|--------|-------|------|-------|
| `places` | `name` | btree | بحث بالاسم |
| `places` | `owner_id` | btree | أماكن المالك |
| `places` | `parent_id` | btree | الفروع |
| `places` | `location` | GiST | PostGIS spatial — أسرع `ST_DWithin` |
| `places` | `search_vector` | GIN | Full-text search |
| `subcategories` | `name` | btree | — |
| `subcategories` | `place_id` | btree | — |
| `items` | `name` | btree | — |
| `items` | `sub_category_id` | btree | — |
| `reviews` | `user_id` | btree | — |
| `reviews` | `place_id` | btree | — |
| `notifications` | `(user_id, is_read)` | btree composite | جلب إشعارات غير مقروءة |
| `notifications` | `created_at DESC` | btree | ترتيب زمني |
| `ai_interactions` | `user_id` | btree | — |
| `ai_interactions` | `session_id` | btree | — |
| `ai_interactions` | `created_at` | btree | — |
| `audit_logs` | `user_id` | btree | — |
| `audit_logs` | `action` | btree | — |
| `properties` | `title` | btree | — |
| `properties` | `price` | btree | فلترة بالسعر |
| `properties` | `owner_id` | btree | — |
| `orders` | `user_id` | btree | — |
| `orders` | `place_id` | btree | — |
| `carts` | `user_id` | btree | — |
| `carts` | `place_id` | btree | — |
| `refresh_tokens` | `user_id` | btree | — |
| `refresh_tokens` | `family_id` | btree | Token rotation |
| `device_tokens` | `user_id` | btree | — |

---

## 12. Constraints وقواعد البيانات

### Check Constraints
| الجدول | اسم الـ Constraint | القاعدة |
|--------|------------------|--------|
| `places` | `check_latitude_range` | `latitude >= -90 AND latitude <= 90` |
| `places` | `check_longitude_range` | `longitude >= -180 AND longitude <= 180` |
| `places` | `check_rating_range` | `rating >= 0 AND rating <= 5` |
| `reviews` | `check_review_rating_range` | `rating >= 1 AND rating <= 5` |
| `property_reviews` | `check_property_review_rating_range` | `rating >= 1 AND rating <= 5` |

### Unique Constraints
| الجدول | اسم الـ Constraint | الحقول |
|--------|------------------|--------|
| `favorites` | `unique_user_place_favorite` | `(user_id, place_id)` |
| `property_favorites` | `unique_user_property_favorite` | `(user_id, property_id)` |
| `search_history` | `unique_user_query` | `(user_id, query)` |

### ON DELETE Behaviors
| السلوك | المعنى | أمثلة |
|--------|--------|-------|
| **CASCADE** | احذف كل السجلات المرتبطة | حذف user → تُحذف favorites, reviews, tokens |
| **SET NULL** | اجعل الـ FK = NULL | حذف device → `refresh_token.device_id = NULL` |
| **RESTRICT** (ضمني) | امنع الحذف | — |

---

## 13. Enums المستخدمة

```python
# notification.py
NotificationType  = NEW_REVIEW | NEW_PROPERTY_REVIEW | PROPERTY_APPROVED
                    | PROPERTY_REJECTED | SYSTEM_ALERT | ORDER_STATUS

NotificationPriority = HIGH | NORMAL

# notification_request.py
TargetType    = ALL_USERS | ALL_OWNERS | SPECIFIC_OWNER | SPECIFIC_USER
RequestStatus = PENDING | APPROVED | REJECTED

# notification_audit.py
AuditAction   = APPROVED | REJECTED

# interaction.py
InteractionType = visit | call | direction | order | save

# app/orders/enums/enums.py
OrderType   = CASH_ON_DELIVERY | TAKE_AWAY
OrderStatus = PENDING | CONFIRMED | PREPARING | READY_FOR_PICKUP
              | OUT_FOR_DELIVERY | COMPLETED | CANCELLED

# users.role (String — not SQLEnum)
Role = USER | OWNER | ADMIN
```

---

## 14. قرارات التصميم

### 1. Soft Delete في 4 جداول فقط
الجداول `users`, `subcategories`, `items`, `sub_items` تستخدم `is_deleted + deleted_at` بدلاً من الحذف الفعلي.  
**السبب:** هذه الجداول مرتبطة بسجلات تاريخية (`orders`, `order_items`) يجب الحفاظ عليها.

### 2. Snapshot Pattern في الأوردرات
`order_items` يحفظ نسخة من `item_name`, `unit_price`, `image_url` وقت الشراء — بدون FK.  
**السبب:** تغيير سعر أو اسم المنتج لاحقاً لا يجب أن يؤثر على السجل التاريخي للأوردر.

### 3. لا FK في `orders.user_id` و `carts.user_id`
**السبب:** `app/orders/` و `src/` لهم قاعدتا بيانات منفصلتان في التهيئة — الـ `user_id` يُتحقق منه في الـ service layer.

### 4. PostGIS للبحث الجغرافي
- `places.location` من نوع `geography(Point, 4326)`
- البحث القريب يستخدم `ST_DWithin(location, target, radius_meters)`
- الترتيب بالأقرب يستخدم `location <-> target`
- **أداء أفضل بكثير** من حساب Haversine في Python

### 5. TSVECTOR للـ Full-Text Search
- `places.search_vector` يُحدَّث بـ trigger أو عند التعديل
- يدعم البحث بالعربي والإنجليزي مع stemming
- **أسرع بكثير** من `LIKE '%query%'` مع index GIN

### 6. Array Columns للهواتف
- `places.phone` و `properties.contact_number` من نوع `VARCHAR[]`
- **أبسط من** إنشاء جدول `place_phones` منفصل لهذه الحالة

### 7. JSONB للبيانات المرنة
| الجدول | الحقل | السبب |
|--------|-------|-------|
| `places` | `delivery_zones` | بنية متغيرة لمناطق التوصيل |
| `ai_interactions` | `entities`, `best_place` | بيانات الـ AI غير محددة الشكل |
| `notifications` | `data` | payload مختلف لكل نوع إشعار |
| `notification_requests` | `data` | — |
| `service_api_keys` | `permissions`, `allowed_ips` | قوائم مرنة |
| `audit_logs` | `metadata_info` | بيانات الحدث متغيرة |

### 8. Self-Referential في `places`
- `parent_id` يشير لنفس الجدول لتمثيل الفروع
- `parent_id = NULL` → مكان رئيسي
- `parent_id = id` → فرع
- `ON DELETE SET NULL` → لو الأصل اتحذف، الفرع يبقى مستقلاً

### 9. Token Rotation Security
- `refresh_tokens.family_id` يربط tokens من نفس جلسة الدخول
- لو token قديم استُخدم بعد التجديد → يُلغى كل الـ family
- هذا يكشف هجمات Token Theft / Token Reuse

### 10. UUID للعناصر الحساسة
- `service_api_keys.id` و `password_reset_tokens.id` هي UUIDs
- **السبب:** صعوبة التخمين (Integer يمكن iterate عليه)
- الـ token نفسه مشفر دائماً كـ SHA-256 hash

---

## 15. ملخص الجداول

| # | الجدول | Cluster | حقول | ملاحظات رئيسية |
|---|--------|---------|------|----------------|
| 1 | `users` | Auth | 17 | Soft Delete, Multi-auth, Role |
| 2 | `refresh_tokens` | Auth | 8 | Token Rotation, family_id |
| 3 | `device_tokens` | Auth | 8 | FCM Push Notifications |
| 4 | `password_reset_tokens` | Auth | 6 | UUID PK, 30min expiry |
| 5 | `audit_logs` | Auth | 6 | SET NULL on user delete |
| 6 | `service_api_keys` | Auth | 8 | UUID PK, Hashed key |
| 7 | `categories` | Places | 3 | UNIQUE name |
| 8 | `places` | Places | 28 | PostGIS + TSVECTOR + Self-ref |
| 9 | `place_images` | Places | 5 | type: place/menu |
| 10 | `subcategories` | Menu | 8 | Soft Delete |
| 11 | `items` | Menu | 10 | Soft Delete, NUMERIC price |
| 12 | `sub_items` | Menu | 9 | Soft Delete, Variants |
| 13 | `reviews` | Social | 7 | Sentiment field, CHECK rating |
| 14 | `favorites` | Social | 5 | UNIQUE(user,place) |
| 15 | `properties` | Real Estate | 13 | Array phones |
| 16 | `property_images` | Real Estate | 4 | — |
| 17 | `property_reviews` | Real Estate | 7 | CHECK rating |
| 18 | `property_favorites` | Real Estate | 5 | UNIQUE(user,prop) |
| 19 | `interactions` | Analytics | 7 | Nullable user_id |
| 20 | `ai_interactions` | AI | 14 | JSONB entities + best_place |
| 21 | `chat_messages` | AI | 5 | Legacy simple log |
| 22 | `conversations` | AI | 3 | — |
| 23 | `messages` | AI | 5 | sender: user/ai |
| 24 | `search_history` | Search | 5 | UNIQUE(user, query) |
| 25 | `search_trends` | Search | 3 | query IS the PK |
| 26 | `notifications` | Notifications | 10 | Composite index |
| 27 | `notification_requests` | Notifications | 11 | Approval workflow |
| 28 | `notification_audits` | Notifications | 5 | APPROVED/REJECTED enum |
| 29 | `orders` | E-commerce | 10 | Snapshot pattern, no FK user |
| 30 | `order_items` | E-commerce | 9 | Full snapshot, no FK items |
| 31 | `carts` | E-commerce | 5 | Per-place cart, no FK user |
| 32 | `cart_items` | E-commerce | 7 | Cached item data |

**الإجمالي: 32 جدول — 298 حقل**

---

*آخر تحديث: يونيو 2026*
