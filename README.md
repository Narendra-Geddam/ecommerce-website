# ShopEasy E-Commerce Platform

ShopEasy is a Docker-based e-commerce demo that now runs on a microservices-oriented local stack with a legacy Flask app still present during migration.

## Stack

- `presentation` (`http://localhost`) serves the storefront with Nginx
- `gateway` (`http://localhost/api/...`) routes API traffic and handles auth context, CSRF, rate limiting, and headers
- `auth-service` manages registration, login, JWTs, and profiles
- `product-service` serves products, categories, filtering, and pagination
- `cart-service` supports guest carts and authenticated carts
- `order-service` handles order creation and order history
- `inventory-service` manages inventory tables and stock-related flows
- `application` (`http://localhost:5050`) is the legacy Flask monolith kept for migration/monitoring work
- `database` is PostgreSQL 15
- `redis` is used for rate limiting, token blacklisting, and shared runtime support

## Current Highlights

- Guest browsing and guest cart flow work through the gateway
- Login/register store JWTs and support guest cart merge after auth
- Checkout, orders, and profile flows are wired to the microservices stack
- CSRF protection, rate limiting, XSS hardening, and security headers are in place
- Product and order APIs support pagination
- Live API smoke tests are available with `pytest`
- Python services run under `gunicorn` in Docker

## Project Layout

```text
.
├── application/          # Legacy Flask monolith
├── data/                 # Shared and service-specific PostgreSQL init SQL
├── infrastructure/       # Redis config and related infra assets
├── k8s/                  # Kubernetes manifests
├── presentation/         # Nginx frontend and static HTML pages
├── services/             # Gateway + microservices + shared libraries
├── tests/                # Live API smoke tests
├── docker-compose.yml
├── .env.example
├── CLAUDE.md             # Improvement tracker
└── KILO.md               # Daily progress tracker
```

## Prerequisites

- Docker Desktop or Docker Engine with Compose support
- Git

## Environment Setup

Copy the sample env file and adjust values if needed:

```bash
cp .env.example .env
```

Important variables:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `SECRET_KEY`
- `REDIS_URL`

## Running The Stack

Start everything:

```bash
docker compose up -d --build
```

Stop everything:

```bash
docker compose down
```

Reset containers and volumes:

```bash
docker compose down -v
docker compose up -d --build
```

## Main URLs

- Storefront: `http://localhost/`
- Cart: `http://localhost/cart.html`
- Checkout: `http://localhost/checkout.html`
- Orders: `http://localhost/orders.html`
- Profile: `http://localhost/profile.html`
- Admin panel: `http://localhost/admin.html`
- Wishlist: `http://localhost/wishlist.html`
- Monitoring dashboard: `http://localhost/monitor`
- Legacy app: `http://localhost:5050`

## Admin Access

The admin panel is available at:

```text
http://localhost/admin.html
```

How to access it:

1. Register or log in with the admin email `admin@shopeasy.local`
2. Use the normal storefront login page at `http://localhost/login.html`
3. After login, open `http://localhost/admin.html`
4. The homepage account menu will also show an `Admin Panel` link for admin users

Notes:

- Admin access is determined by the JWT `is_admin` claim
- The default local admin email is `admin@shopeasy.local`
- The admin email list is controlled by the `ADMIN_EMAILS` environment variable in Docker/runtime config

## Admin Features

The current admin panel supports:

- viewing recent orders
- updating order status
- viewing inventory rows
- viewing low-stock products
- restocking inventory
- syncing missing inventory rows from products
- creating new products
- editing product details and stock-linked catalog data
- archiving products without breaking order history
- viewing users and banning/deactivating accounts
- creating and deleting homepage banners
- creating and deleting homepage offer cards
- creating and deleting coupon codes

## Admin Portal Workflows

The admin portal at `http://localhost/admin.html` is now intended to be the store-owner control center, not a customer-style page.

Main workflows:

- `Homepage Banner Studio`
  - upload a banner image directly from the admin panel
  - write banner title, subtitle, badge text, colors, sort order, and target link
  - publish or hide the banner for all storefront users
  - active banners appear in the public homepage slideshow
- `Product Catalog`
  - create products
  - edit product title, description, category, image path, price, stock, and active status
  - archive products without deleting order history
- `Offers and Coupons`
  - create/edit/delete homepage offer cards from admin
  - create/edit/delete coupon codes from admin
  - coupon usage is intended for checkout or manual mention inside banner text
- `Orders Control`
  - update order status
  - cancel eligible orders from admin
- `Inventory Desk`
  - restock products
  - sync missing inventory rows
  - review low-stock items
- `Users and Access`
  - ban/unban users
  - activate/deactivate users

## Homepage Content Rules

Current storefront behavior:

- the public homepage hero banner is admin-managed
- banner images uploaded from admin are served from `presentation/static/uploads/`
- the old homepage offer-card strip below the hero banner has been removed
- coupon codes should not be promoted in that removed homepage strip
- if admins want to announce a festive coupon or promotion on the homepage, they should place it manually inside banner content
- the actual coupon application flow belongs in checkout

This keeps the homepage cleaner and makes banners the main marketing surface for announcements, seasonal offers, and welcome campaigns.

## Unified Admin Portal

The control-center style admin UI is available at:

```text
http://localhost/admin.html
```

It is designed as a single place to manage the store across these areas:

- dashboard and low-stock watchlist
- product catalog management
- user moderation
- homepage banners and offer cards
- coupon management
- order status management
- inventory operations

Homepage content is now partially CMS-driven:

- `GET /api/homepage/content` returns active banners and offer cards
- the storefront homepage reads this content and renders live admin-managed sections

Current scope:

- This is a strong MVP control center for the existing ShopEasy architecture
- It is not yet a full Amazon/Flipkart-scale back office with analytics, seller onboarding, returns workflows, ad bidding, or advanced merchandising rules
- The next natural expansion would be richer product editing, review moderation, user search/filter tools, dashboard analytics, and media management

The current storefront/admin feature set also includes:

- product reviews and ratings
- wishlist management
- coupon validation and discounted checkout
- user-side order cancellation with stock restoration

## Product And Inventory Management Status

Current status:

- You can already update stock quantities from the admin panel
- You can restock products and sync inventory records
- You can manage order statuses
- You cannot yet create new products, edit product details, upload product images, or delete/archive products from the admin panel

Yes, we can add full product management next.

That next step would typically include:

- create new products
- edit product name, price, description, category, image, and stock
- archive or delete products
- manage inventory from the same admin workflow
- optionally add coupon management and review moderation to the admin panel

## Main API Endpoints

Full gateway OpenAPI spec:

- `docs/openapi.yaml`

Gateway-backed endpoints:

- `GET /api/me`
- `POST /api/register`
- `POST /api/login`
- `POST /api/logout`
- `PUT /api/profile`
- `GET /api/products`
- `GET /api/categories`
- `GET /api/cart`
- `POST /api/cart/add/<id>`
- `POST /api/cart/remove/<id>`
- `POST /api/cart/clear`
- `POST /api/cart/merge`
- `GET /api/orders`
- `POST /api/orders`
- `GET /api/csrf-token`
- `GET /api/products/<id>/reviews`
- `POST /api/products/<id>/reviews`
- `GET /api/wishlist`
- `POST /api/wishlist/add/<id>`
- `POST /api/wishlist/remove/<id>`
- `GET /api/coupons/validate`
- `POST /api/orders/<id>/cancel`
- `GET /api/admin/orders`
- `PUT /api/admin/orders/<id>/status`
- `GET /api/admin/users`
- `PUT /api/admin/users/<id>/status`
- `GET /api/admin/products`
- `POST /api/admin/products`
- `PUT /api/admin/products/<id>`
- `DELETE /api/admin/products/<id>`
- `GET /api/admin/coupons`
- `POST /api/admin/coupons`
- `PUT /api/admin/coupons/<id>`
- `DELETE /api/admin/coupons/<id>`
- `GET /api/admin/inventory`
- `GET /api/admin/inventory/low-stock`
- `POST /api/admin/inventory/restock`
- `POST /api/admin/inventory/sync`
- `GET /api/admin/homepage/banners`
- `POST /api/admin/homepage/banners`
- `PUT /api/admin/homepage/banners/<id>`
- `DELETE /api/admin/homepage/banners/<id>`
- `GET /api/admin/homepage/offers`
- `POST /api/admin/homepage/offers`
- `PUT /api/admin/homepage/offers/<id>`
- `DELETE /api/admin/homepage/offers/<id>`

Legacy endpoints still exist on the monolith at `http://localhost:5050`, including:

- `GET /products`
- `GET /categories`
- `POST /api/register`
- `POST /api/login`

## Monitoring

The monitoring dashboard is available at:

```text
http://localhost/monitor
```

It surfaces:

- recent request history
- request timing
- service health
- container/runtime overview

## Database Notes

- PostgreSQL is the source of truth for users, products, orders, carts, and inventory
- Init scripts live in `data/`
- The shared schema in `data/schema.sql` now includes indexes for:
  - `products.category`
  - `products.name`
  - `orders.user_id`

## Testing

A lightweight live API smoke suite is included.

Run it against the active Docker stack with a disposable Python container:

```bash
docker run --rm --network demo_ecommerce-network -v "${PWD}:/workspace" -w /workspace python:3.11-slim sh -lc "pip install --no-cache-dir -r requirements-test.txt && pytest"
```

What it currently covers:

- guest auth state
- product pagination response shape
- registration validation
- register + auth flow
- guest cart round-trip

## Useful Docker Commands

Show service status:

```bash
docker compose ps
```

Tail logs:

```bash
docker compose logs -f gateway
docker compose logs -f auth-service
docker compose logs -f order-service
docker compose logs -f presentation
```

Rebuild selected services:

```bash
docker compose up -d --build gateway auth-service order-service presentation
```

Open a database shell:

```bash
docker compose exec database psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

## Migration Status

The repository is in a transition state:

- core storefront traffic uses the gateway and microservices
- the legacy Flask app is still present for compatibility and monitoring work
- product and order functionality exist in both legacy and service-oriented forms during migration

See `CLAUDE.md` and `KILO.md` in the repo for the current improvement roadmap and progress notes.
