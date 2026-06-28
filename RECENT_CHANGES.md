# Recent Backend Changes

> Date: 2026-06-29

---

## 1. Place Status Fix — `is_open` vs `is_active`

### المشكلة
`is_active` كان بيتستخدم لعمليتين مختلفتين:
- **Hide** (الأدمن يخفي المكان) → `is_active = false`
- **Close** (الأونر يقفل المكان) → `is_active = false` ← نفس النتيجة

النتيجة: لما الأونر بيعمل Close، المكان بيختفي من الأبليكيشن بالكامل.

### الحل
فصل الـ concept في field منفصل:

| Field | المعنى | مين يتحكم فيه |
|-------|--------|--------------|
| `is_active` | مخفي / ظاهر (Hide/Show) | Admin فقط |
| `is_open` | مفتوح / مغلق (Open/Close) | Owner |

المكانات في الموبايل بتتفلتر بـ `is_active = true` فقط — المكانات المقفولة بتفضل ظاهرة وبيتبعت `is_open: false` في الـ response.

### الملفات اللي اتغيرت

#### `src/models/place.py`
```python
# أُضيف بعد is_active
is_open = Column(Boolean, default=True, nullable=False, server_default='true')
```

#### `src/schemas/place.py`
```python
# PlaceBase — الـ default مفتوح
is_open: bool = True

# PlaceUpdate — Owner يقدر يعدله
is_open: Optional[bool] = None

# PlaceResponse — بيتبعت للموبايل
is_open: bool = True

# NearbyPlaceResponse — بيتبعت في نتايج البحث القريب
is_open: bool = True
```

#### `src/api/dashboard/owner.py`
```python
# قبل
class UpdateStatus(BaseModel):
    is_active: bool = Field(...)

place.is_active = payload.is_active
return {"message": ..., "is_active": place.is_active}

# بعد
class UpdateStatus(BaseModel):
    is_open: bool = Field(...)

place.is_open = payload.is_open
return {"message": ..., "is_open": place.is_open}
```

#### `alembic/versions/f6a7b8c9d0e1_add_is_open_to_places.py` ← ملف جديد
```python
def upgrade():
    # يضيف column is_open بـ default = true لكل الصفوف الموجودة
    op.add_column('places',
        sa.Column('is_open', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )
```

---

## 2. Delivery Zones في Place Details

### المشكلة
`delivery_zones` كان موجود في الـ DB (JSONB column) لكن مش بيتبعتش في الـ API response، فالموبايل مش قادر يشوفه.

الـ endpoint المخصص له (`/api/owner/my-place/delivery-price`) بيرجع **403** للـ users العاديين.

### الحل
إضافة `delivery_zones` في `PlaceResponse` عشان يتضمن تلقائياً في:
```
GET /api/mobile/places/{id}/
```

### الملف اللي اتغير

#### `src/schemas/place.py`
```python
# PlaceResponse — أُضيف
delivery_zones: Optional[List[dict]] = []

# PlaceUpdate — Owner يقدر يعدل الزونز
delivery_zones: Optional[List[dict]] = None
```

### الـ Response بعد التغيير
```json
{
  "id": 5,
  "name": "test2",
  "delivery_price": 20,
  "is_free_delivery": false,
  "delivery_zones": [
    { "name": "بني سويف", "price": 30 },
    { "name": "الحي الثالث", "price": 50 }
  ]
}
```

> **ملاحظة:** لو `delivery_zones` مش متحطتش بيانات في الـ DB، الـ response هيرجع `null`. لو محتاج يرجع `[]` دايماً، لازم نضيف validator.

---

## ملخص الملفات المتغيرة

| الملف | نوع التغيير |
|-------|------------|
| `src/models/place.py` | إضافة column `is_open` |
| `src/schemas/place.py` | إضافة `is_open` و `delivery_zones` في الـ schemas |
| `src/api/dashboard/owner.py` | تعديل endpoint الـ status ليستخدم `is_open` |
| `alembic/versions/f6a7b8c9d0e1_add_is_open_to_places.py` | migration جديد لـ `is_open` |

---

## خطوات التفعيل

1. **شغل الـ migration:**
   ```bash
   alembic upgrade head
   ```

2. **أعد تشغيل الـ server** عشان الـ schema changes تتحمل.
