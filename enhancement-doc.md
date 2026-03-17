# E-Commerce Application Enhancement Documentation

This document tracks all security improvements and enhancements made to the e-commerce application.

---

## Completed Improvements

### ✅ 1. Password Hashing (2026-03-16)

**Priority:** 🔴 High (Security Critical)

**Problem:**
- Passwords were hashed using SHA256, which is not designed for password storage
- SHA256 is fast, making brute-force attacks feasible
- No salting mechanism, same passwords produce identical hashes

**Solution:**
- Replaced SHA256 with bcrypt password hashing
- bcrypt automatically generates unique salts for each password
- bcrypt is computationally slow by design, resisting brute-force attacks

**Files Changed:**
- `application/requirements.txt` - Added `bcrypt==4.1.2`
- `application/app.py` - Updated password hashing functions

**Code Changes:**

```python
# Before (INSECURE)
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# After (SECURE)
import bcrypt

def hash_password(password):
    """Hash password using bcrypt with automatic salt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

**Login Endpoint Update:**
- Changed from comparing hashes in SQL query to fetching stored hash and using `verify_password()`
- This is necessary because bcrypt hashes are different each time due to salt

**Migration Note:**
- Existing users will need to reset their passwords after deployment
- Old SHA256 hashes are incompatible with bcrypt verification

---

## Pending Improvements

### 🔴 High Priority (Security Critical)

#### 2. Add Observability/Monitoring Dashboard
- **Files:** New `monitoring/` service, `presentation/monitor.html`, Kubernetes configs
- **Goal:** Educational monitoring to understand Kubernetes deployment, containerization, and request flow
- **Features:**
  - `/monitor` endpoint showing real-time request tracing
  - Visual representation of service-to-service communication
  - Pod status and health for each service
  - Request latency between services (Frontend → Backend → Database)
  - Container resource usage (CPU, Memory)
  - Network topology diagram showing traffic flow
- **Purpose:** Learn K8s concepts:
  - How pods communicate
  - Service discovery
  - Load balancing
  - Container orchestration
  - Request tracing across microservices
- **Implementation Steps:**
  1. Add request ID tracking middleware
  2. Create logging service to capture request flow
  3. Build `/monitor` dashboard UI
  4. Integrate with Kubernetes metrics API
  5. Add distributed tracing (Jaeger/Zipkin or custom)

#### 3. Remove Hardcoded Secrets
- **Files:** `application/app.py`, `docker-compose.yml`
- **Issue:** SECRET_KEY and database credentials have weak default fallbacks
- **Solution:** Use environment variables with no defaults, add `.env.example`

#### 4. Add CSRF Protection
- **File:** `application/app.py`
- **Issue:** All POST endpoints vulnerable to Cross-Site Request Forgery
- **Solution:** Implement Flask-WTF CSRF tokens

#### 5. Fix XSS Vulnerabilities
- **Files:** `presentation/*.html`
- **Issue:** User-controlled data rendered without sanitization
- **Solution:** Implement HTML escaping/sanitization in JavaScript

#### 6. Add Rate Limiting
- **File:** `application/app.py`
- **Issue:** Login endpoint has no rate limiting, vulnerable to brute force
- **Solution:** Implement rate limiting with Flask-Limiter or similar

#### 7. Add Security Headers
- **File:** `presentation/nginx.conf`
- **Issue:** Missing security headers (X-Frame-Options, CSP, HSTS, etc.)
- **Solution:** Configure security headers in Nginx

---

### 🟡 Medium Priority (Functionality)

#### 8. Database Connection Pooling
- **File:** `application/app.py`
- **Issue:** New connection created per request
- **Solution:** Use `psycopg2.pool` for connection reuse

#### 9. Add Transaction Management
- **File:** `application/app.py`
- **Issue:** Order creation without transactions, risk of data inconsistency
- **Solution:** Wrap order operations in database transactions

#### 10. Stock Validation
- **File:** `application/app.py`, `data/schema.sql`
- **Issue:** Products can be ordered with 0 stock, stock never decremented
- **Solution:** Add stock check before orders, decrement on purchase

#### 11. Add Pagination
- **File:** `application/app.py`
- **Issue:** All products returned at once
- **Solution:** Implement limit/offset pagination

#### 12. Input Validation
- **File:** `application/app.py`
- **Issue:** No validation for email format, password strength, phone numbers
- **Solution:** Add server-side validation with regex patterns

#### 13. Add Database Indexes
- **File:** `data/schema.sql`
- **Issue:** Missing indexes on frequently queried columns
- **Solution:** Add indexes on category, name, user_id columns

---

### 🟢 Low Priority (Enhancements)

#### 14. Add Testing
- **Files:** New `tests/` directory
- **Solution:** Create unit tests, integration tests, e2e tests

#### 15. Fix README.md
- **Issue:** Documentation still references SQLite
- **Solution:** Update to reflect PostgreSQL architecture

#### 16. API Documentation
- **Solution:** Add OpenAPI/Swagger specification

#### 17. Production WSGI Server
- **File:** `application/Dockerfile`
- **Issue:** Uses Flask dev server
- **Solution:** Configure gunicorn properly

#### 18. Add HTTPS/SSL
- **File:** `presentation/nginx.conf`
- **Solution:** Configure SSL certificates

---

### 🔵 Future Features

#### 19. Password Reset
- Implement forgot password functionality with email

#### 20. Email Verification
- Add email confirmation for new accounts

#### 21. Admin Panel
- Create admin dashboard for product/order management

#### 22. Product Reviews
- Add review and rating system

#### 23. Wishlist
- Implement wishlist functionality

#### 24. Coupon Codes
- Add discount/promo code system

#### 25. Order Cancellation
- Allow users to cancel/refund orders

#### 26. Inventory Management
- Full stock management system

---

## Security Best Practices Applied

| Practice | Status |
|----------|--------|
| Password Hashing (bcrypt) | ✅ Done |
| Environment Variables for Secrets | ⏳ Pending |
| CSRF Protection | ⏳ Pending |
| XSS Prevention | ⏳ Pending |
| Rate Limiting | ⏳ Pending |
| Security Headers | ⏳ Pending |
| Input Validation | ⏳ Pending |
| HTTPS/SSL | ⏳ Pending |

---

## Architecture Reference

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Nginx         │────▶│   Flask         │────▶│   PostgreSQL    │
│   (Frontend)    │     │   (Backend)     │     │   (Database)    │
│   Port 80       │     │   Port 5000     │     │   Port 5432     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Kubernetes Learning Objectives

### Goal
This application is designed to learn Kubernetes deployment, containerization, and microservice communication patterns.

### Key Concepts to Understand

#### 1. Service Discovery
```
User Request Flow:
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Browser │───▶│ Nginx   │───▶│ Flask   │───▶│PostgreSQL│
│         │    │ Service │    │ Service │    │ Service │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │
     │         Pod: nginx     Pod: flask     Pod: postgres
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                          Kubernetes Cluster
```

#### 2. Request Tracing (To Be Implemented)
Each request will be tracked with a unique Request ID:
```
Request ID: req-abc123
├── [nginx-pod]     Received request    → 2ms
├── [flask-pod]     Processing API call → 15ms
├── [postgres-pod]  Query executed      → 5ms
└── Total: 22ms
```

#### 3. Pod Communication Patterns
- **Frontend (Nginx)** → Routes to Backend via Service name
- **Backend (Flask)** → Connects to Database via Service name
- **Database (PostgreSQL)** → Persists data in Volume

#### 4. Observability Dashboard (`/monitor`)
```
┌─────────────────────────────────────────────────────────────┐
│                    MONITORING DASHBOARD                      │
├─────────────────────────────────────────────────────────────┤
│ SERVICES STATUS                                              │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│ │ Nginx    │ │ Flask    │ │PostgreSQL│                     │
│ │ Running  │ │ Running  │ │ Running  │                     │
│ │ Pod: 3/3 │ │ Pod: 2/2 │ │ Pod: 1/1 │                     │
│ └──────────┘ └──────────┘ └──────────┘                     │
├─────────────────────────────────────────────────────────────┤
│ REQUEST FLOW                                                 │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ GET /products → nginx → flask → postgres → response  │   │
│ │ Time: 45ms | Status: 200 | Pod: flask-7d8f9           │   │
│ └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ NETWORK TOPOLOGY                                             │
│                                                              │
│    [User] ──▶ [Ingress] ──▶ [nginx-svc] ──▶ [flask-svc]    │
│                                         │           │       │
│                                         ▼           ▼       │
│                                    [nginx-pod] [flask-pod]  │
│                                                      │       │
│                                                      ▼       │
│                                              [postgres-svc]  │
│                                                      │       │
│                                                      ▼       │
│                                              [postgres-pod]  │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Steps (Gradual)

1. **Phase 1: Request ID Middleware** - Add unique ID to each request
2. **Phase 2: Request Logging** - Log entry/exit at each service
3. **Phase 3: Metrics Collection** - Capture timing and status
4. **Phase 4: Dashboard UI** - Build `/monitor` visualization
5. **Phase 5: K8s Integration** - Connect to Kubernetes metrics API
6. **Phase 6: Distributed Tracing** - Optional: Add Jaeger/Zipkin

---

## Commands Reference

```bash
# Rebuild and restart containers
docker-compose down -v && docker-compose up --build

# View backend logs
docker-compose logs -f backend

# View database logs
docker-compose logs -f db

# Check running containers
docker-compose ps
```

---

## Change Log

| Date | Improvement | Description |
|------|-------------|-------------|
| 2026-03-16 | Password Hashing | Replaced SHA256 with bcrypt for secure password storage |
| | | |