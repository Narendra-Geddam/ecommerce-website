<div align="center">

# 🛒 ShopEasy E-Commerce Platform

<img src="https://img.shields.io/badge/Flask-3.1.3-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
<img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
<img src="https://img.shields.io/badge/Nginx-Alpine-009639?style=for-the-badge&logo=nginx&logoColor=white" alt="Nginx">
<img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">

<img src="https://img.shields.io/github/last-commit/Narendra-Geddam/ecommerce-website?style=for-the-badge" alt="Last Commit">
<img src="https://img.shields.io/github/languages/top/Narendra-Geddam/ecommerce-website?style=for-the-badge" alt="Language">
<img src="https://img.shields.io/github/issues/Narendra-Geddam/ecommerce-website?style=for-the-badge" alt="Issues">
<img src="https://img.shields.io/github/license/Narendra-Geddam/ecommerce-website?style=for-the-badge" alt="License">

### A Modern 3-Tier E-Commerce Application with Real-Time Monitoring

*Built with ❤️ using Flask, PostgreSQL, and Nginx*

[🚀 Quick Start](#-quick-start) • [📊 Monitoring](#-monitoring-dashboard) • [✨ Features](#-features) • [🏗️ Architecture](#-architecture)

</div>

---

<div align="center">

## 🏗️ Architecture Overview

</div>

<table align="center">
<tr>
<td align="center" width="33%">
<h3>🌐 Presentation Layer</h3>
<img src="https://img.shields.io/badge/Nginx-Alpine-009639?style=flat-square&logo=nginx" alt="Nginx">
<br><br>
<code>Port 80</code>
<br>
<span>Static files & reverse proxy</span>
</td>
<td align="center" width="2%">
<h1>→</h1>
</td>
<td align="center" width="33%">
<h3>⚡ Application Layer</h3>
<img src="https://img.shields.io/badge/Flask-3.1.3-000000?style=flat-square&logo=flask" alt="Flask">
<br><br>
<code>Port 5000</code>
<br>
<span>REST API & Business Logic</span>
</td>
<td align="center" width="2%">
<h1>→</h1>
</td>
<td align="center" width="33%">
<h3>🗄️ Data Layer</h3>
<img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql" alt="PostgreSQL">
<br><br>
<code>Port 5432</code>
<br>
<span>Persistent data storage</span>
</td>
</tr>
</table>

---

<div align="center">

## ✨ Features

</div>

<table>
<tr>
<td width="50%">

### 🛍️ E-Commerce Features
- 📦 **50+ Real Products** across 6 categories
- 🔍 **Product Search & Filtering** by category
- 🛒 **Shopping Cart** with session persistence
- 👤 **User Authentication** (Register/Login/Logout)
- 📋 **Order History** with order tracking
- 💳 **Checkout Flow** with address forms
- 🎨 **Modern Responsive UI** with animations

</td>
<td width="50%">

### 🔒 Security Features
- 🔐 **Bcrypt Password Hashing** (industry standard)
- 🌐 **CORS Protection** with Flask-CORS 6.0.2
- 🛡️ **Secure Headers** via Nginx
- 📊 **Request Tracing** with unique IDs
- ⏱️ **Rate Tracking** per endpoint
- 🔑 **Session Management** with Flask sessions

</td>
</tr>
</table>

<table>
<tr>
<td width="50%">

### 📊 Monitoring Dashboard
- 📡 **Real-time Request Flow** with timing
- 🐳 **Container/Pod Information**
- 📈 **Service Health Status**
- 🕒 **Request History** (last 100 requests)
- 📉 **Endpoint Performance Metrics**
- 🏗️ **Architecture Visualization**

</td>
<td width="50%">

### 🐳 DevOps Features
- 🐋 **Docker Compose** for local development
- 🔄 **Auto Database Seeding** on startup
- 📦 **Multi-stage Builds** optimization
- 🏥 **Health Check Endpoints**
- 📝 **Structured Logging**
- 🚀 **Production Ready** configuration

</td>
</tr>
</table>

---

<div align="center">

## 📊 Monitoring Dashboard

</div>

<div align="center">

### 🎯 Access the Dashboard

**→ Open `http://localhost/monitor` after starting the application ←**

</div>

<table>
<tr>
<td>

<img src="https://img.shields.io/badge/Endpoint-/monitor-blue?style=flat-square" alt="Monitor Endpoint">

### What You'll See:

| Panel | Description |
|-------|-------------|
| **Stats Overview** | Total requests, avg latency, error rate, uptime |
| **Running Containers** | Container names, images, replicas, health status |
| **Service Status** | Nginx, Flask, PostgreSQL health & latency |
| **Request Flow** | Real-time request log with descriptions |
| **Endpoint Performance** | Per-endpoint latency & error counts |

### Request Descriptions:

Each request shows a human-readable description like:
- `Fetching product catalog` → `/products`
- `Adding item to cart` → `/api/cart/add/:id`
- `User logging in` → `/api/login`
- `Placing new order` → `/api/orders`

</td>
</tr>
</table>

<div align="center">

### 📸 Dashboard Preview

```html
┌─────────────────────────────────────────────────────────────────────┐
│  📊 MONITORING DASHBOARD                                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Total    │ │ Avg      │ │ Error    │ │ Uptime   │ │ Req/min  │ │
│  │ Requests │ │ Latency  │ │ Rate     │ │          │ │          │ │
│  │  1,234   │ │  4.2ms   │ │  0.0%    │ │ 2h 15m   │ │  12.5    │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  📦 RUNNING CONTAINERS                                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │ demo-presentation│ │  5c2e2fa52eb5  │ │ demo-database-1 │       │
│  │ Nginx Frontend   │ │ Flask Backend   │ │ PostgreSQL DB   │       │
│  │ ● Running        │ │ ● Running       │ │ ● Running       │       │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
├─────────────────────────────────────────────────────────────────────┤
│  📡 REQUEST FLOW                                                    │
│  ┌────────┬────────┬─────────────────────┬────────┬──────────┐     │
│  │ ID     │ Method │ Description         │ Status │ Duration │     │
│  ├────────┼────────┼─────────────────────┼────────┼──────────┤     │
│  │ a1b2c3 │ GET    │ Fetching products   │ 200    │ 12.5ms   │     │
│  │ d4e5f6 │ POST   │ Adding to cart      │ 200    │ 3.2ms    │     │
│  │ g7h8i9 │ POST   │ User logging in     │ 200    │ 45.1ms   │     │
│  └────────┴────────┴─────────────────────┴────────┴──────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

</div>

---

<div align="center">

## 🚀 Quick Start

</div>

### Prerequisites
- Docker & Docker Compose installed
- Git installed

### 1️⃣ Clone & Run

```bash
# Clone the repository
git clone https://github.com/Narendra-Geddam/ecommerce-website.git
cd ecommerce-website

# Start all services
docker-compose up --build
```

### 2️⃣ Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| 🏪 **Store** | http://localhost | Main e-commerce site |
| 📊 **Monitor** | http://localhost/monitor | Real-time dashboard |
| 🗄️ **Database** | localhost:5432 | PostgreSQL (internal) |

### 3️⃣ Stop the Application

```bash
docker-compose down -v  # -v removes volumes (resets DB)
```

---

<div align="center">

## 📁 Project Structure

</div>

```
ecommerce-website/
├── 📂 application/           # Backend (Flask)
│   ├── app.py               # Main application with API endpoints
│   └── requirements.txt     # Python dependencies
│
├── 📂 presentation/          # Frontend (Nginx)
│   ├── index.html           # Product listing page
│   ├── cart.html            # Shopping cart
│   ├── checkout.html        # Checkout flow
│   ├── monitor.html         # 📊 Monitoring dashboard
│   ├── nginx.conf           # Nginx configuration
│   └── static/              # Images & static assets
│
├── 📂 data/                  # Database
│   ├── schema.sql           # Database schema
│   └── seed_products.sql    # 50+ product seeds
│
├── 📄 docker-compose.yml    # Docker orchestration
├── 📄 CLAUDE.md             # Development roadmap
└── 📄 README.md             # This file
```

---

<div align="center">

## 🔌 API Endpoints

</div>

<table>
<thead>
<tr>
<th>Method</th>
<th>Endpoint</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/products</code></td>
<td>Get all products (filter by ?category=)</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/categories</code></td>
<td>Get all product categories</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/POST-blue?style=flat-square" alt="POST"></td>
<td><code>/api/register</code></td>
<td>Register new user</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/POST-blue?style=flat-square" alt="POST"></td>
<td><code>/api/login</code></td>
<td>User authentication</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/api/cart</code></td>
<td>Get cart items</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/POST-blue?style=flat-square" alt="POST"></td>
<td><code>/api/cart/add/:id</code></td>
<td>Add product to cart</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/POST-blue?style=flat-square" alt="POST"></td>
<td><code>/api/orders</code></td>
<td>Create new order</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/api/monitor/requests</code></td>
<td>📊 Request history</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/api/monitor/services</code></td>
<td>📊 Service status</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/api/monitor/stats</code></td>
<td>📊 Aggregate statistics</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/health</code></td>
<td>💚 Liveness probe (is container running?)</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/ready</code></td>
<td>💜 Readiness probe (can container receive traffic?)</td>
</tr>
<tr>
<td><img src="https://img.shields.io/badge/GET-green?style=flat-square" alt="GET"></td>
<td><code>/live</code></td>
<td>💗 Simple liveness check</td>
</tr>
</tbody>
</table>

---

<div align="center">

## 💚 Health Checks & Probes

</div>

<table>
<tr>
<td width="50%">

### 🔍 Docker Health Checks

All services include Docker health checks:

```yaml
# Nginx (Presentation)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s

# Flask (Application)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/ready"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 20s

# PostgreSQL (Database)
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ecommerce"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

</td>
<td width="50%">

### ☸️ Kubernetes Probes

```yaml
# Liveness Probe - Restart if unhealthy
livenessProbe:
  httpGet:
    path: /live
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

# Readiness Probe - Route traffic when ready
readinessProbe:
  httpGet:
    path: /ready
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3

# Startup Probe - For slow starting containers
startupProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 30
```

</td>
</tr>
</table>

<div align="center">

### 🏥 Health Check Endpoints

</div>

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | **Liveness** - Is the service running? | `{"status":"healthy","service":"nginx"}` |
| `GET /ready` | **Readiness** - Can handle traffic + DB connected? | `{"status":"ready","database":"connected"}` |
| `GET /live` | **Simple Liveness** - Basic alive check | `{"status":"alive","service":"flask"}` |

```bash
# Test health endpoints
curl http://localhost/health     # Nginx liveness
curl http://localhost/ready      # Backend readiness (proxied)
curl http://localhost/live        # Nginx alive check

# Direct backend health
curl http://localhost:5000/health
curl http://localhost:5000/ready
curl http://localhost:5000/live
```

---

<div align="center">

## 🛠️ Technology Stack

</div>

<table align="center">
<tr>
<th>Category</th>
<th>Technology</th>
<th>Version</th>
</tr>
<tr>
<td>Frontend</td>
<td>Nginx Alpine</td>
<td>Latest</td>
</tr>
<tr>
<td>Backend</td>
<td>Flask</td>
<td>3.1.3</td>
</tr>
<tr>
<td>Database</td>
<td>PostgreSQL</td>
<td>15 Alpine</td>
</tr>
<tr>
<td>Security</td>
<td>Flask-CORS</td>
<td>6.0.2</td>
</tr>
<tr>
<td>Security</td>
<td>Bcrypt</td>
<td>4.1.2</td>
</tr>
<tr>
<td>WSGI</td>
<td>Gunicorn</td>
<td>22.0.0</td>
</tr>
<tr>
<td>Monitoring</td>
<td>psutil</td>
<td>5.9.8</td>
</tr>
</table>

---

<div align="center">

## 📈 Performance & Security

</div>

<table>
<tr>
<td width="50%">

### ⚡ Performance Features
- Connection pooling ready
- Static file caching via Nginx
- Optimized database queries
- Request ID tracing
- Latency tracking per endpoint
- Auto-refresh monitoring (5s intervals)

</td>
<td width="50%">

### 🔒 Security Headers
```nginx
X-Request-ID: abc12345
X-Response-Time: 12.34ms
```
- Bcrypt password hashing
- CORS protection enabled
- SQL injection prevention
- XSS protection via template escaping

</td>
</tr>
</table>

---

<div align="center">

## 🧪 Testing

</div>

```bash
# Run the application
docker-compose up --build

# Test products endpoint
curl http://localhost/api/products | head

# Test monitoring
curl http://localhost/api/monitor/services

# View in browser
open http://localhost
open http://localhost/monitor
```

---

<div align="center">

## 📝 License

</div>

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

## 🤝 Contributing

</div>

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<div align="center">

## 📞 Support

</div>

If you have any questions or issues, please [open an issue](https://github.com/Narendra-Geddam/ecommerce-website/issues) on GitHub.

---

<div align="center">

**Made with ❤️ by [Narendra Geddam](https://github.com/Narendra-Geddam)**

<img src="https://img.shields.io/github/stars/Narendra-Geddam/ecommerce-website?style=social" alt="GitHub stars">
<img src="https://img.shields.io/github/forks/Narendra-Geddam/ecommerce-website?style=social" alt="GitHub forks">
<img src="https://img.shields.io/github/watchers/Narendra-Geddam/ecommerce-website?style=social" alt="GitHub watchers">

</div>