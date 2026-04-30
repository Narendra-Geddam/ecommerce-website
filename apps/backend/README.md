# Flask API Backend

This is the backend API service for the e-commerce application, built with **Flask** and **PostgreSQL**.

## Overview

The Flask API serves as the core business logic layer, providing RESTful endpoints for:
- **Product Management** - Browse and search products
- **User Authentication** - Login, registration, password management
- **Order Processing** - Create and manage orders
- **Shopping Cart** - Manage cart items
- **Profile Management** - User account and profile data

## Structure

```
application/
├── app.py              # Main Flask application and route handlers
├── requirements.txt    # Python dependencies
└── Dockerfile         # Container image definition
```

## Key Technologies

- **Flask** - Lightweight Python web framework
- **PostgreSQL** - Relational database via psycopg2
- **Gunicorn** - WSGI application server (production)
- **Flask-CORS** - Cross-origin request handling
- **bcrypt** - Password hashing and verification

## Environment Variables

The application requires these environment variables (injected via K8s secrets):

| Variable | Source | Description |
|----------|--------|-------------|
| `DATABASE_URL` | AWS Secrets Manager | PostgreSQL connection string |
| `SECRET_KEY` | AWS Secrets Manager | Flask session encryption key |
| `FLASK_ENV` | AWS Parameter Store | Environment (production/development) |
| `DEBUG` | AWS Parameter Store | Debug mode toggle |
| `LOG_LEVEL` | AWS Parameter Store | Logging verbosity level |

## Build & Run

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://ecommerce:password@localhost:5432/ecommerce"
export SECRET_KEY="dev-secret-key"

# Run Flask development server
python app.py
# Runs on http://localhost:5000
```

### Docker Container

```bash
# Build image
docker build -t flask-api:latest .

# Run container
docker run -e DATABASE_URL="postgresql://..." \
           -e SECRET_KEY="..." \
           -p 5000:5000 \
           flask-api:latest
```

### Kubernetes Deployment

The application is deployed as a Kubernetes Deployment (3 replicas in production):

```bash
# Via Helm (recommended)
helm install ecommerce ./infra/kubernetes/helm -n prod-ecommerce --create-namespace

# View running pods
kubectl get pods -n prod-ecommerce -l app=flask-api

# View logs
kubectl logs -n prod-ecommerce -l app=flask-api --tail=50
```

## API Endpoints

### Products
- `GET /api/products` - Fetch all products with pagination
- `GET /api/products/<id>` - Get product details

### Users & Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - User login
- `GET /api/profile` - Get current user profile
- `POST /api/logout` - User logout

### Orders
- `GET /api/orders` - Get user's orders
- `POST /api/orders` - Create new order
- `GET /api/orders/<id>` - Order details

### Cart
- `GET /api/cart` - Get shopping cart
- `POST /api/cart/add` - Add item to cart
- `DELETE /api/cart/<item_id>` - Remove from cart

### Health & Monitoring
- `GET /health` - Health check endpoint
- `GET /api/stats` - Application statistics

## Database Schema

The application uses PostgreSQL (database schema in `../data/schema.sql`):

**Main Tables:**
- `users` - User accounts and authentication
- `products` - Product catalog
- `orders` - Customer orders
- `order_items` - Items in each order
- `cart_items` - Shopping cart contents

See [Database Schema](../data/README.md) for complete documentation.

## Configuration

### Deployment Configuration (Helm)

Configure via `infra/kubernetes/helm/values.yaml`:

```yaml
# Flask API configuration
flaskApi:
  replicas: 3           # Number of pods
  image: usernamenarendra/morecraze-application:v2.1.0
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"
```

### Local Configuration

Modify `app.py` for local development settings:
- Default database connection string
- Debug mode
- Session configuration

## Dependencies

See `requirements.txt` for complete list:

```
Flask==2.3.0
Flask-CORS==4.0.0
psycopg2-binary==2.9.0
gunicorn==20.0.0
bcrypt==4.0.0
```

## Performance & Health

The API includes built-in monitoring:

- **Request Tracking** - Last 100 requests logged
- **Error Tracking** - Total errors counted
- **Health Endpoint** - Container orchestration health checks
- **Graceful Shutdown** - Proper cleanup on termination

View stats:
```bash
curl http://localhost:5000/api/stats
```

## Troubleshooting

### Connection Errors

**"password authentication failed"**
- Verify `DATABASE_URL` environment variable
- Check PostgreSQL pod is running: `kubectl get pods -n prod-ecommerce postgres-db-0`
- Verify credentials in `terraform.tfvars`

**"connection to server refused"**
- Ensure PostgreSQL service is accessible
- Check DNS resolution: `kubectl exec -it <flask-pod> -- nslookup postgres-service.prod-ecommerce`

### Application Not Starting

**Check logs:**
```bash
kubectl logs -n prod-ecommerce -l app=flask-api --tail=100
```

**Describe pod for events:**
```bash
kubectl describe pod -n prod-ecommerce <pod-name>
```

### Slow Queries

Enable query logging by adjusting `LOG_LEVEL` parameter in AWS Parameter Store to `DEBUG`.

## Development

### Adding New Endpoints

1. Edit `app.py` and add route decorator:
   ```python
   @app.route('/api/new-endpoint', methods=['GET'])
   def new_endpoint():
       # Implementation
       return jsonify(response)
   ```

2. Rebuild Docker image
3. Deploy via Helm upgrade

### Running Tests

```bash
# From workspace root
pytest tests/
```

## Security

- **Passwords** - Hashed with bcrypt (12-round salt)
- **Sessions** - Encrypted with Flask secret key
- **Database** - Connections via TLS (in production)
- **CORS** - Restricted to frontend origin
- **SQL Injection** - Prevented via parameterized queries

## Deployment

See main [README.md](../README.md#deployment-methods) for full deployment instructions:

- **Helm** (Recommended) - Template-based, environment-specific
- **Manual K8s** - Direct manifest deployment (learning reference)
- **Terraform + Helm** - Complete infrastructure automation

## Links

- **Main Guide**: [README.md](../README.md)
- **Helm Deployment**: [infra/kubernetes/helm/README.md](../infra/kubernetes/helm/README.md)
- **Database Schema**: [data/README.md](../data/README.md)
- **Frontend**: [apps/frontend/README.md](../apps/frontend/README.md)
- **K8s Reference**: [infra/kubernetes/base/README.md](../infra/kubernetes/base/README.md)
