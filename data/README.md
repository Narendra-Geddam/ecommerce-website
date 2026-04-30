# Database Schema & Data

This directory contains the PostgreSQL database schema definition and initial data for the e-commerce application.

## Overview

The `schema.sql` file defines the complete database structure for the e-commerce system:
- **User Management** - Accounts, authentication
- **Product Catalog** - Products with pricing and stock
- **Order Management** - Transactions and order details
- **Cart Management** - Shopping cart items

## Structure

```
data/
└── schema.sql          # Complete DDL and DML statements
```

## Database Architecture

### Tables

#### `users`
Stores user account information and authentication data.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,        -- bcrypt hash
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Relationships:**
- One-to-Many: `users` → `orders`
- One-to-Many: `users` → `cart_items`

**Indexes:**
- `email` (unique) - Fast login lookups
- `created_at` - User activity reports

#### `products`
Catalog of available products with pricing and inventory.

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(500),
    category VARCHAR(100),
    stock INTEGER DEFAULT 100,             -- Current inventory
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Data Categories:**
- **Mobiles** - Smartphones and devices (10 products)
- **Books** - Educational and fiction (11 products)
- **Clothings** - Apparel and fashion (10 products)
- **Beauty** - Cosmetics and personal care (10 products)
- **Furniture** - Home and office furniture (5 products)
- **Laptops** - Computers and portable devices (5 products)

**Total Products:** 50 (all with real product data)

**Relationships:**
- One-to-Many: `products` → `order_items`
- One-to-Many: `products` → `cart_items`

#### `orders`
Customer orders with status tracking and delivery information.

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),  -- Foreign key
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Processing',
    shipping_address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    phone VARCHAR(20),
    payment_method VARCHAR(50) DEFAULT 'COD',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_date TIMESTAMP
);
```

**Status Values:**
- `Processing` - Order received, awaiting fulfillment
- `Shipped` - Order is in transit
- `Delivered` - Order successfully delivered
- `Cancelled` - Order cancelled by customer or system

**Payment Methods:**
- `COD` - Cash on Delivery (default)
- `UPI` - Unified Payments Interface
- `Credit Card` - Credit card payment
- `Debit Card` - Debit card payment

**Relationships:**
- Many-to-One: `orders` → `users` (foreign key)
- One-to-Many: `orders` → `order_items`

#### `order_items`
Line items for each order (many-to-many between orders and products).

```sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL           -- Price at time of order
);
```

**Features:**
- `ON DELETE CASCADE` - Remove items when order is deleted
- Captures historical pricing (not affected by product price changes)

**Relationships:**
- Many-to-One: `order_items` → `orders`
- Many-to-One: `order_items` → `products`

#### `cart_items`
Current shopping cart for each user.

```sql
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL
);
```

**Features:**
- Temporary storage for items before checkout
- Deleted after order completion or expiration

## Entity Relationship Diagram

```
users (1) ──── (M) orders
  │              │
  │              └──┬──── (M) order_items
  │                 │
  └─────────────────┴────── (M) cart_items

products (1) ──┬──── (M) order_items
               └──────── (M) cart_items
```

## Sample Data

### Products (50 Items)

**Mobiles (10 items)** - Rs. 19.99 to Rs. 1,199.99
- Redmi 9A, Samsung Galaxy M31, iPhone 12 Pro Max, OnePlus Nord CE, Jio Phone, realme narzo, OPPO A54, Vivo S1 Pro, Mi 11X, iPhone XR

**Books (11 items)** - Rs. 0.69 to Rs. 5.07
- The Monk Who Sold His Ferrari, Immortals of Meluha, Wuthering Heights, Byomkesh Bakshi, Pride and Prejudice, Hitchhiker's Guide, Green Humour, Sunderkand, Phir Meri Yaad, Kabir

**Clothings (10 items)** - Rs. 2.99 to Rs. 12.99
- Aeropostale Shirts, Khadi Silk Sarees, T-shirts, Baby Costumes, Kurtas, Blouses

**Beauty (10 items)** - Rs. 1.59 to Rs. 248.00
- Dove Shower Wash, Perfumes, Deodorants, Face Wash, Coconut Oil, Lotion, Hair Straightener, Kajal, Nail Polish

**Furniture (5 items)** - Rs. 31.99 to Rs. 328.99
- Office Chairs, Study Desks, Beds, Sofas, Wardrobes

**Laptops (5 items)** - Rs. 375.90 to Rs. 2,154.90
- HP 15, Dell Inspiron, Lenovo IdeaPad, ASUS ROG Zephyrus, MacBook Pro

## Initialization

### First-Time Setup

```bash
# Connect to PostgreSQL
psql -U ecommerce -h localhost -d ecommerce

# Run schema initialization
\i schema.sql
```

### Container Initialization

When deploying via Kubernetes, the schema is initialized by the PostgreSQL StatefulSet:

```yaml
initContainers:
  - name: db-init
    image: postgres:15-alpine
    command:
      - sh
      - -c
      - psql -U ecommerce -d ecommerce < /schema/schema.sql
    volumeMounts:
      - name: schema-volume
        mountPath: /schema
```

## Data Queries

### Find Products by Category

```sql
SELECT name, price, stock FROM products 
WHERE category = 'Mobiles' 
ORDER BY price DESC;
```

### Get User Order History

```sql
SELECT o.id, o.order_date, o.total_amount, o.status 
FROM orders o
WHERE o.user_id = $1
ORDER BY o.order_date DESC;
```

### Calculate Order Revenue

```sql
SELECT SUM(total_amount) as revenue, COUNT(*) as orders 
FROM orders 
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';
```

### Stock Availability

```sql
SELECT name, stock FROM products 
WHERE stock > 0 
ORDER BY stock ASC;
```

### Low Stock Alert

```sql
SELECT id, name, stock FROM products 
WHERE stock < 5 AND stock > 0
ORDER BY stock ASC;
```

## Backup & Recovery

### Backup Database

```bash
# Dump entire database
pg_dump -U ecommerce ecommerce > backup.sql

# Compressed backup
pg_dump -U ecommerce ecommerce | gzip > backup.sql.gz
```

### Restore from Backup

```bash
# Restore database
psql -U ecommerce ecommerce < backup.sql

# From compressed backup
gunzip -c backup.sql.gz | psql -U ecommerce ecommerce
```

### In Kubernetes

```bash
# Backup from running pod
kubectl exec -n prod-ecommerce postgres-db-0 -- \
  pg_dump -U ecommerce ecommerce > backup.sql

# Restore to pod
kubectl cp backup.sql prod-ecommerce/postgres-db-0:/tmp/backup.sql
kubectl exec -n prod-ecommerce postgres-db-0 -- \
  psql -U ecommerce ecommerce < /tmp/backup.sql
```

## Performance Tuning

### Recommended Indexes

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created ON users(created_at DESC);

-- Order queries
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_order_date ON orders(order_date DESC);

-- Product searches
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_stock ON products(stock);

-- Cart access
CREATE INDEX idx_cart_user_id ON cart_items(user_id);
```

### Query Optimization

```sql
-- Use EXPLAIN ANALYZE for slow queries
EXPLAIN ANALYZE
SELECT p.name, SUM(oi.quantity) as total_sold
FROM products p
JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id
ORDER BY total_sold DESC LIMIT 10;
```

## Maintenance

### Regular Tasks

**Weekly:**
- Monitor slow queries
- Check disk space usage
- Verify backups

**Monthly:**
- Analyze table statistics: `ANALYZE;`
- Reindex tables: `REINDEX DATABASE ecommerce;`
- Review growth metrics

**Quarterly:**
- Archive old orders (>6 months)
- Optimize queries with low selectivity
- Review password expiration policies

### Connection String

For application configuration:

```
postgresql://ecommerce:password@postgres-service.prod-ecommerce:5432/ecommerce
```

- **Host:** `postgres-service.prod-ecommerce` (K8s service DNS)
- **User:** `ecommerce`
- **Password:** `password` (from AWS Secrets Manager)
- **Database:** `ecommerce`
- **Port:** `5432` (default PostgreSQL)

## Troubleshooting

### Connection Issues

**"does not exist" error**
```bash
# Verify database exists
psql -U postgres -l | grep ecommerce

# Create if missing
createdb -U postgres ecommerce
```

**"permission denied" error**
```bash
# Check user permissions
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ecommerce TO ecommerce;"
```

### Schema Issues

**Missing tables**
```bash
# Re-run initialization
psql -U ecommerce ecommerce < schema.sql
```

**Duplicate key errors**
```sql
-- Check for conflicts
SELECT * FROM products WHERE id = <conflict_id>;

-- Fix with UPSERT
INSERT INTO products (...) VALUES (...) 
ON CONFLICT (id) DO UPDATE SET ...;
```

## Links

- **Backend README**: [apps/backend/README.md](../apps/backend/README.md)
- **Main Guide**: [README.md](../README.md)
- **Helm Deployment**: [infra/kubernetes/helm/README.md](../infra/kubernetes/helm/README.md)
- **K8s Reference**: [infra/kubernetes/base/README.md](../infra/kubernetes/base/README.md)
