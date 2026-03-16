# Simple 3-Tier E-Commerce Application

This is a simple e-commerce application built with Flask and SQLite to demonstrate the three-tier architecture.

## Tiers

1. **Presentation Tier**: HTML templates and static files in the `presentation` folder.
2. **Application Tier**: Flask application in the `application` folder (`app.py`).
3. **Data Tier**: SQLite database (`ecommerce.db`) with schema in the `data` folder (`schema.sql`).

## Files

- `application/app.py`: Main Flask application.
- `data/schema.sql`: Database schema and sample data.
- `presentation/index.html`: Product listing page.
- `presentation/cart.html`: Shopping cart page.
- `presentation/checkout.html`: Checkout page.
- `presentation/static/`: Static files (images, CSS, JavaScript)
- `Dockerfile`: Docker configuration for containerization
- `requirements.txt`: Python dependencies
- `k8s/deployment.yaml`: Kubernetes deployment manifest
- `helm-chart/`: Helm chart for Kubernetes deployment
- `3_tier_ecommerce_explanation.md`: Explanation of the three-tier architecture.

## How to Run

### Option 1: Direct Execution
1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python application/app.py
   ```

3. Open your web browser and go to `http://localhost:5000`.

### Option 2: Docker
1. Build the Docker image:
   ```
   docker build -t ecommerce-app .
   ```

2. Run the Docker container:
   ```
   docker run -p 5000:5000 ecommerce-app
   ```

3. Open your web browser and go to `http://localhost:5000`.

### Option 3: Kubernetes (using kubectl)
1. Apply the Kubernetes manifest:
   ```
   kubectl apply -f k8s/deployment.yaml
   ```

2. Access the application via the LoadBalancer service or port-forward:
   ```
   kubectl port-forward svc/ecommerce-app-service 5000:80
   ```

3. Open your web browser and go to `http://localhost:5000`.

### Option 4: Kubernetes (using Helm)
1. Install the Helm chart:
   ```
   helm install ecommerce-app ./helm-chart
   ```

2. Access the application via the LoadBalancer service or port-forward:
   ```
   kubectl port-forward svc/ecommerce-app 5000:80
   ```

3. Open your web browser and go to `http://localhost:5000`.

## Functionality

- Browse products on the home page.
- Add products to the cart.
- View the cart and total price.
- Proceed to checkout (which clears the cart and shows a thank you message).

## Notes

- This is a simplified example for educational purposes.
- In a real application, you would need to add user authentication, secure payment processing, and more robust error handling.
- The secret key in `application/app.py` should be changed and kept secret in production.
- Image files are stored as placeholders in `presentation/static/` and referenced in the database.
- Each tier is separated into its own directory for clarity:
  - Presentation: `presentation/` (HTML, CSS, images)
  - Application: `application/` (Flask app)
  - Data: `data/` (database schema)
- The Kubernetes manifest (`k8s/deployment.yaml`) creates a Deployment with 3 replicas and a LoadBalancer Service.
- The Helm chart (`helm-chart/`) provides a templatable way to deploy the application with configurable values.