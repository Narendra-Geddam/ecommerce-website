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
presentation/
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
helm install ecommerce ./helm-chart -n prod-ecommerce --create-namespace

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
**User Profile** - View and edit account details, connects to `/api/profile`

### cart.html
**Shopping Cart** - Display cart items, quantity adjustment, connects to `/api/cart`

### checkout.html
**Checkout Process** - Payment and shipping information, POST to `/api/orders`

### orders.html
**Order History** - View past orders, connects to `/api/orders`

### monitor.html
**System Monitor** - Dashboard showing system stats, API calls, health status (admin only)

## Nginx Configuration

The `nginx.conf` file includes:

```nginx
# Upstream backend
upstream flask_api {
    server flask-api-service:5000;
}

# Gzip compression
gzip on;
gzip_types text/plain text/css application/json;

# Reverse proxy configuration
location /api/ {
    proxy_pass http://flask_api;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
}

# Static file caching
location /static/ {
    expires 7d;
    cache_control: max-age=604800;
}
```

## Environment Variables

The frontend doesn't require secrets but uses:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_URL` | `http://flask-api-service:5000` | Backend API endpoint |

Set in Docker/K8s container environment.

## Static Assets

### CSS
- **style.css** - Main stylesheet with responsive design
- **responsive.css** - Mobile-first breakpoints

### JavaScript
- **app.js** - Main application logic
- **api-client.js** - API communication utilities
- **utils.js** - Helper functions

### Images
- **products/** - Product catalog images
- **uploads/** - User-generated content

## API Integration

The frontend communicates with Flask API via REST:

```javascript
// Example API call
fetch('http://api-endpoint/api/products')
  .then(response => response.json())
  .then(data => renderProducts(data))
  .catch(error => console.error('Error:', error));
```

All API endpoints documented in [application/README.md](../application/README.md#api-endpoints)

## Browser Compatibility

- **Chrome** 90+
- **Firefox** 88+
- **Safari** 14+
- **Edge** 90+
- **Mobile** iOS Safari, Chrome Mobile

## Performance

Nginx configuration optimizations:

```nginx
# Compression
gzip on;              # Enable Gzip compression
gzip_min_length 1000; # Only compress >1KB

# Caching
expires 7d;           # Static files: 7 day cache
add_header Cache-Control "public, immutable";

# Connection pooling
keepalive_requests 100;
keepalive_timeout 65s;
```

Metrics:
- Initial page load: ~500ms (over 1Mbps)
- Static asset caching: 7 days
- Gzip compression ratio: ~70% reduction

## Configuration

### Deployment Configuration (Helm)

Configure via `helm-chart/values.yaml`:

```yaml
# Nginx frontend configuration
nginxFrontend:
  replicas: 3           # Number of pods
  image: usernamenarendra/morecraze-presentation:v2.6.0
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"
    limits:
      memory: "256Mi"
      cpu: "200m"
  
  # Backend API configuration
  apiUrl: "http://flask-api-service:5000"
```

### Nginx Configuration Customization

Edit `nginx.conf` and rebuild Docker image:

```bash
docker build -t frontend:latest .
```

## Troubleshooting

### 502 Bad Gateway

**Cause:** Cannot reach Flask API backend

**Fix:**
```bash
# Check API service is running
kubectl get svc -n prod-ecommerce flask-api-service

# Verify connectivity from Nginx pod
kubectl exec -it <nginx-pod> -n prod-ecommerce -- curl http://flask-api-service:5000/health

# Check Nginx logs
kubectl logs -n prod-ecommerce -l app=nginx-frontend
```

### Slow Page Load

**Check gzip compression:**
```bash
curl -I -H "Accept-Encoding: gzip" http://localhost:80/
```

**Check cache headers:**
```bash
curl -I http://localhost:80/static/style.css
```

### Static Files Not Loading

**Verify volume mount:**
```bash
kubectl describe pod -n prod-ecommerce <nginx-pod> | grep -A 5 Mounts
```

**Check file permissions:**
```bash
kubectl exec -it <nginx-pod> -n prod-ecommerce -- ls -la /usr/share/nginx/html/
```

## Development

### Adding New Pages

1. Create new HTML file in `presentation/` directory
2. Update Nginx routing in `nginx.conf` if needed
3. Add menu link to `index.html`
4. Rebuild Docker image:
   ```bash
   docker build -t frontend:latest .
   ```

### Modifying Styles

Edit CSS files in `static/` and rebuild:

```bash
docker build -t frontend:latest .
```

### Testing Locally

```bash
# Start local Nginx
docker run -p 80:80 -v $(pwd):/usr/share/nginx/html:ro nginx:latest

# Visit http://localhost
```

## Security

- **Content Security Policy** - Restricts inline scripts
- **X-Frame-Options** - Prevents clickjacking
- **X-Content-Type-Options** - MIME type sniffing prevention
- **HTTPS** - Enforced in production (ALB terminates SSL)
- **CORS** - Restricted to API domain

## Deployment

See main [README.md](../README.md#deployment-methods) for full deployment instructions:

- **Helm** (Recommended) - Template-based, environment-specific
- **Manual K8s** - Direct manifest deployment (learning reference)
- **Terraform + Helm** - Complete infrastructure automation

## Links

- **Main Guide**: [README.md](../README.md)
- **Helm Deployment**: [helm-chart/README.md](../helm-chart/README.md)
- **Backend API**: [application/README.md](../application/README.md)
- **K8s Reference**: [k8s/README.md](../k8s/README.md)
