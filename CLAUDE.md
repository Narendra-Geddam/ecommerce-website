# E-Commerce Application - Daily Improvements

Work on one improvement per day. Mark completed items with ✅.

---

## 🔴🔴 CRITICAL HIGH PRIORITY - Guest Checkout Flow

**PROBLEM:** Current microservices setup breaks the guest checkout flow. Users should be able to:
1. Browse products WITHOUT login
2. Add items to cart WITHOUT login
3. Place order → THEN ask to create account or login

**ISSUE DETAILS:**
- Auth endpoints return 401 for guests (should return `{"authenticated": false}` with 200)
- Cart requires JWT token (should support guest carts)
- Frontend checks auth on load and fails with HTML error

**FILES TO FIX:**
- `services/auth-service/app.py` - `/api/auth/me` must return 200 for unauthenticated users
- `services/gateway/app.py` - Cart endpoints should not require token
- `presentation/index.html` - Don't fail on auth check, show Login link always

**EXPECTED BEHAVIOR:**
```
Guest User Flow:
1. Visit homepage → See products ✓
2. Click "Add to Cart" → Cart works with guest ID ✓
3. View cart → Shows items ✓
4. Click "Checkout" → Redirect to login/register
5. After login → Cart merges, proceed to checkout
```

**STATUS:** Mostly fixed - guest browsing, guest cart, login state, checkout, order history, and guest cart merge now work through the microservices stack

**FIXES COMPLETED ON 2026-03-17:**
- Forwarded `X-Cart-ID` through `services/gateway/app.py` so guest carts persist correctly
- Updated `presentation/cart.html` to use the cart-service response shape `{ items, cart_id, total }`
- Updated `presentation/checkout.html` to use the new cart response and send `cart_id` when placing orders
- Fixed frontend auth by storing JWTs after login/register and sending `Authorization: Bearer ...` from app pages
- Updated `services/gateway/app.py` to attach authenticated user context for valid bearer tokens on optional-auth routes like `/api/me`
- Fixed `presentation/orders.html` to read `data.orders` instead of treating the full response as an array
- Added guest cart merge after login/register via `/api/cart/merge`
- Rebuilt and verified the Docker stack with live API checks for cart, auth, checkout, and orders

---

## 🔴 High Priority (Security Critical)

- [x] **1. Fix Password Hashing** - Replace SHA256 with bcrypt/argon2 in `application/app.py`
- [x] **2. Add Observability/Monitoring** - Create `/monitor` dashboard to visualize K8s deployment, request flow, pod status, service communication for learning containerization
- [x] **3. Remove Hardcoded Secrets** - Use environment variables for SECRET_KEY and database credentials
- [x] **4. Add CSRF Protection** - Implement CSRF protection for browser-driven POST/PUT/DELETE API requests
- [x] **5. Fix XSS Vulnerabilities** - Sanitize/escape user data in JavaScript template literals
- [x] **6. Add Rate Limiting** - Implement rate limiting on login endpoint to prevent brute force
- [x] **7. Add Security Headers** - Configure X-Frame-Options, CSP, HSTS in nginx.conf

---

## 🟡 Medium Priority (Functionality)

- [x] **8. Database Connection Pooling** - Use psycopg2.pool instead of creating new connections per request
- [x] **9. Add Transaction Management** - Wrap order creation in proper database transactions
- [x] **10. Stock Validation** - Validate stock before orders and decrement stock after purchase
- [x] **11. Add Pagination** - Implement pagination for /products endpoint
- [x] **12. Input Validation** - Add email format, password strength, and phone validation
- [x] **13. Add Database Indexes** - Add indexes on products.category, products.name, orders.user_id

---

## 🟢 Low Priority (Enhancements)

- [x] **14. Add Testing** - Create unit tests, integration tests, and e2e tests
- [x] **15. Fix README.md** - Update documentation to reflect PostgreSQL instead of SQLite
- [x] **16. API Documentation** - Add OpenAPI/Swagger specification
- [x] **17. Production WSGI Server** - Use gunicorn instead of flask run in Dockerfile
- [ ] **18. Add HTTPS/SSL** - Configure SSL certificates for secure connections (intentionally skipped for now)

---

## 🔵 Future Features

- [ ] **19. Password Reset** - Implement forgot password functionality (skipped by request for now)
- [ ] **20. Email Verification** - Add email confirmation for new accounts (skipped by request for now)
- [x] **21. Admin Panel** - Create admin dashboard for product/order management
- [x] **22. Product Reviews** - Add review and rating system
- [x] **23. Wishlist** - Implement wishlist functionality
- [x] **24. Coupon Codes** - Add discount/promo code system
- [x] **25. Order Cancellation** - Allow users to cancel/refund orders
- [x] **26. Inventory Management** - Full stock management system

---

## 🟣 Microservices Migration

- [x] **27. Redis Infrastructure** - Add Redis for session storage, rate limiting, token blacklisting
- [x] **28. Shared Libraries** - Create database pool, JWT handler, logging middleware
- [x] **29. API Gateway** - Create gateway with JWT validation, rate limiting, request routing
- [x] **30. Auth Service** - Extract auth endpoints to separate service with JWT tokens
- [x] **31. Database Schemas** - Create service-specific database schemas
- [ ] **32. Product Service** - Extract product endpoints with pagination and pooling
- [x] **33. Cart Service** - Create cart service with database persistence
- [x] **34. Order Service** - Extract order endpoints with transaction management
- [ ] **35. Inventory Service** - Create inventory service for stock management

---

## Progress Tracking

| Date | Item # | Description | Notes |
|------|--------|-------------|-------|
| 2026-03-16 | 1 | Fix Password Hashing | Replaced SHA256 with bcrypt for secure password storage |
| 2026-03-16 | 2 | Add Observability/Monitoring | Created /monitor dashboard with request tracking, service status, and endpoint metrics |
| 2026-03-17 | 3 | Remove Hardcoded Secrets | Moved Compose/runtime secrets to `.env`, added `.env.example`, removed hardcoded DB/JWT/Flask secret fallbacks from tracked source |
| 2026-03-17 | 4 | Add CSRF Protection | Added gateway-issued CSRF tokens, enforced `X-CSRF-Token` on mutating API calls, and updated frontend POST/PUT flows |
| 2026-03-17 | 5 | Fix XSS Vulnerabilities | Added escaping helpers for HTML/attribute rendering in product, cart, checkout, profile, and orders pages |
| 2026-03-17 | 6 | Add Rate Limiting | Centralized gateway rate limits for login/register/refresh routes and verified throttling on repeated login failures |
| 2026-03-17 | 7 | Add Security Headers | Added HSTS, permissions policy, and cross-origin protection headers in nginx and gateway responses |
| 2026-03-17 | 8 | Database Connection Pooling | Replaced legacy per-request Postgres connections with a shared threaded connection pool in `application/app.py` |
| 2026-03-17 | 9 | Add Transaction Management | Wrapped legacy order creation in an explicit transaction with rollback and only clear cart after commit |
| 2026-03-17 | 10 | Stock Validation | Added stock checks and transactional stock decrements to legacy and microservice order creation flows |
| 2026-03-17 | 11 | Add Pagination | Added page/page_size support and pagination metadata to the legacy `/products` endpoint in `application/app.py` |
| 2026-03-17 | 12 | Input Validation | Added shared email/password/phone/pincode validation to auth/order flows and matching frontend form checks |
| 2026-03-17 | 13 | Add Database Indexes | Added missing legacy/shared indexes for `products.category`, `products.name`, and `orders.user_id` in `data/schema.sql` and applied them to the live database |
| 2026-03-17 | 14 | Add Testing | Added a lightweight pytest suite for live gateway API checks covering guest auth, pagination, registration validation, auth flow, and guest cart round-trip |
| 2026-03-17 | 15 | Fix README.md | Rewrote the README to match the current Docker Compose, PostgreSQL, Redis, gateway, microservices, and testing workflow |
| 2026-03-17 | 16 | API Documentation | Added a gateway-level OpenAPI spec in `docs/openapi.yaml` covering health, auth, products, cart, orders, security headers, and request conventions |
| 2026-03-17 | 17 | Production WSGI Server | Confirmed Docker services run under `gunicorn`, removed leftover Flask-run env hints, and disabled debug mode in direct `app.run` fallbacks |
| 2026-03-17 | 21-26 | Admin, reviews, wishlist, coupons, cancellation, inventory | Added admin JWT support, admin dashboard, product reviews, wishlist flows, coupon validation/application, order cancellation with stock restore, inventory admin APIs, and verified the batch live with Docker |
| 2026-03-17 | 27-31 | Microservices Phase 1 | Added Redis, shared libraries, API Gateway, Auth Service, database schemas |
| 2026-03-17 | Guest Checkout Flow | Cart/auth/order integration fixes | Fixed guest cart persistence, login JWT handling, checkout payloads, order history parsing, and guest cart merge |
| 2026-03-18 | Admin Portal Polish | Management-style admin portal, banner image uploads, product CRUD, promo/order/inventory controls, homepage cleanup | Added upload-backed homepage banners, improved admin workflows, fixed gateway empty-body POST handling, removed homepage offer strip, and cleaned storefront category/homepage presentation |

---

## Quick Commands

```bash
# Restart containers after changes
docker-compose down -v && docker-compose up --build

# View logs for specific service
docker-compose logs -f gateway
docker-compose logs -f auth-service
docker-compose logs -f redis

# Rebuild only specific services
docker-compose build gateway auth-service

# View database logs
docker-compose logs -f database
```
