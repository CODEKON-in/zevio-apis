# zevio-apis

Backend REST API for the **Zevio** platform — built with **Python (Flask)** and **Supabase**.

---

## Setup

1. **Install dependencies**
   ```bash
   pip install flask supabase python-dotenv
   ```

2. **Create `secrets.env`** in the project root:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_SECRET_KEY=your_supabase_service_role_key
   API_KEY=your_secret_api_key
   ```

3. **Run the server**
   ```bash
   python main.py
   ```
   Server starts at `http://0.0.0.0:2222`

---

## Authentication

Every request **must** include the API key in the request header:

```
X-API-Key: your_secret_api_key
```

Missing or invalid key returns:
```json
{ "status": "unauthorized", "csrf": "..." }
```

---

## Response Format

All responses follow this structure:

```json
{
  "status": "ok",
  "csrf": "random_hex_token",
  "data": { }
}
```

| Field | Description |
|-------|-------------|
| `status` | `"ok"` on success, or an error message string |
| `csrf` | A fresh random token returned on every response |
| `data` | Present only when the endpoint returns data |

---

## Endpoints

### 👤 User / Profile

---

#### `GET /api/user/<uid>`
Fetch a user profile by their UUID.

**Path param:**
| Param | Type | Description |
|-------|------|-------------|
| `uid` | UUID | The user's unique ID |

**Success response:**
```json
{
  "status": "ok",
  "csrf": "...",
  "data": {
    "id": "uuid",
    "name": "Mohamed",
    "phone": "9876543210",
    "user_type": "shop"
  }
}
```

---

#### `POST /api/user/add/`
Create a new user profile.

**Form fields:**
| Field | Required | Validation |
|-------|----------|------------|
| `uid` | ✅ | Valid UUID |
| `name` | ✅ | Max 100 chars |
| `phone` | ✅ | 10-digit number |
| `user_type` | ✅ | `customer`, `shop`, or `delivery_person` |

**Success:** `201`

---

#### `POST /api/user/update/`
Update a single field of a user profile.

**Form fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `uid` | ✅ | User's UUID |
| `attr` | ✅ | Field to update: `name`, `phone`, `user_type` |
| `attr_value` | ✅ | New value (validated per field) |

---

#### `POST /api/user/delete/`
Delete a user profile.

**Form fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `uid` | ✅ | User's UUID |

---

### 🏪 Shops

---

#### `GET /api/shops/`
Get all shops. Optionally filter by city.

**Query param:**
| Param | Required | Description |
|-------|----------|-------------|
| `city` | ❌ | Filter shops by city name |

**Example:** `GET /api/shops/?city=Chennai`

---

#### `GET /api/shop/<shop_id>`
Get a single shop by its UUID.

---

#### `GET /api/shop/slug/<slug>`
Get a shop by its slug.

**Example:** `GET /api/shop/slug/my-bakery`

---

#### `GET /api/shops/by-profile/<profile_id>`
Get all shops owned by a profile (user).

---

#### `POST /api/shop/add/`
Create a new shop.

**Form fields:**
| Field | Required | Validation |
|-------|----------|------------|
| `profile_id` | ✅ | Valid UUID |
| `shop_name` | ✅ | Max 100 chars |
| `slug` | ✅ | Lowercase, letters/numbers/hyphens only |
| `description` | ❌ | Max 1000 chars |
| `logo_url` | ❌ | Max 500 chars |
| `cover_image_url` | ❌ | Max 500 chars |
| `contact_phone` | ✅ | 10-digit number |
| `contact_email` | ✅ | Valid email format |
| `address` | ❌ | Max 500 chars |
| `city` | ✅ | Max 100 chars |

**Success:** `201`

---

#### `POST /api/shop/update/`
Update a single field of a shop.

**Form fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `shop_id` | ✅ | Shop's UUID |
| `attr` | ✅ | Field: `shop_name`, `description`, `logo_url`, `cover_image_url`, `contact_phone`, `contact_email`, `address`, `city` |
| `attr_value` | ✅ | New value |

---

#### `POST /api/shop/toggle-orders/`
Enable or disable order acceptance for a shop.

**Form fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `shop_id` | ✅ | Shop's UUID |
| `status` | ✅ | `"true"` or `"false"` |

---

#### `POST /api/shop/delete/`
Delete a shop and all its products.

**Form fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `shop_id` | ✅ | Shop's UUID |

---

### 📦 Products

---

#### `GET /api/product/<product_id>`
Get a single product by its UUID.

---

#### `GET /api/product/slug/<slug>`
Get a product by its slug.

---

#### `GET /api/products/by-shop/<shop_id>`
Get all products belonging to a shop.

**Query param:**
| Param | Required | Description |
|-------|----------|-------------|
| `available` | ❌ | `true` to return only available products |

**Example:** `GET /api/products/by-shop/<shop_id>?available=true`

---

#### `POST /api/product/add/`
Add a new product to a shop.

**Form fields:**
| Field | Required | Validation |
|-------|----------|------------|
| `shop_id` | ✅ | Valid UUID |
| `name` | ✅ | Max 200 chars |
| `slug` | ✅ | Lowercase, letters/numbers/hyphens only |
| `description` | ❌ | Max 1000 chars |
| `price` | ✅ | Non-negative number |
| `image_url` | ❌ | Max 500 chars |
| `is_available` | ❌ | `"true"` (default) or `"false"` |

**Success:** `201`

---

#### `POST /api/product/update/`
Update a single field of a product.

**Form fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `product_id` | ✅ | Product's UUID |
| `attr` | ✅ | Field: `name`, `description`, `price`, `image_url`, `slug` |
| `attr_value` | ✅ | New value |

---

#### `POST /api/product/toggle-availability/`
Enable or disable a product's availability.

**Form fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `product_id` | ✅ | Product's UUID |
| `status` | ✅ | `"true"` or `"false"` |

---

#### `POST /api/product/delete/`
Delete a product.

**Form fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `product_id` | ✅ | Product's UUID |

---

## Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| `200` | Success |
| `201` | Created successfully |
| `400` | Bad request / invalid input |
| `401` | Missing or invalid API key |
| `404` | Resource not found |
| `405` | Method not allowed |
| `500` | Internal server error |

---

## Project Structure

```
zevio-project/
├── main.py         # All API routes & security middleware
├── profile.py      # Profile table CRUD operations
├── shop.py         # Shops table CRUD operations
├── product.py      # Products table CRUD operations
├── auth.py         # Input validators & sanitizers
├── db.py           # Supabase client & table initializers
├── secrets.env     # Environment variables (not committed)
└── .gitignore
```
