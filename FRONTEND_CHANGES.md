# API Changes — Frontend Teams

> Date: 2026-06-29  
> Affects: Flutter App · Dashboard

---

## Change 1 — Place Open/Close Status

### Background
Previously, closing a place made it **completely disappear** from the app. This is now fixed.

A new field `is_open` has been added to separate two different concepts:

| Field | Meaning | Who controls it |
|-------|---------|-----------------|
| `is_active` | Place is visible / hidden | Admin only |
| `is_open` | Place is open / closed | Owner |

A **closed** place still appears in the app — it just shows a "Closed" status.  
A **hidden** place (`is_active = false`) does not appear at all.

---

### Flutter App

#### New field in Place response
All place endpoints now return `is_open`:

```
GET /api/mobile/places/{id}/
GET /api/mobile/places/
GET /api/mobile/places/nearby
GET /api/mobile/places/trending
```

**Response example:**
```json
{
  "id": 5,
  "name": "test2",
  "is_active": true,
  "is_open": false,
  "delivery_price": 20,
  ...
}
```

**Action required:**
- If `is_open == false` → show a **"Closed"** badge on the place card and details screen
- Do **not** hide the place — it should still be visible and browsable

---

### Dashboard (Owner)

#### Status endpoint — request body changed

```
PUT /api/owner/my-place/status
```

**Before (old — no longer works):**
```json
{ "is_active": true }
```

**After (new):**
```json
{ "is_open": true }
```

**Response:**
```json
{
  "message": "Place status updated to Open",
  "is_open": true
}
```

**Action required:**
- Update the Open/Close toggle to send `is_open` instead of `is_active`
- Update the response handler to read `is_open` instead of `is_active`

---

---

## Change 2 — Delivery Zones in Place Details

### Background
Delivery zones were stored in the database but never returned in the API response. They are now included.

---

### Flutter App

#### New field in Place details

```
GET /api/mobile/places/{id}/
```

**Response now includes `delivery_zones`:**
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

**Notes:**
- `delivery_zones` can be `null` if no zones have been configured for this place
- Each zone object has two keys: `name` (String) and `price` (Number)
- `delivery_zones` only appears in the **single place details** endpoint — not in the list or nearby endpoints

**Action required:**
- On the place details / checkout screen, read `delivery_zones` and let the user pick their zone
- Use the selected zone's `price` as the delivery fee instead of the flat `delivery_price`
- If `delivery_zones` is `null` or empty → fall back to `delivery_price`

---

### Dashboard (Owner)

Delivery zones are managed via the existing endpoint:

```
PUT /api/owner/my-place/delivery-price
```

No changes needed on the dashboard side for this feature.

---

---

## Summary

| Change | Endpoint | Field | Flutter | Dashboard |
|--------|----------|-------|---------|-----------|
| Open/Close status | `GET /api/mobile/places/*` | `is_open` added | Show Closed badge | — |
| Open/Close toggle | `PUT /api/owner/my-place/status` | `is_active` → `is_open` | — | Update request body |
| Delivery zones | `GET /api/mobile/places/{id}/` | `delivery_zones` added | Read zones on checkout | — |
