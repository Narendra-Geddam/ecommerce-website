# E-Commerce Application - Daily Improvements

Work on one improvement per day. Mark completed items with ✅.

---

## 🔴 High Priority (Security Critical)

- [x] **1. Fix Password Hashing** - Replace SHA256 with bcrypt/argon2 in `application/app.py`
- [x] **2. Add Observability/Monitoring** - Create `/monitor` dashboard to visualize K8s deployment, request flow, pod status, service communication for learning containerization
- [ ] **3. Remove Hardcoded Secrets** - Use environment variables for SECRET_KEY and database credentials
- [ ] **4. Add CSRF Protection** - Implement Flask-WTF CSRF tokens for all POST endpoints
- [ ] **5. Fix XSS Vulnerabilities** - Sanitize/escape user data in JavaScript template literals
- [ ] **6. Add Rate Limiting** - Implement rate limiting on login endpoint to prevent brute force
- [ ] **7. Add Security Headers** - Configure X-Frame-Options, CSP, HSTS in nginx.conf

---

## 🟡 Medium Priority (Functionality)

- [ ] **8. Database Connection Pooling** - Use psycopg2.pool instead of creating new connections per request
- [ ] **9. Add Transaction Management** - Wrap order creation in proper database transactions
- [ ] **10. Stock Validation** - Validate stock before orders and decrement stock after purchase
- [ ] **11. Add Pagination** - Implement pagination for /products endpoint
- [ ] **12. Input Validation** - Add email format, password strength, and phone validation
- [ ] **13. Add Database Indexes** - Add indexes on products.category, products.name, orders.user_id

---

## 🟢 Low Priority (Enhancements)

- [ ] **14. Add Testing** - Create unit tests, integration tests, and e2e tests
- [ ] **15. Fix README.md** - Update documentation to reflect PostgreSQL instead of SQLite
- [ ] **16. API Documentation** - Add OpenAPI/Swagger specification
- [ ] **17. Production WSGI Server** - Use gunicorn instead of flask run in Dockerfile
- [ ] **18. Add HTTPS/SSL** - Configure SSL certificates for secure connections

---

## 🔵 Future Features

- [ ] **19. Password Reset** - Implement forgot password functionality
- [ ] **20. Email Verification** - Add email confirmation for new accounts
- [ ] **21. Admin Panel** - Create admin dashboard for product/order management
- [ ] **22. Product Reviews** - Add review and rating system
- [ ] **23. Wishlist** - Implement wishlist functionality
- [ ] **24. Coupon Codes** - Add discount/promo code system
- [ ] **25. Order Cancellation** - Allow users to cancel/refund orders
- [ ] **26. Inventory Management** - Full stock management system

---

## Progress Tracking

| Date | Item # | Description | Notes |
|------|--------|-------------|-------|
| 2026-03-16 | 1 | Fix Password Hashing | Replaced SHA256 with bcrypt for secure password storage |
| 2026-03-16 | 2 | Add Observability/Monitoring | Created /monitor dashboard with request tracking, service status, and endpoint metrics |

---

## Quick Commands

```bash
# Restart containers after changes
docker-compose down -v && docker-compose up --build

# View backend logs
docker-compose logs -f backend

# View database logs
docker-compose logs -f db
```