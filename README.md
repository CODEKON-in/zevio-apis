# Zevio API Reference

> All requests require the header: **`X-API-Key: <your_key>`**

All responses return:
```json
{ "status": "ok", "csrf": "<token>", "data": { } }
```
`data` is only present on GET responses. On error, `status` contains the error message.

---

## 👤 Users

### Get User
```
GET /api/user/<uid>
```
Returns profile data for the given user UUID.

---

### Create User
```
POST /api/user/add/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `uid` | ✅ | Valid UUID |
| `name` | ✅ | Max 100 chars |
| `phone` | ✅ | 10-digit number |
| `user_type` | ✅ | `customer` · `shop` · `delivery_person` |

---

### Update User
```
POST /api/user/update/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `uid` | ✅ | User's UUID |
| `attr` | ✅ | `name` · `phone` · `user_type` |
| `attr_value` | ✅ | New value for the chosen field |

---

### Delete User
```
POST /api/user/delete/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `uid` | ✅ | User's UUID |

---

## 🏪 Shops

### Get All Shops
```
GET /api/shops/
GET /api/shops/?city=Chennai
```
Returns all shops. Pass `city` query param to filter by city.

---

### Get Shop by ID
```
GET /api/shop/<shop_id>
```

---

### Get Shop by Slug
```
GET /api/shop/slug/<slug>
```
Example: `GET /api/shop/slug/my-bakery`

---

### Get Shops by Owner
```
GET /api/shops/by-profile/<profile_id>
```
Returns all shops belonging to a specific user profile.

---

### Create Shop
```
POST /api/shop/add/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `profile_id` | ✅ | Owner's UUID |
| `shop_name` | ✅ | Max 100 chars |
| `slug` | ✅ | Lowercase letters, numbers & hyphens only |
| `contact_phone` | ✅ | 10-digit number |
| `contact_email` | ✅ | Valid email |
| `city` | ✅ | Max 100 chars |
| `description` | ❌ | Max 1000 chars |
| `logo_url` | ❌ | Image URL |
| `cover_image_url` | ❌ | Image URL |
| `address` | ❌ | Max 500 chars |

---

### Update Shop
```
POST /api/shop/update/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `shop_id` | ✅ | Shop's UUID |
| `attr` | ✅ | `shop_name` · `description` · `logo_url` · `cover_image_url` · `contact_phone` · `contact_email` · `address` · `city` |
| `attr_value` | ✅ | New value |

---

### Toggle Order Acceptance
```
POST /api/shop/toggle-orders/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `shop_id` | ✅ | Shop's UUID |
| `status` | ✅ | `"true"` to accept orders · `"false"` to pause |

---

### Delete Shop
```
POST /api/shop/delete/
```
> ⚠️ Also deletes **all products** belonging to this shop.

| Field | Required | Notes |
|-------|:--------:|-------|
| `shop_id` | ✅ | Shop's UUID |

---

## 📦 Products

### Get Product by ID
```
GET /api/product/<product_id>
```

---

### Get Product by Slug
```
GET /api/product/slug/<slug>
```

---

### Get Products by Shop
```
GET /api/products/by-shop/<shop_id>
GET /api/products/by-shop/<shop_id>?available=true
```
Pass `available=true` to return only products that are currently available.

---

### Add Product
```
POST /api/product/add/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `shop_id` | ✅ | Shop's UUID |
| `name` | ✅ | Max 200 chars |
| `slug` | ✅ | Lowercase letters, numbers & hyphens only |
| `price` | ✅ | Non-negative number |
| `description` | ❌ | Max 1000 chars |
| `image_url` | ❌ | Image URL |
| `is_available` | ❌ | `"true"` (default) · `"false"` |

---

### Update Product
```
POST /api/product/update/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `product_id` | ✅ | Product's UUID |
| `attr` | ✅ | `name` · `description` · `price` · `image_url` · `slug` |
| `attr_value` | ✅ | New value |

---

### Toggle Product Availability
```
POST /api/product/toggle-availability/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `product_id` | ✅ | Product's UUID |
| `status` | ✅ | `"true"` to show · `"false"` to hide |

---

### Delete Product
```
POST /api/product/delete/
```
| Field | Required | Notes |
|-------|:--------:|-------|
| `product_id` | ✅ | Product's UUID |

---

## ⚡ Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `400` | Invalid input |
| `401` | Invalid or missing API key |
| `404` | Not found |
| `500` | Server error |
