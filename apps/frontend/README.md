# Frontend - Nginx Presentation Layer

This is the **Nginx-based frontend** for the e-commerce application, serving the user interface and handling static assets.

## Overview

The presentation layer is a containerized Nginx web server that:
- Serves **HTML pages** for the e-commerce UI (index, product, cart, checkout, etc.)
- Manages **static assets** (CSS, JavaScript, images)
- **Reverse proxies** requests to the Flask API backend
- Implements **request routing and load balancing**
- Compresses responses for optimal performance

## Structure

```
apps/frontend/
├── index.html              # Main landing page
├── login.html              # User login page
├── register.html           # User registration page
├── profile.html            # User profile page
├── cart.html               # Shopping cart page
├── checkout.html           # Checkout/payment page
├── orders.html             # Order history page
├── monitor.html            # Monitoring dashboard
├── nginx.conf              # Nginx configuration
├── Dockerfile              # Container image definition
├── images/                 # Product images and assets
└── static/                 # CSS, JavaScript, images
    └── products/           # Product catalog images
    └── uploads/            # User uploaded files
```

## Key Technologies

- **Nginx** - High-performance web server and reverse proxy
- **HTML5** - Modern semantic markup
- **JavaScript** - Client-side interactivity (Vanilla JS)
- **CSS3** - Responsive styling
- **Docker** - Containerization

## Build & Run

### Local Development

Requires Nginx installed:

```bash
# Copy static assets
cp -r static/* /usr/share/nginx/html/

# Copy HTML pages
cp *.html /usr/share/nginx/html/

# Copy Nginx config
sudo cp nginx.conf /etc/nginx/nginx.conf

# Start Nginx
sudo systemctl start nginx
# Runs on http://localhost:80
```

### Docker Container

```bash
# Build image
docker build -t frontend:latest .

# Run container
docker run -p 80:80 \
           -e API_URL="http://flask-api:5000" \
           frontend:latest
```

### Kubernetes Deployment

The application is deployed as a Kubernetes Deployment (3 replicas in production):

```bash
# Via Helm (recommended)
helm install ecommerce ./infra/kubernetes/helm -n prod-ecommerce --create-namespace

# View running pods
kubectl get pods -n prod-ecommerce -l app=nginx-frontend

# View logs
kubectl logs -n prod-ecommerce -l app=nginx-frontend --tail=50
```

## Page Descriptions

### index.html
**Landing Page** - Main entry point showing featured products and categories

### login.html
**User Login** - Authentication page, POST to `/api/login`

### register.html
**User Registration** - New account creation, POST to `/api/register`

### profile.html
**User Profile** - Profile management, managed via API calls

### cart.html
**Shopping Cart** - View and manage cart items

### checkout.html
**Checkout Page** - Final order placement form

### orders.html
**Order History** - View previous orders and tracking

### monitor.html
**Monitoring Dashboard** - System metrics and health checks (requires /api/monitor endpoints)
