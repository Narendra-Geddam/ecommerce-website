import os
import bcrypt
import time
import uuid
import psutil
import socket
import platform
import re
from flask import Flask, jsonify, request, session, make_response, g
from flask_cors import CORS
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import deque
from threading import Lock

app = Flask(__name__)
app_secret_key = os.environ.get('SECRET_KEY')
if not app_secret_key:
    raise RuntimeError('SECRET_KEY environment variable is required')
app.secret_key = app_secret_key

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
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL environment variable is required')

db_pool = pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=DATABASE_URL
)


def get_db():
    conn = db_pool.getconn()
    conn.autocommit = True
    return conn


def release_db(conn):
    if conn is not None:
        db_pool.putconn(conn)

def hash_password(password):
    """Hash password using bcrypt with automatic salt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


EMAIL_RE = re.compile(r'^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$', re.IGNORECASE)
PHONE_RE = re.compile(r'^\d{10}$')
PINCODE_RE = re.compile(r'^\d{6}$')


def normalize_optional_text(value, max_length=None):
    text = str(value or '').strip()
    if max_length is not None:
        text = text[:max_length]
    return text


def normalize_email(value):
    return normalize_optional_text(value, 255).lower()


def normalize_phone(value):
    return re.sub(r'\D', '', str(value or ''))


def validate_name(value):
    name = normalize_optional_text(value, 100)
    if len(name) < 2:
        return False, 'Name must be at least 2 characters'
    return True, name


def validate_email(value):
    email = normalize_email(value)
    if not EMAIL_RE.match(email):
        return False, 'Invalid email format'
    return True, email


def validate_password(value):
    password = str(value or '')
    if len(password) < 8:
        return False, 'Password must be at least 8 characters'
    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return False, 'Password must include at least one letter and one number'
    return True, password


def validate_phone(value, required=False):
    phone = normalize_phone(value)
    if not phone:
        if required:
            return False, 'Phone number is required'
        return True, ''
    if not PHONE_RE.match(phone):
        return False, 'Phone number must be 10 digits'
    return True, phone


def validate_pincode(value, required=False):
    pincode = re.sub(r'\D', '', str(value or ''))
    if not pincode:
        if required:
            return False, 'Pincode is required'
        return True, ''
    if not PINCODE_RE.match(pincode):
        return False, 'Pincode must be 6 digits'
    return True, pincode


def validate_registration_payload(data):
    sanitized = {}

    ok, result = validate_name(data.get('name'))
    if not ok:
        return False, result, None
    sanitized['name'] = result

    ok, result = validate_email(data.get('email'))
    if not ok:
        return False, result, None
    sanitized['email'] = result

    ok, result = validate_password(data.get('password'))
    if not ok:
        return False, result, None
    sanitized['password'] = result

    ok, result = validate_phone(data.get('phone'))
    if not ok:
        return False, result, None
    sanitized['phone'] = result

    ok, result = validate_pincode(data.get('pincode'))
    if not ok:
        return False, result, None
    sanitized['pincode'] = result

    sanitized['address'] = normalize_optional_text(data.get('address'), 255)
    sanitized['city'] = normalize_optional_text(data.get('city'), 100)
    sanitized['state'] = normalize_optional_text(data.get('state'), 100)
    return True, None, sanitized


def validate_profile_payload(data):
    sanitized = {}

    ok, result = validate_name(data.get('name'))
    if not ok:
        return False, result, None
    sanitized['name'] = result

    ok, result = validate_phone(data.get('phone'))
    if not ok:
        return False, result, None
    sanitized['phone'] = result

    ok, result = validate_pincode(data.get('pincode'))
    if not ok:
        return False, result, None
    sanitized['pincode'] = result

    sanitized['address'] = normalize_optional_text(data.get('address'), 255)
    sanitized['city'] = normalize_optional_text(data.get('city'), 100)
    sanitized['state'] = normalize_optional_text(data.get('state'), 100)
    return True, None, sanitized


def validate_shipping_payload(data):
    sanitized = {}

    ok, result = validate_name(data.get('name', 'Guest User'))
    if not ok:
        return False, result, None
    sanitized['name'] = result

    ok, result = validate_phone(data.get('phone'), required=True)
    if not ok:
        return False, result, None
    sanitized['phone'] = result

    ok, result = validate_pincode(data.get('pincode'), required=True)
    if not ok:
        return False, result, None
    sanitized['pincode'] = result

    address = normalize_optional_text(data.get('address'), 255)
    city = normalize_optional_text(data.get('city'), 100)
    state = normalize_optional_text(data.get('state'), 100)
    if not address:
        return False, 'Address is required', None
    if not city:
        return False, 'City is required', None
    if not state:
        return False, 'State is required', None

    sanitized['address'] = address
    sanitized['city'] = city
    sanitized['state'] = state
    sanitized['payment_method'] = normalize_optional_text(data.get('payment_method'), 30) or 'COD'
    return True, None, sanitized

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
        release_db(conn)
        return {'status': 'healthy', 'latency_ms': 0}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

@app.route('/products')
def get_products():
    """API endpoint to get paginated products"""
    category = request.args.get('category')
    search = request.args.get('search')
    raw_page = request.args.get('page', '1')
    raw_page_size = request.args.get('page_size', '12')

    try:
        page = max(1, int(raw_page))
        page_size = min(100, max(1, int(raw_page_size)))
    except ValueError:
        return jsonify({'error': 'Invalid pagination parameters'}), 400

    offset = (page - 1) * page_size

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = 'SELECT * FROM products WHERE 1=1'
    count_query = 'SELECT COUNT(*) AS total FROM products WHERE 1=1'
    params = []

    if category and category != 'All':
        query += ' AND category = %s'
        count_query += ' AND category = %s'
        params.append(category)

    if search:
        query += ' AND (name ILIKE %s OR description ILIKE %s)'
        count_query += ' AND (name ILIKE %s OR description ILIKE %s)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term])

    cur.execute(count_query, params)
    total = cur.fetchone()['total']

    query += ' ORDER BY id LIMIT %s OFFSET %s'
    paginated_params = params + [page_size, offset]

    cur.execute(query, paginated_params)
    products = cur.fetchall()
    cur.close()
    release_db(conn)

    # Convert Decimal to float for JSON serialization
    for p in products:
        p['price'] = float(p['price'])
        p['stock'] = int(p['stock']) if p['stock'] else 0

    total_pages = (total + page_size - 1) // page_size if total else 0

    return jsonify({
        'products': products,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1 and total_pages > 0
        }
    })

@app.route('/products/<int:product_id>')
def get_product(product_id):
    """API endpoint to get a single product"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cur.fetchone()
    cur.close()
    release_db(conn)
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
    release_db(conn)
    return jsonify(['All'] + categories)

# Auth endpoints
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json() or {}

    required = ['name', 'email', 'password']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    is_valid, error, sanitized = validate_registration_payload(data)
    if not is_valid:
        return jsonify({'success': False, 'error': error}), 400

    hashed_pw = hash_password(sanitized['password'])

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute('''
            INSERT INTO users (name, email, password, phone, address, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, email
        ''', (sanitized['name'], sanitized['email'], hashed_pw,
              sanitized['phone'], sanitized['address'],
              sanitized['city'], sanitized['state'], sanitized['pincode']))

        user = cur.fetchone()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']

        return jsonify({'success': True, 'user': user})
    except psycopg2.IntegrityError:
        return jsonify({'success': False, 'error': 'Email already exists'}), 400
    finally:
        cur.close()
        release_db(conn)

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json() or {}

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    email = normalize_email(data.get('email'))
    password = str(data.get('password', ''))
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('''
        SELECT id, name, email, password FROM users
        WHERE email = %s
    ''', (email,))

    user = cur.fetchone()
    cur.close()
    release_db(conn)

    if user and verify_password(password, user['password']):
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
    release_db(conn)

    if user:
        user['authenticated'] = True
        return jsonify(user)

    return jsonify({'authenticated': False})

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    is_valid, error, sanitized = validate_profile_payload(data)
    if not is_valid:
        return jsonify({'success': False, 'error': error}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        UPDATE users SET name = %s, phone = %s, address = %s, city = %s, state = %s, pincode = %s
        WHERE id = %s
    ''', (sanitized['name'], sanitized['phone'], sanitized['address'],
          sanitized['city'], sanitized['state'], sanitized['pincode'],
          session['user_id']))

    cur.close()
    release_db(conn)

    session['user_name'] = sanitized['name']

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
    release_db(conn)

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
    release_db(conn)

    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login to place order'}), 401

    data = request.get_json() or {}
    cart = session.get('cart', [])

    if not cart:
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400

    is_valid, error, sanitized = validate_shipping_payload(data)
    if not is_valid:
        return jsonify({'success': False, 'error': error}), 400

    conn = get_db()
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get products and calculate total
        product_counts = {}
        for pid in cart:
            product_counts[pid] = product_counts.get(pid, 0) + 1

        product_ids = list(product_counts.keys())
        cur.execute('SELECT * FROM products WHERE id = ANY(%s) FOR UPDATE', (product_ids,))
        products = cur.fetchall()

        products_by_id = {p['id']: p for p in products}
        for product_id, quantity in product_counts.items():
            product = products_by_id.get(product_id)
            available_stock = int(product['stock']) if product and product['stock'] is not None else 0
            if not product or available_stock < quantity:
                conn.rollback()
                return jsonify({
                    'success': False,
                    'error': 'Insufficient stock',
                    'product_id': product_id,
                    'available': available_stock,
                    'requested': quantity
                }), 400

        total = sum(p['price'] * product_counts[p['id']] for p in products)

        # Set delivery date (7 days from now)
        delivery_date = datetime.now() + timedelta(days=7)

        # Create order
        cur.execute('''
            INSERT INTO orders (user_id, total_amount, status, shipping_address, city, state, pincode, phone, payment_method, delivery_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (session['user_id'], total, 'Processing', sanitized['address'],
              sanitized['city'], sanitized['state'], sanitized['pincode'],
              sanitized['phone'], sanitized['payment_method'], delivery_date))

        order_id = cur.fetchone()['id']

        # Create order items
        for p in products:
            cur.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            ''', (order_id, p['id'], product_counts[p['id']], p['price']))

            cur.execute('''
                UPDATE products
                SET stock = stock - %s
                WHERE id = %s
            ''', (product_counts[p['id']], p['id']))

            cur.execute('''
                UPDATE inventory
                SET quantity = quantity - %s
                WHERE product_id = %s
            ''', (product_counts[p['id']], p['id']))

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': 'Failed to create order', 'message': str(e)}), 500
    finally:
        conn.autocommit = True
        cur.close()
        release_db(conn)

    # Clear cart only after a successful commit
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
    release_db(conn)

    return jsonify(order)

@app.route('/health')
def health():
    """Health check endpoint for liveness probe"""
    return jsonify({'status': 'healthy', 'service': 'flask'})

@app.route('/ready')
def ready():
    """Readiness probe - checks if app can receive traffic (database connection)"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        release_db(conn)
        return jsonify({
            'status': 'ready',
            'service': 'flask',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'service': 'flask',
            'database': 'disconnected',
            'error': str(e)
        }), 503

@app.route('/live')
def live():
    """Liveness probe - checks if the process is running"""
    return jsonify({'status': 'alive', 'service': 'flask'})

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
        release_db(conn)
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
    app.run(host='0.0.0.0', port=5000, debug=False)
