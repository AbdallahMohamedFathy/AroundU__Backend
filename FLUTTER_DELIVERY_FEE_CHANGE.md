# API Change — Delivery Fee in Orders

## What changed

The order response now includes `delivery_fee` as a separate field.

`total_price` = items total + delivery fee (already calculated on the backend).

---

## Affected Endpoints

```
POST /api/user/orders/checkout
GET  /api/user/orders/my
GET  /api/user/orders/{id}
```

---

## New Response Structure

```json
{
  "id": 12,
  "status": "PENDING",
  "order_type": "CASH_ON_DELIVERY",
  "delivery_fee": 20.0,
  "total_price": 190.0,
  "items": [
    {
      "item_name": "Burger",
      "unit_price": 85.0,
      "quantity": 2,
      "total_price": 170.0
    }
  ]
}
```

---

## Logic

| Order Type | Delivery Fee |
|------------|-------------|
| `CASH_ON_DELIVERY` | `place.delivery_price` (or `0` if free delivery) |
| `TAKE_AWAY` | `0` |

---

## Action Required

- Show `delivery_fee` as a separate line in the order summary screen
- Show `total_price` as the final total (no need to recalculate on the Flutter side)
- If `delivery_fee == 0` and order type is delivery → show **"Free Delivery"**

---

> **Note:** Existing orders in the DB will have `delivery_fee = 0` — this only applies to new orders placed after the update.
