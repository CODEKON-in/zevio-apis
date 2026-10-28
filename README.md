# 🚀 Zevio Backend API Documentation

Welcome to the developer documentation for the **Zevio API**. This API powers the Zevio platform, providing complete management for user profiles, merchant shops, product catalogs, and order processing.

---

## 🌐 Base URL

| Environment | URL |
| :--- | :--- |
| **Production (Live)** | `https://zevio-apis.vercel.app/` |
| **Local Development** | `http://127.0.0.1:2222/` |

---

## ⚡ Quickstart

Check if the API is active by making a request to the root endpoint (no authentication required):

```bash
curl -X GET https://zevio-apis.vercel.app/
```

**Response (`200 OK`):**
```json
{
  "status": "ok",
  "data": {
    "name": "Zevio API",
    "version": "1.0.0",
    "status": "running"
  },
  "csrf": "69baad9b469b42a12b1f85d802c295df"
}
```

---

## 🔐 Authentication

All API endpoints under `/api/*` require API Key authentication via an HTTP request header:

| Header | Value | Description |
| :--- | :--- | :--- |
| **`X-API-Key`** | `<YOUR_SECRET_API_KEY>` | Passed with every request |

### Example Authenticated Request
```bash
curl -X GET "https://zevio-apis.vercel.app/api/shops/" \
  -H "X-API-Key: YOUR_API_KEY"
```

If the key is missing or invalid, the API returns:
```json
{
  "status": "unauthorized",
  "csrf": "<token>"
}
```
*(HTTP Status: `401 Unauthorized`)*

---

## 📦 Request & Response Format

- **Content-Type**:
  - `GET` requests pass parameters in the URL query string.
  - `POST` requests accept **`multipart/form-data`** or **`application/x-www-form-urlencoded`** (form fields).
- **Standard Success Response**:
  ```json
  {
    "status": "ok",
    "csrf": "5f1b2c...",
    "data": { ... }
  }
  ```
- **Standard Error Response**:
  ```json
  {
    "status": "invalid name",
    "csrf": "5f1b2c..."
  }
  ```

---

## 📑 Table of Contents
- [👤 Users / Profiles](#-users--profiles)
- [🏪 Shops](#-shops)
- [📦 Products](#-products)
- [🛒 Orders](#-orders)
- [🧾 Order Items](#-order-items)
- [🚦 HTTP Status Codes](#-http-status-codes)
- [💻 Local Development & Deployment](#-local-development--deployment)

---

## 👤 Users / Profiles

Manage customer, shop owner, and delivery personnel accounts.

### 1. Get User Profile
Retrieves user information for a specific UUID.

- **Method**: `GET`
- **Path**: `/api/user/<uid>`
- **Headers**: `X-API-Key: YOUR_API_KEY`

```bash
curl -X GET "https://zevio-apis.vercel.app/api/user/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d" \
  -H "X-API-Key: YOUR_API_KEY"
```

---

### 2. Create User Profile
Registers a new user profile.

- **Method**: `POST`
- **Path**: `/api/user/add/`
- **Headers**: `X-API-Key: YOUR_API_KEY`
- **Form Body**:

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `uid` | String | ✅ | Unique UUID for the user |
| `name` | String | ✅ | User's full name (max 100 chars) |
| `phone` | String | ✅ | 10-digit numeric phone number |
| `user_type` | String | ✅ | One of: `customer`, `shop`, `delivery_person` |

```bash
curl -X POST "https://zevio-apis.vercel.app/api/user/add/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "uid=9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d" \
  -F "name=Alex Johnson" \
  -F "phone=9876543210" \
  -F "user_type=customer"
```

---

### 3. Update User Attribute
Updates a specific field for a user.

- **Method**: `POST`
- **Path**: `/api/user/update/`
- **Form Body**:

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `uid` | String | ✅ | User's UUID |
| `attr` | String | ✅ | Attribute to modify: `name`, `phone`, or `user_type` |
| `attr_value` | String | ✅ | New value for the specified attribute |

```bash
curl -X POST "https://zevio-apis.vercel.app/api/user/update/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "uid=9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d" \
  -F "attr=name" \
  -F "attr_value=Alexander Johnson"
```

---

### 4. Delete User Profile
Removes a user profile from the platform.

- **Method**: `POST`
- **Path**: `/api/user/delete/`
- **Form Body**: `uid` (UUID)

```bash
curl -X POST "https://zevio-apis.vercel.app/api/user/delete/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "uid=9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
```

---

## 🏪 Shops

Manage storefronts, merchant profiles, and operational statuses.

### 1. List All Shops
Returns all registered shops. Optionally filter by city.

- **Method**: `GET`
- **Path**: `/api/shops/`
- **Query Params**:
  - `city` *(optional)*: Filter shops by city name (e.g. `?city=Mumbai`)

```bash
# All shops
curl -X GET "https://zevio-apis.vercel.app/api/shops/" \
  -H "X-API-Key: YOUR_API_KEY"

# Filter by city
curl -X GET "https://zevio-apis.vercel.app/api/shops/?city=Mumbai" \
  -H "X-API-Key: YOUR_API_KEY"
```

---

### 2. Get Shop Details
Fetch shop information using either ID or unique URL slug.

```bash
# By ID
GET /api/shop/<shop_id>

# By Slug
GET /api/shop/slug/<slug>
```

```bash
curl -X GET "https://zevio-apis.vercel.app/api/shop/slug/fresh-mart" \
  -H "X-API-Key: YOUR_API_KEY"
```

---

### 3. List Shops by Owner Profile
Returns all stores associated with a specific profile UUID.

- **Method**: `GET`
- **Path**: `/api/shops/by-profile/<profile_id>`

---

### 4. Register a New Shop
Creates a new merchant store.

- **Method**: `POST`
- **Path**: `/api/shop/add/`
- **Form Body**:

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `profile_id` | String | ✅ | Owner's UUID |
| `shop_name` | String | ✅ | Store name (max 100 chars) |
| `slug` | String | ✅ | URL-friendly slug (lowercase, numbers, hyphens) |
| `contact_phone` | String | ✅ | 10-digit phone number |
| `contact_email` | String | ✅ | Valid email address |
| `city` | String | ✅ | City name (max 100 chars) |
| `description` | String | ❌ | Store description (max 1000 chars) |
| `logo_url` | String | ❌ | URL to store logo image |
| `cover_image_url` | String | ❌ | URL to storefront cover banner |
| `address` | String | ❌ | Physical address (max 500 chars) |

```bash
curl -X POST "https://zevio-apis.vercel.app/api/shop/add/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "profile_id=9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d" \
  -F "shop_name=Fresh Bakery" \
  -F "slug=fresh-bakery" \
  -F "contact_phone=9876543210" \
  -F "contact_email=hello@freshbakery.com" \
  -F "city=Mumbai" \
  -F "address=12 MG Road"
```

---

### 5. Update Shop Details
- **Method**: `POST`
- **Path**: `/api/shop/update/`
- **Form Fields**:
  - `shop_id` (UUID)
  - `attr`: `shop_name`, `description`, `logo_url`, `cover_image_url`, `contact_phone`, `contact_email`, `address`, or `city`
  - `attr_value`: New value

---

### 6. Toggle Order Acceptance
Open or pause incoming orders for a shop.

- **Method**: `POST`
- **Path**: `/api/shop/toggle-orders/`
- **Form Fields**:
  - `shop_id`: Shop's UUID
  - `status`: `"true"` (accepting orders) or `"false"` (paused)

---

### 7. Delete Shop
Permanently removes a shop and cascadingly deletes all its products.

- **Method**: `POST`
- **Path**: `/api/shop/delete/`
- **Form Fields**: `shop_id` (UUID)

---

## 📦 Products

Manage inventory, pricing, and availability.

### 1. Get Product
```bash
# By Product ID
GET /api/product/<product_id>

# By Product Slug
GET /api/product/slug/<slug>
```

---

### 2. List Products by Shop
- **Method**: `GET`
- **Path**: `/api/products/by-shop/<shop_id>`
- **Query Params**:
  - `available`: Pass `true` to return only in-stock items (`?available=true`)

```bash
curl -X GET "https://zevio-apis.vercel.app/api/products/by-shop/e0c94da8-d5e1-4b19-9134-2e91295b9542?available=true" \
  -H "X-API-Key: YOUR_API_KEY"
```

---

### 3. Add Product
- **Method**: `POST`
- **Path**: `/api/product/add/`
- **Form Body**:

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `shop_id` | String | ✅ | Store UUID |
| `name` | String | ✅ | Product name (max 200 chars) |
| `slug` | String | ✅ | Lowercase slug (`choco-cake`) |
| `price` | Number | ✅ | Unit price (non-negative float) |
| `description` | String | ❌ | Details (max 1000 chars) |
| `image_url` | String | ❌ | Image URL |
| `is_available` | String | ❌ | `"true"` (default) or `"false"` |

---

### 4. Update Product & Availability
```bash
# Update field (name, description, price, image_url, slug)
POST /api/product/update/
Fields: product_id, attr, attr_value

# Toggle availability
POST /api/product/toggle-availability/
Fields: product_id, status ("true" | "false")

# Delete product
POST /api/product/delete/
Fields: product_id
```

---

## 🛒 Orders

Handle customer checkouts, status transitions, and order histories.

### Order Status Lifecycle
```text
pending  ──►  confirmed  ──►  preparing  ──►  out_for_delivery  ──►  delivered
   │
   └──►  cancelled
```

---

### 1. Place a New Order
Creates an order along with its line items in a single atomic operation.

- **Method**: `POST`
- **Path**: `/api/order/place/`
- **Form Body**:

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `customer_id` | String | ✅ | Customer UUID |
| `shop_id` | String | ✅ | Merchant UUID |
| `recipient_name` | String | ✅ | Full name of recipient |
| `recipient_phone` | String | ✅ | 10-digit phone number |
| `delivery_address`| String | ✅ | Street address |
| `delivery_city` | String | ✅ | City name |
| `delivery_postal_code`| String | ❌ | Postal / PIN code |
| `subtotal` | Number | ✅ | Total sum of items |
| `delivery_fee` | Number | ❌ | Delivery fee (default: `0`) |
| `discount_amount`| Number | ❌ | Discounts applied (default: `0`) |
| `total_amount` | Number | ✅ | Grand total (`subtotal + fee - discount`) |
| `items` | JSON String | ✅ | Array of ordered items (see format below) |

#### Format of `items` parameter:
```json
[
  {
    "product_id": "c1f1f2e0-24db-4fbc-bdf8-6c303f8a0c20",
    "product_name": "Paneer Butter Masala",
    "unit_price": 240.0,
    "quantity": 2
  },
  {
    "product_name": "Butter Naan",
    "unit_price": 40.0,
    "quantity": 3
  }
]
```

#### Example cURL:
```bash
curl -X POST "https://zevio-apis.vercel.app/api/order/place/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "customer_id=9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d" \
  -F "shop_id=e0c94da8-d5e1-4b19-9134-2e91295b9542" \
  -F "recipient_name=Alex Johnson" \
  -F "recipient_phone=9876543210" \
  -F "delivery_address=Apartment 4B, Sunset Boulevard" \
  -F "delivery_city=Mumbai" \
  -F "subtotal=600" \
  -F "delivery_fee=40" \
  -F "total_amount=640" \
  -F 'items=[{"product_name":"Burger","unit_price":200,"quantity":3}]'
```

**Success Response (`201 Created`):**
```json
{
  "status": "ok",
  "data": {
    "order_id": "a98df241-11ee-45f8-8bb5-5fa8619bc2e1",
    "order_number": "ZV-7C12DF4A"
  },
  "csrf": "6f2e8..."
}
```

---

### 2. Tracking Orders
```bash
# Get Order by ID
GET /api/order/<order_id>

# Get Order by Human-Readable Order Number (e.g. ZV-7C12DF4A)
GET /api/order/number/<order_number>

# Get Orders by Customer
GET /api/orders/by-customer/<customer_id>?status=pending

# Get Orders by Shop
GET /api/orders/by-shop/<shop_id>?status=confirmed

# Get Order Line Items
GET /api/order/<order_id>/items/
```

---

### 3. Update Order Status
Transition the status as the order progresses:

- **Method**: `POST`
- **Path**: `/api/order/update-status/`
- **Fields**: `order_id`, `status` (`pending` · `confirmed` · `preparing` · `out_for_delivery` · `delivered` · `cancelled`)

---

### 4. Cancel or Delete Order
```bash
# Cancel an order
POST /api/order/cancel/
Fields: order_id

# Delete an order (removes order and all items)
POST /api/order/delete/
Fields: order_id
```

---

## 🧾 Order Items

Modify individual items inside an existing order:

```bash
# Add line item
POST /api/order/item/add/
Fields: order_id, product_name, unit_price, quantity, product_id (optional)

# Remove line item
POST /api/order/item/delete/
Fields: item_id
```

---

## 🚦 HTTP Status Codes

| Code | Status | Meaning |
| :---: | :--- | :--- |
| **`200`** | OK | Request was successful and returned data |
| **`201`** | Created | Resource successfully created (User, Shop, Product, Order) |
| **`400`** | Bad Request | Missing or invalid input parameter/validator error |
| **`401`** | Unauthorized | Missing or incorrect `X-API-Key` header |
| **`404`** | Not Found | Requested resource ID or route does not exist |
| **`500`** | Internal Server Error | Server-side execution or database error |

---

## 💻 Local Development & Deployment

### 1. Clone & Setup Locally
```bash
# Clone the repository
git clone https://github.com/CODEKON-in/zevio-apis.git
cd zevio-apis

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Secrets
Create a `secrets.env` file in the project root:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your_supabase_service_role_key
API_KEY=your_secure_api_key
```

### 3. Run Locally
```bash
python3 main.py
```
The server will start at `http://127.0.0.1:2222`.

### 4. Vercel Deployment
This project is configured with zero configuration for Vercel Serverless Functions:
1. Import your GitHub repository into [Vercel](https://vercel.com).
2. Under **Project Settings → Environment Variables**, add:
   - `SUPABASE_URL`
   - `SUPABASE_SECRET_KEY`
   - `API_KEY`
3. Click **Deploy**. Vercel will automatically detect `main.py` and run your Flask application globally at `https://zevio-apis.vercel.app/`.
