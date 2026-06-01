# Sub-Items Feature — Dashboard Team Guide

## What Changed

Owners can now add **sub-items (variants)** to any item (e.g. sizes S / M / L / XL).  
Each sub-item has its own name, price, description, and availability toggle.

All endpoints require **Owner or Admin** JWT token (`Authorization: Bearer <token>`).

---

## New Endpoints

Base prefix: `/api/v1/items`

### 1. Create Sub-Item
```
POST /api/v1/items/{item_id}/sub-items
```
**Who:** Owner (of the item's place) or Admin

**Request body:**
```json
{
  "name": "L",
  "description": "Large size",
  "price": 95.00,
  "is_available": true
}
```
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | ✅ | Max 255 chars. Must be unique per item |
| `price` | number | ✅ | Must be > 0 |
| `description` | string | ❌ | Optional |
| `is_available` | bool | ❌ | Default: `true` |

**Response `201`:** SubItemResponse (see schema below)

---

### 2. Update Sub-Item
```
PUT /api/v1/items/sub-items/{sub_item_id}
```
**Who:** Owner (of the item's place) or Admin

**Request body (all fields optional):**
```json
{
  "name": "XL",
  "price": 110.00,
  "is_available": true
}
```
**Response `200`:** SubItemResponse

---

### 3. Delete Sub-Item
```
DELETE /api/v1/items/sub-items/{sub_item_id}
```
**Who:** Owner (of the item's place) or Admin

**Response `204`:** No content (soft delete)

---

### 4. Toggle Availability
```
PATCH /api/v1/items/sub-items/{sub_item_id}/availability
```
**Who:** Owner or Admin

**Response `200`:** SubItemResponse with updated `is_available`

---

## SubItemResponse Schema

```json
{
  "id": 10,
  "name": "M",
  "description": null,
  "price": "75.00",
  "is_available": true,
  "item_id": 1,
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": null
}
```

---

## Sub-Items in Item Response

All item GET endpoints now return `sub_items` list inside each item.  
The dashboard item list/detail already shows variants — no extra endpoint needed.

---

## Permissions Summary

| Action | Owner | Admin |
|--------|-------|-------|
| Create sub-item | ✅ (own items only) | ✅ |
| Update sub-item | ✅ (own items only) | ✅ |
| Delete sub-item | ✅ (own items only) | ✅ |
| Toggle availability | ✅ (own items only) | ✅ |
| View sub-items | ✅ | ✅ |

> An Owner can only manage sub-items for items that belong to **their own place**.
