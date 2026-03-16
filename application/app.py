import os
import bcrypt
import time
import uuid
import psutil
import socket
import platform
from flask import Flask, jsonify, request, session, make_response, g
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import deque
from threading import Lock

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Enable CORS for frontend
CORS(app, supports_credentials=True)

# Request tracking storage
request_history = deque(maxlen=100)
request_history_lock = Lock()
stats = {
    'total_requests': 0,
    'total_errors': 0,
    'start_time': datetime.now()
}

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://ecommerce:password@database:5432/ecommerce')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def hash_password(password):
    """Hash password using bcrypt with automatic salt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Request tracking middleware
@app.before_request
def before_request():
    """Track request start time and generate unique ID"""
    g.request_id = str(uuid.uuid4())[:8]
    g.request_start_time = time.time()

def get_request_description(method, path):
    """Get a human-readable description of what the request does"""
    descriptions = {
        ('GET', '/products'): 'Fetching product catalog',
        ('GET', '/categories'): 'Loading product categories',
        ('GET', '/api/cart'): 'Viewing shopping cart',
        ('POST', '/api/cart/add'): 'Adding item to cart',
        ('POST', '/api/cart/remove'): 'Removing item from cart',
        ('POST', '/api/cart/clear'): 'Clearing cart',
        ('GET', '/api/cart/count'): 'Checking cart item count',
        ('POST', '/api/login'): 'User logging in',
        ('POST', '/api/register'): 'New user registering',
        ('POST', '/api/logout'): 'User logging out',
        ('GET', '/api/me'): 'Checking user session',
        ('PUT', '/api/profile'): 'Updating user profile',
        ('GET', '/api/orders'): 'Fetching order history',
        ('POST', '/api/orders'): 'Placing new order',
        ('GET', '/health'): 'Health check',
    }

    # Check for exact match first
    key = (method, path)
    if key in descriptions:
        return descriptions[key]

    # Check for pattern matches (with IDs)
    if path.startswith('/products/') and method == 'GET':
        return 'Fetching single product details'
    if path.startswith('/api/cart/add/') and method == 'POST':
        return 'Adding item to cart'
    if path.startswith('/api/cart/remove/') and method == 'POST':
        return 'Removing item from cart'
    if path.startswith('/api/orders/') and method == 'GET':
        return 'Fetching order details'
    if path.startswith('/api/monitor/'):
        return None  # Filter out monitoring requests

    return f'{method} {path}'

@app.after_request
def after_request(response):
    """Record request details after processing"""
    duration = (time.time() - g.request_start_time) * 1000  # Convert to ms

    # Get description and skip monitoring requests
    description = get_request_description(request.method, request.path)
    if description is None:
        # Skip monitoring requests from history
        return response

    request_info = {
        'id': g.request_id,
        'path': request.path,
        'method': request.method,
        'status': response.status_code,
        'duration_ms': round(duration, 2),
        'timestamp': datetime.now().isoformat(),
        'ip': request.remote_addr,
        'description': description
    }

    with request_history_lock:
        request_history.append(request_info)
        stats['total_requests'] += 1
        if response.status_code >= 400:
            stats['total_errors'] += 1

    # Add request ID header for tracing
    response.headers['X-Request-ID'] = g.request_id
    response.headers['X-Response-Time'] = f'{duration:.2f}ms'
    return response

# Health check for services
def get_db_status():
    """Check database connection status"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return {'status': 'healthy', 'latency_ms': 0}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

@app.route('/products')
def get_products():
    """API endpoint to get all products"""
    category = request.args.get('category')
    search = request.args.get('search')

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = 'SELECT * FROM products WHERE 1=1'
    params = []

    if category and category != 'All':
        query += ' AND category = %s'
        params.append(category)

    if search:
        query += ' AND (name ILIKE %s OR description ILIKE %s)'
        params.extend([f'%{search}%', f'%{search}%'])

    query += ' ORDER BY id'

    cur.execute(query, params)
    products = cur.fetchall()
    cur.close()
    conn.close()

    # Convert Decimal to float for JSON serialization
    for p in products:
        p['price'] = float(p['price'])
        p['stock'] = int(p['stock']) if p['stock'] else 0

    return jsonify(products)

@app.route('/products/<int:product_id>')
def get_product(product_id):
    """API endpoint to get a single product"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()
    if product:
        product['price'] = float(product['price'])
        product['stock'] = int(product['stock']) if product['stock'] else 0
        return jsonify(product)
    return jsonify({'error': 'Product not found'}), 404

@app.route('/categories')
def get_categories():
    """Get all product categories"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT DISTINCT category FROM products ORDER BY category')
    categories = [row['category'] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(['All'] + categories)

# Auth endpoints
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()

    required = ['name', 'email', 'password']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    hashed_pw = hash_password(data['password'])

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute('''
            INSERT INTO users (name, email, password, phone, address, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, email
        ''', (data['name'], data['email'], hashed_pw,
              data.get('phone', ''), data.get('address', ''),
              data.get('city', ''), data.get('state', ''), data.get('pincode', '')))

        user = cur.fetchone()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']

        return jsonify({'success': True, 'user': user})
    except psycopg2.IntegrityError:
        return jsonify({'success': False, 'error': 'Email already exists'}), 400
    finally:
        cur.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
        SELECT id, name, email, password FROM users
        WHERE email = %s
    ''', (data['email'],))

    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and verify_password(data['password'], user['password']):
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        return jsonify({'success': True, 'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}})

    return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/me', methods=['GET'])
def get_current_user():
    """Get current logged in user"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False})

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('''
        SELECT id, name, email, phone, address, city, state, pincode, created_at
        FROM users WHERE id = %s
    ''', (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        user['authenticated'] = True
        return jsonify(user)

    return jsonify({'authenticated': False})

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        UPDATE users SET name = %s, phone = %s, address = %s, city = %s, state = %s, pincode = %s
        WHERE id = %s
    ''', (data.get('name'), data.get('phone'), data.get('address'),
          data.get('city'), data.get('state'), data.get('pincode'),
          session['user_id']))

    cur.close()
    conn.close()

    session['user_name'] = data.get('name')

    return jsonify({'success': True})

# Cart endpoints (session-based for guest users)
@app.route('/api/cart', methods=['GET'])
def get_cart():
    """API endpoint to get cart items"""
    cart = session.get('cart', [])
    if not cart:
        return jsonify([])

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get unique products with quantities
    product_counts = {}
    for pid in cart:
        product_counts[pid] = product_counts.get(pid, 0) + 1

    product_ids = list(product_counts.keys())
    cur.execute(f'SELECT * FROM products WHERE id = ANY(%s)', (product_ids,))
    products = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for p in products:
        p['price'] = float(p['price'])
        p['quantity'] = product_counts[p['id']]
        result.append(p)

    return jsonify(result)

@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """API endpoint to add product to cart"""
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(product_id)
    session.modified = True
    return jsonify({'success': True, 'cart_count': len(session['cart'])})

@app.route('/api/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Remove one instance of product from cart"""
    if 'cart' in session and product_id in session['cart']:
        session['cart'].remove(product_id)
        session.modified = True
    return jsonify({'success': True, 'cart_count': len(session.get('cart', []))})

@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    """API endpoint to clear cart"""
    session.pop('cart', None)
    return jsonify({'success': True})

@app.route('/api/cart/count', methods=['GET'])
def cart_count():
    """Get cart count"""
    return jsonify({'count': len(session.get('cart', []))})

# Order endpoints
@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get user orders"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
        SELECT id, total_amount, status, shipping_address, city, state, pincode,
               payment_method, order_date, delivery_date
        FROM orders
        WHERE user_id = %s
        ORDER BY order_date DESC
    ''', (session['user_id'],))

    orders = cur.fetchall()

    # Get order items for each order
    for order in orders:
        order['total_amount'] = float(order['total_amount'])
        cur.execute('''
            SELECT oi.quantity, oi.price, p.name, p.image_url
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        ''', (order['id'],))
        order['items'] = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login to place order'}), 401

    data = request.get_json()
    cart = session.get('cart', [])

    if not cart:
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get products and calculate total
    product_counts = {}
    for pid in cart:
        product_counts[pid] = product_counts.get(pid, 0) + 1

    product_ids = list(product_counts.keys())
    cur.execute(f'SELECT * FROM products WHERE id = ANY(%s)', (product_ids,))
    products = cur.fetchall()

    total = sum(p['price'] * product_counts[p['id']] for p in products)

    # Set delivery date (7 days from now)
    delivery_date = datetime.now() + timedelta(days=7)

    # Create order
    cur.execute('''
        INSERT INTO orders (user_id, total_amount, status, shipping_address, city, state, pincode, phone, payment_method, delivery_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (session['user_id'], total, 'Processing', data.get('address', ''),
          data.get('city', ''), data.get('state', ''), data.get('pincode', ''),
          data.get('phone', ''), data.get('payment_method', 'COD'), delivery_date))

    order_id = cur.fetchone()['id']

    # Create order items
    for p in products:
        cur.execute('''
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        ''', (order_id, p['id'], product_counts[p['id']], p['price']))

    cur.close()
    conn.close()

    # Clear cart
    session.pop('cart', None)

    return jsonify({'success': True, 'order_id': order_id})

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details with tracking"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
        SELECT id, total_amount, status, shipping_address, city, state, pincode,
               phone, payment_method, order_date, delivery_date
        FROM orders
        WHERE id = %s AND user_id = %s
    ''', (order_id, session['user_id']))

    order = cur.fetchone()

    if not order:
        return jsonify({'error': 'Order not found'}), 404

    # Get order items
    cur.execute('''
        SELECT oi.quantity, oi.price, p.name, p.image_url
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = %s
    ''', (order_id,))

    order['items'] = cur.fetchall()
    order['total_amount'] = float(order['total_amount'])

    # Generate tracking steps based on status
    status_steps = {
        'Processing': ['Order Placed', 'Processing'],
        'Shipped': ['Order Placed', 'Processing', 'Shipped', 'Out for Delivery'],
        'Delivered': ['Order Placed', 'Processing', 'Shipped', 'Out for Delivery', 'Delivered']
    }

    order['tracking_steps'] = status_steps.get(order['status'], status_steps['Processing'])

    cur.close()
    conn.close()

    return jsonify(order)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

# Monitoring API Endpoints
@app.route('/api/monitor/requests')
def get_monitor_requests():
    """Get recent request history"""
    with request_history_lock:
        requests = list(request_history)
    return jsonify({
        'requests': requests,
        'total': len(requests)
    })

@app.route('/api/monitor/services')
def get_monitor_services():
    """Get service status with container/pod information"""
    # Get container/pod info
    hostname = socket.gethostname()
    service_name = os.environ.get('SERVICE_NAME', 'unknown')
    service_tier = os.environ.get('SERVICE_TIER', 'unknown')
    replicas = os.environ.get('REPLICAS', '1')

    # Check database
    db_start = time.time()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        db_latency = round((time.time() - db_start) * 1000, 2)
        db_status = 'healthy'
    except Exception as e:
        db_latency = 0
        db_status = 'unhealthy'

    # Container/Pod info for each service
    services = [
        {
            'name': 'Nginx',
            'type': 'frontend',
            'status': 'healthy',
            'latency_ms': 0,
            'port': 80,
            'description': 'Static file server & reverse proxy',
            'container': {
                'name': 'demo-presentation-1',
                'image': 'demo-presentation:latest',
                'tier': 'presentation',
                'replicas': 1
            }
        },
        {
            'name': 'Flask',
            'type': 'backend',
            'status': 'healthy',
            'latency_ms': 0,
            'port': 5000,
            'description': 'Python API server',
            'container': {
                'name': hostname,
                'image': 'demo-application:latest',
                'tier': 'application',
                'service_name': service_name,
                'replicas': int(replicas)
            }
        },
        {
            'name': 'PostgreSQL',
            'type': 'database',
            'status': db_status,
            'latency_ms': db_latency,
            'port': 5432,
            'description': 'Primary data store',
            'container': {
                'name': 'demo-database-1',
                'image': 'postgres:15-alpine',
                'tier': 'data',
                'replicas': 1
            }
        }
    ]

    return jsonify({
        'services': services,
        'container_info': {
            'hostname': hostname,
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'service_name': service_name,
            'service_tier': service_tier
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/monitor/stats')
def get_monitor_stats():
    """Get aggregate statistics"""
    with request_history_lock:
        total = stats['total_requests']
        errors = stats['total_errors']
        uptime = (datetime.now() - stats['start_time']).total_seconds()

        # Calculate averages from recent history
        recent = list(request_history)
        avg_latency = sum(r['duration_ms'] for r in recent) / len(recent) if recent else 0

        # Endpoint breakdown
        endpoints = {}
        for r in recent:
            path = r['path']
            if path not in endpoints:
                endpoints[path] = {'count': 0, 'total_latency': 0, 'errors': 0}
            endpoints[path]['count'] += 1
            endpoints[path]['total_latency'] += r['duration_ms']
            if r['status'] >= 400:
                endpoints[path]['errors'] += 1

        # Calculate averages for each endpoint
        for path in endpoints:
            count = endpoints[path]['count']
            endpoints[path]['avg_latency'] = round(endpoints[path]['total_latency'] / count, 2)

    return jsonify({
        'total_requests': total,
        'total_errors': errors,
        'error_rate': round((errors / total * 100) if total > 0 else 0, 2),
        'avg_latency_ms': round(avg_latency, 2),
        'uptime_seconds': round(uptime, 0),
        'requests_per_minute': round(total / (uptime / 60) if uptime > 0 else 0, 2),
        'endpoints': endpoints,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/monitor/system')
def get_monitor_system():
    """Get system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return jsonify({
            'cpu_percent': cpu_percent,
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'percent': disk.percent
            }
        })
    except Exception:
        # Fallback if psutil not available
        return jsonify({
            'cpu_percent': 0,
            'memory': {'total_gb': 0, 'used_gb': 0, 'percent': 0},
            'disk': {'total_gb': 0, 'used_gb': 0, 'percent': 0}
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)