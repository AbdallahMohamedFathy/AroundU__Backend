# Sub-Items Feature — Flutter Team Guide

## What Changed

Every `Item` object now includes a `sub_items` list. Sub-items are variants of an item (e.g. sizes: S, M, L, XL). The user can add either the **main item** or a **sub-item** to the cart.

---

## Updated Item Response

All existing item endpoints now return `sub_items` inside each item:

```json
{
  "id": 1,
  "name": "تشيز كيك",
  "description": "...",
  "price": "75.00",
  "image_url": "https://...",
  "is_available": true,
  "sub_category_id": 3,
  "subcategory_name": "Desserts",
  "sub_items": [
    {
      "id": 10,
      "name": "S",
      "description": null,
      "price": "50.00",
      "is_available": true,
      "item_id": 1,
      "created_at": "2026-06-01T00:00:00Z",
      "updated_at": null
    },
    {
      "id": 11,
      "name": "M",
      "description": null,
      "price": "75.00",
      "is_available": true,
      "item_id": 1,
      "created_at": "2026-06-01T00:00:00Z",
      "updated_at": null
    },
    {
      "id": 12,
      "name": "L",
      "description": null,
      "price": "95.00",
      "is_available": true,
      "item_id": 1,
      "created_at": "2026-06-01T00:00:00Z",
      "updated_at": null
    }
  ],
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": null
}
```

> `sub_items` returns an **empty list `[]`** if the item has no variants — no null checks needed.

---

## UI Logic

| Condition | Behaviour |
|-----------|-----------|
| `sub_items` is empty | Show item directly with its price, user adds it to cart as-is |
| `sub_items` has items | Show variant selector (S / M / L …), user picks one before adding to cart |
| Sub-item `is_available: false` | Show it as greyed out / disabled |

---

## Affected Endpoints (no URL changes)

All these endpoints already return the new `sub_items` field — no extra calls needed:

| Endpoint | Tag |
|----------|-----|
| `GET /api/mobile/items/place/{place_id}` | Mobile - Items |
| `GET /api/mobile/items/place/{place_id}/top` | Mobile - Items |
| `GET /api/v1/items` | Items |
| `GET /api/v1/items/subcategory/{subcategory_id}` | Items |

---

## Cart Integration (when implemented)

When adding to cart, send either:
- `item_id` only → user chose the main item
- `item_id` + `sub_item_id` → user chose a variant

```json
{
  "item_id": 1,
  "sub_item_id": 11,
  "quantity": 2
}
```
