"""
Product Service

Handles product and category management:
- List products with pagination
- Get single product details
- List categories
- Search and filter products
"""
import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, g
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

# Add shared libraries to path (in Docker, shared is at /app/shared)
sys.path.insert(0, '/app/shared')

from database.pool import get_connection_pool, get_db_connection
from middleware.logging import setup_logging, request_logger

app = Flask(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL environment variable is required')
DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', 20))
MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', 100))
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/app/uploads')
ALLOWED_UPLOAD_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}

# Setup logging
setup_logging('product-service')
request_logger.init_app(app)

# Initialize database pool
db_pool = get_connection_pool(DATABASE_URL)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_request_user():
    user_id = request.headers.get('X-User-ID')
    if user_id:
        return {
            'id': int(user_id),
            'name': request.headers.get('X-User-Name', 'ShopEasy User')
        }
    return None


def is_admin_request():
    return request.headers.get('X-User-Is-Admin', '').lower() == 'true'


def normalize_image_url(image_url: str) -> str:
    """Return a safe image path for stored UI records."""
    value = str(image_url or '').strip()
    return value


def validate_banner_payload(data):
    """Validate admin banner payload."""
    title = str(data.get('title', '')).strip()
    if not title:
        return None, 'Banner title is required'

    banner = {
        'title': title,
        'subtitle': str(data.get('subtitle', '')).strip(),
        'image_url': normalize_image_url(data.get('image_url', '')),
        'link_url': str(data.get('link_url', '')).strip() or '/',
        'badge': str(data.get('badge', '')).strip(),
        'background_color': str(data.get('background_color', '')).strip() or '#1f3c88',
        'text_color': str(data.get('text_color', '')).strip() or '#ffffff',
        'active': bool(data.get('active', True)),
    }

    try:
        banner['sort_order'] = int(data.get('sort_order', 0) or 0)
    except (TypeError, ValueError):
        return None, 'Banner sort order must be a number'

    return banner, None


def save_banner_upload(file_storage):
    """Persist an uploaded banner image and return its public static path."""
    if not file_storage or not file_storage.filename:
        return None, 'Banner image file is required'

    original_name = secure_filename(file_storage.filename)
    _, extension = os.path.splitext(original_name.lower())
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        return None, 'Only PNG, JPG, JPEG, WEBP, and GIF images are allowed'

    filename = f"banner-{int(datetime.utcnow().timestamp())}-{original_name}"
    destination = os.path.join(UPLOAD_DIR, filename)
    file_storage.save(destination)
    return f'/static/uploads/{filename}', None


@app.route('/health')
def health():
    """Health check for liveness probe"""
    return jsonify({'status': 'healthy', 'service': 'product-service'})


@app.route('/ready')
def ready():
    """Readiness probe - checks database connection"""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT 1')
        return jsonify({
            'status': 'ready',
            'service': 'product-service',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'service': 'product-service',
            'database': 'disconnected',
            'error': str(e)
        }), 503


@app.route('/live')
def live():
    """Liveness probe"""
    return jsonify({'status': 'alive', 'service': 'product-service'})


@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products with pagination, filtering, and search"""
    # Pagination parameters
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(MAX_PAGE_SIZE, max(1, int(request.args.get('page_size', DEFAULT_PAGE_SIZE))))
    offset = (page - 1) * page_size

    # Filter parameters
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc').upper()

    # Validate sort parameters
    valid_sort_fields = ['id', 'name', 'price', 'category', 'stock', 'created_at']
    if sort_by not in valid_sort_fields:
        sort_by = 'id'
    if sort_order not in ['ASC', 'DESC']:
        sort_order = 'ASC'

    try:
        with db_pool.connection() as cursor:
            # Build query
            query = '''
                SELECT p.*,
                       COALESCE((
                           SELECT ROUND(AVG(pr.rating)::numeric, 1)
                           FROM product_reviews pr
                           WHERE pr.product_id = p.id
                       ), 0) AS avg_rating,
                       (
                           SELECT COUNT(*)
                           FROM product_reviews pr
                           WHERE pr.product_id = p.id
                       ) AS review_count
                FROM products p
                WHERE p.is_active = TRUE
            '''
            count_query = 'SELECT COUNT(*) as total FROM products WHERE is_active = TRUE'
            params = []

            if category and category.lower() != 'all':
                query += ' AND category = %s'
                count_query += ' AND category = %s'
                params.append(category)

            if search:
                query += ' AND (name ILIKE %s OR description ILIKE %s)'
                count_query += ' AND (name ILIKE %s OR description ILIKE %s)'
                search_term = f'%{search}%'
                params.extend([search_term, search_term])

            if min_price:
                query += ' AND price >= %s'
                count_query += ' AND price >= %s'
                params.append(float(min_price))

            if max_price:
                query += ' AND price <= %s'
                count_query += ' AND price <= %s'
                params.append(float(max_price))

            # Get total count
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # Add sorting and pagination
            query += f' ORDER BY {sort_by} {sort_order}'
            query += ' LIMIT %s OFFSET %s'
            params.extend([page_size, offset])

            cursor.execute(query, params)
            products = cursor.fetchall()

            # Convert Decimal to float for JSON serialization
            for p in products:
                p['price'] = float(p['price'])
                p['stock'] = int(p['stock']) if p['stock'] else 0
                p['avg_rating'] = float(p['avg_rating']) if p.get('avg_rating') is not None else 0
                p['review_count'] = int(p.get('review_count') or 0)

            # Calculate pagination metadata
            total_pages = (total + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            return jsonify({
                'products': products,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                }
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch products',
            'message': str(e)
        }), 500


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT p.*,
                       COALESCE((
                           SELECT ROUND(AVG(pr.rating)::numeric, 1)
                           FROM product_reviews pr
                           WHERE pr.product_id = p.id
                       ), 0) AS avg_rating,
                       (
                           SELECT COUNT(*)
                           FROM product_reviews pr
                           WHERE pr.product_id = p.id
                       ) AS review_count
                FROM products p
                WHERE p.id = %s AND p.is_active = TRUE
            ''', (product_id,))
            product = cursor.fetchone()

            if product:
                product['price'] = float(product['price'])
                product['stock'] = int(product['stock']) if product['stock'] else 0
                product['avg_rating'] = float(product['avg_rating']) if product.get('avg_rating') is not None else 0
                product['review_count'] = int(product.get('review_count') or 0)
                return jsonify(product)

            return jsonify({'error': 'Product not found'}), 404

    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch product',
            'message': str(e)
        }), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT DISTINCT category
                FROM products
                WHERE is_active = TRUE
                ORDER BY category
            ''')
            categories = [row['category'] for row in cursor.fetchall()]

            return jsonify(['All'] + categories)

    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch categories',
            'message': str(e)
        }), 500


@app.route('/api/products/search', methods=['GET'])
def search_products():
    """Advanced product search with filters"""
    query_text = request.args.get('q', '')
    category = request.args.get('category')
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(MAX_PAGE_SIZE, max(1, int(request.args.get('page_size', DEFAULT_PAGE_SIZE))))
    offset = (page - 1) * page_size

    if not query_text:
        return jsonify({'error': 'Search query required'}), 400

    try:
        with db_pool.connection() as cursor:
            # Use PostgreSQL full-text search
            sql = '''
                SELECT * FROM products
                WHERE to_tsvector('english', name || ' ' || coalesce(description, '')) @@ plainto_tsquery('english', %s)
            '''
            params = [query_text]

            if category and category.lower() != 'all':
                sql += ' AND category = %s'
                params.append(category)

            sql += ' LIMIT %s OFFSET %s'
            params.extend([page_size, offset])

            cursor.execute(sql, params)
            products = cursor.fetchall()

            for p in products:
                p['price'] = float(p['price'])
                p['stock'] = int(p['stock']) if p['stock'] else 0

            return jsonify({
                'products': products,
                'query': query_text,
                'page': page
            })

    except Exception as e:
            return jsonify({
                'error': 'Search failed',
                'message': str(e)
            }), 500


@app.route('/api/homepage/content', methods=['GET'])
def get_homepage_content():
    """Return public homepage banner and offer content."""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT id, title, subtitle, image_url, link_url, badge, background_color,
                       text_color, sort_order
                FROM homepage_banners
                WHERE active = TRUE
                ORDER BY sort_order ASC, id ASC
            ''')
            banners = cursor.fetchall()

            cursor.execute('''
                SELECT id, title, description, coupon_code, cta_label, cta_link,
                       highlight_text, sort_order
                FROM homepage_offers
                WHERE active = TRUE
                ORDER BY sort_order ASC, id ASC
            ''')
            offers = cursor.fetchall()

            return jsonify({'banners': banners, 'offers': offers})
    except Exception as e:
        return jsonify({'error': 'Failed to load homepage content', 'message': str(e)}), 500


@app.route('/api/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Get reviews for a product."""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT id, user_id, user_name, rating, comment, created_at
                FROM product_reviews
                WHERE product_id = %s
                ORDER BY created_at DESC
            ''', (product_id,))
            reviews = cursor.fetchall()
            return jsonify({
                'product_id': product_id,
                'reviews': reviews,
                'count': len(reviews)
            })
    except Exception as e:
        return jsonify({'error': 'Failed to fetch reviews', 'message': str(e)}), 500


@app.route('/api/products/<int:product_id>/reviews', methods=['POST'])
def add_product_review(product_id):
    """Create or update a review for a product."""
    user = get_request_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    rating = int(data.get('rating', 0))
    comment = str(data.get('comment', '')).strip()

    if rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT id FROM products WHERE id = %s', (product_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Product not found'}), 404

            cursor.execute('''
                INSERT INTO product_reviews (product_id, user_id, user_name, rating, comment)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (product_id, user_id)
                DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    rating = EXCLUDED.rating,
                    comment = EXCLUDED.comment,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, rating, comment
            ''', (product_id, user['id'], user['name'], rating, comment))
            review = cursor.fetchone()
            return jsonify({'success': True, 'review': review})
    except Exception as e:
        return jsonify({'error': 'Failed to save review', 'message': str(e)}), 500


@app.route('/api/wishlist', methods=['GET'])
def get_wishlist():
    """Get the authenticated user's wishlist."""
    user = get_request_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                INSERT INTO wishlists (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
            ''', (user['id'],))
            cursor.execute('''
                SELECT p.id, p.name, p.description, p.price, p.image_url, p.category, p.stock,
                       wi.created_at as added_at
                FROM wishlists w
                JOIN wishlist_items wi ON wi.wishlist_id = w.id
                JOIN products p ON p.id = wi.product_id
                WHERE w.user_id = %s
                ORDER BY wi.created_at DESC
            ''', (user['id'],))
            items = cursor.fetchall()
            for item in items:
                item['price'] = float(item['price'])
                item['stock'] = int(item['stock']) if item['stock'] else 0
            return jsonify({'items': items, 'count': len(items)})
    except Exception as e:
        return jsonify({'error': 'Failed to fetch wishlist', 'message': str(e)}), 500


@app.route('/api/wishlist/add/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    """Add a product to the authenticated user's wishlist."""
    user = get_request_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT id FROM products WHERE id = %s', (product_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Product not found'}), 404

            cursor.execute('''
                INSERT INTO wishlists (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
            ''', (user['id'],))
            cursor.execute('SELECT id FROM wishlists WHERE user_id = %s', (user['id'],))
            wishlist_id = cursor.fetchone()['id']
            cursor.execute('''
                INSERT INTO wishlist_items (wishlist_id, product_id)
                VALUES (%s, %s)
                ON CONFLICT (wishlist_id, product_id) DO NOTHING
            ''', (wishlist_id, product_id))
            cursor.execute('SELECT COUNT(*) AS count FROM wishlist_items WHERE wishlist_id = %s', (wishlist_id,))
            return jsonify({'success': True, 'count': cursor.fetchone()['count']})
    except Exception as e:
        return jsonify({'error': 'Failed to add to wishlist', 'message': str(e)}), 500


@app.route('/api/wishlist/remove/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id):
    """Remove a product from the authenticated user's wishlist."""
    user = get_request_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT id FROM wishlists WHERE user_id = %s', (user['id'],))
            wishlist = cursor.fetchone()
            if not wishlist:
                return jsonify({'success': True, 'count': 0})
            cursor.execute('DELETE FROM wishlist_items WHERE wishlist_id = %s AND product_id = %s', (wishlist['id'], product_id))
            cursor.execute('SELECT COUNT(*) AS count FROM wishlist_items WHERE wishlist_id = %s', (wishlist['id'],))
            return jsonify({'success': True, 'count': cursor.fetchone()['count']})
    except Exception as e:
        return jsonify({'error': 'Failed to remove from wishlist', 'message': str(e)}), 500


@app.route('/api/admin/products', methods=['GET', 'POST'])
def admin_products():
    """Admin product listing and creation."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'GET':
        page = max(1, int(request.args.get('page', 1)))
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.args.get('page_size', 25))))
        offset = (page - 1) * page_size
        search = str(request.args.get('search', '') or '').strip()

        try:
            with db_pool.connection() as cursor:
                where = 'WHERE 1=1'
                params = []
                if search:
                    where += ' AND (name ILIKE %s OR description ILIKE %s OR category ILIKE %s)'
                    term = f'%{search}%'
                    params.extend([term, term, term])

                cursor.execute(f'SELECT COUNT(*) AS total FROM products {where}', params)
                total = cursor.fetchone()['total']

                cursor.execute(f'''
                    SELECT id, name, description, price, image_url, category, stock, is_active, created_at
                    FROM products
                    {where}
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                ''', params + [page_size, offset])
                products = cursor.fetchall()
                for product in products:
                    product['price'] = float(product['price'])
                    product['stock'] = int(product['stock'] or 0)

                return jsonify({
                    'products': products,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': (total + page_size - 1) // page_size
                    }
                })
        except Exception as e:
            return jsonify({'error': 'Failed to fetch admin products', 'message': str(e)}), 500

    data = request.get_json() or {}
    name = str(data.get('name', '')).strip()
    description = str(data.get('description', '')).strip()
    category = str(data.get('category', '')).strip()
    image_url = str(data.get('image_url', '')).strip()

    try:
        price = float(data.get('price', 0))
        stock = max(0, int(data.get('stock', 0)))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid price or stock'}), 400

    if not name or price <= 0 or not category:
        return jsonify({'error': 'Name, category, and positive price are required'}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                INSERT INTO products (name, description, price, image_url, category, stock, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                RETURNING id, name, description, price, image_url, category, stock, is_active
            ''', (name, description, price, image_url, category, stock))
            product = cursor.fetchone()
            cursor.execute('''
                INSERT INTO inventory (product_id, quantity, reserved_quantity)
                VALUES (%s, %s, 0)
                ON CONFLICT (product_id)
                DO UPDATE SET quantity = EXCLUDED.quantity
            ''', (product['id'], stock))
            product['price'] = float(product['price'])
            return jsonify({'success': True, 'product': product}), 201
    except Exception as e:
        return jsonify({'error': 'Failed to create product', 'message': str(e)}), 500


@app.route('/api/admin/products/<int:product_id>', methods=['PUT', 'DELETE'])
def admin_product_detail(product_id):
    """Admin product editing and archive toggle."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'DELETE':
        try:
            with db_pool.connection() as cursor:
                cursor.execute('''
                    UPDATE products
                    SET is_active = FALSE
                    WHERE id = %s
                    RETURNING id, name, is_active
                ''', (product_id,))
                product = cursor.fetchone()
                if not product:
                    return jsonify({'error': 'Product not found'}), 404
                return jsonify({'success': True, 'product': product})
        except Exception as e:
            return jsonify({'error': 'Failed to archive product', 'message': str(e)}), 500

    data = request.get_json() or {}
    name = str(data.get('name', '')).strip()
    description = str(data.get('description', '')).strip()
    category = str(data.get('category', '')).strip()
    image_url = str(data.get('image_url', '')).strip()

    try:
        price = float(data.get('price', 0))
        stock = max(0, int(data.get('stock', 0)))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid price or stock'}), 400

    is_active = bool(data.get('is_active', True))

    if not name or price <= 0 or not category:
        return jsonify({'error': 'Name, category, and positive price are required'}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                UPDATE products
                SET name = %s, description = %s, price = %s, image_url = %s,
                    category = %s, stock = %s, is_active = %s
                WHERE id = %s
                RETURNING id, name, description, price, image_url, category, stock, is_active
            ''', (name, description, price, image_url, category, stock, is_active, product_id))
            product = cursor.fetchone()
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            cursor.execute('''
                INSERT INTO inventory (product_id, quantity, reserved_quantity)
                VALUES (%s, %s, 0)
                ON CONFLICT (product_id)
                DO UPDATE SET quantity = EXCLUDED.quantity
            ''', (product_id, stock))
            product['price'] = float(product['price'])
            return jsonify({'success': True, 'product': product})
    except Exception as e:
        return jsonify({'error': 'Failed to update product', 'message': str(e)}), 500


@app.route('/api/admin/homepage/banners', methods=['GET', 'POST'])
def admin_homepage_banners():
    """Admin banner management."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'GET':
        try:
            with db_pool.connection() as cursor:
                cursor.execute('''
                    SELECT id, title, subtitle, image_url, link_url, badge, background_color,
                           text_color, sort_order, active
                    FROM homepage_banners
                    ORDER BY sort_order ASC, id ASC
                ''')
                return jsonify({'banners': cursor.fetchall()})
        except Exception as e:
            return jsonify({'error': 'Failed to fetch banners', 'message': str(e)}), 500

    data = request.get_json() or {}
    banner, error = validate_banner_payload(data)
    if error:
        return jsonify({'error': error}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                INSERT INTO homepage_banners
                    (title, subtitle, image_url, link_url, badge, background_color, text_color, sort_order, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, title, subtitle, image_url, link_url, badge, background_color, text_color, sort_order, active
            ''', (
                banner['title'],
                banner['subtitle'],
                banner['image_url'],
                banner['link_url'],
                banner['badge'],
                banner['background_color'],
                banner['text_color'],
                banner['sort_order'],
                banner['active']
            ))
            return jsonify({'success': True, 'banner': cursor.fetchone()}), 201
    except Exception as e:
        return jsonify({'error': 'Failed to create banner', 'message': str(e)}), 500


@app.route('/api/admin/homepage/banners/upload', methods=['POST'])
def admin_homepage_banner_upload():
    """Upload a banner image and return a public path served by nginx."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    image_url, error = save_banner_upload(request.files.get('image'))
    if error:
        return jsonify({'error': error}), 400

    return jsonify({'success': True, 'image_url': image_url}), 201


@app.route('/api/admin/homepage/banners/<int:banner_id>', methods=['PUT', 'DELETE'])
def admin_homepage_banner_detail(banner_id):
    """Update or remove a homepage banner."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'DELETE':
        try:
            with db_pool.connection() as cursor:
                cursor.execute('DELETE FROM homepage_banners WHERE id = %s RETURNING id', (banner_id,))
                deleted = cursor.fetchone()
                if not deleted:
                    return jsonify({'error': 'Banner not found'}), 404
                return jsonify({'success': True, 'banner_id': banner_id})
        except Exception as e:
            return jsonify({'error': 'Failed to delete banner', 'message': str(e)}), 500

    data = request.get_json() or {}
    banner, error = validate_banner_payload(data)
    if error:
        return jsonify({'error': error}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                UPDATE homepage_banners
                SET title = %s, subtitle = %s, image_url = %s, link_url = %s, badge = %s,
                    background_color = %s, text_color = %s, sort_order = %s, active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, title, subtitle, image_url, link_url, badge, background_color, text_color, sort_order, active
            ''', (
                banner['title'],
                banner['subtitle'],
                banner['image_url'],
                banner['link_url'],
                banner['badge'],
                banner['background_color'],
                banner['text_color'],
                banner['sort_order'],
                banner['active'],
                banner_id
            ))
            banner = cursor.fetchone()
            if not banner:
                return jsonify({'error': 'Banner not found'}), 404
            return jsonify({'success': True, 'banner': banner})
    except Exception as e:
        return jsonify({'error': 'Failed to update banner', 'message': str(e)}), 500


@app.route('/api/admin/homepage/offers', methods=['GET', 'POST'])
def admin_homepage_offers():
    """Admin homepage offer management."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'GET':
        try:
            with db_pool.connection() as cursor:
                cursor.execute('''
                    SELECT id, title, description, coupon_code, cta_label, cta_link,
                           highlight_text, sort_order, active
                    FROM homepage_offers
                    ORDER BY sort_order ASC, id ASC
                ''')
                return jsonify({'offers': cursor.fetchall()})
        except Exception as e:
            return jsonify({'error': 'Failed to fetch offers', 'message': str(e)}), 500

    data = request.get_json() or {}
    title = str(data.get('title', '')).strip()
    if not title:
        return jsonify({'error': 'Offer title is required'}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                INSERT INTO homepage_offers
                    (title, description, coupon_code, cta_label, cta_link, highlight_text, sort_order, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, title, description, coupon_code, cta_label, cta_link, highlight_text, sort_order, active
            ''', (
                title,
                str(data.get('description', '')).strip(),
                str(data.get('coupon_code', '')).strip().upper(),
                str(data.get('cta_label', '')).strip() or 'Shop Now',
                str(data.get('cta_link', '')).strip() or '/',
                str(data.get('highlight_text', '')).strip(),
                int(data.get('sort_order', 0) or 0),
                bool(data.get('active', True))
            ))
            return jsonify({'success': True, 'offer': cursor.fetchone()}), 201
    except Exception as e:
        return jsonify({'error': 'Failed to create offer', 'message': str(e)}), 500


@app.route('/api/admin/homepage/offers/<int:offer_id>', methods=['PUT', 'DELETE'])
def admin_homepage_offer_detail(offer_id):
    """Update or delete a homepage offer."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'DELETE':
        try:
            with db_pool.connection() as cursor:
                cursor.execute('DELETE FROM homepage_offers WHERE id = %s RETURNING id', (offer_id,))
                deleted = cursor.fetchone()
                if not deleted:
                    return jsonify({'error': 'Offer not found'}), 404
                return jsonify({'success': True, 'offer_id': offer_id})
        except Exception as e:
            return jsonify({'error': 'Failed to delete offer', 'message': str(e)}), 500

    data = request.get_json() or {}
    title = str(data.get('title', '')).strip()
    if not title:
        return jsonify({'error': 'Offer title is required'}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                UPDATE homepage_offers
                SET title = %s, description = %s, coupon_code = %s, cta_label = %s,
                    cta_link = %s, highlight_text = %s, sort_order = %s, active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, title, description, coupon_code, cta_label, cta_link, highlight_text, sort_order, active
            ''', (
                title,
                str(data.get('description', '')).strip(),
                str(data.get('coupon_code', '')).strip().upper(),
                str(data.get('cta_label', '')).strip() or 'Shop Now',
                str(data.get('cta_link', '')).strip() or '/',
                str(data.get('highlight_text', '')).strip(),
                int(data.get('sort_order', 0) or 0),
                bool(data.get('active', True)),
                offer_id
            ))
            offer = cursor.fetchone()
            if not offer:
                return jsonify({'error': 'Offer not found'}), 404
            return jsonify({'success': True, 'offer': offer})
    except Exception as e:
        return jsonify({'error': 'Failed to update offer', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)
