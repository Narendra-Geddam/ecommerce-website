"""
Order Service

Handles order processing:
- Create orders with transaction management
- Get order history
- Get order details
- Order status management
"""
import os
import sys
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, g
from psycopg2.extras import RealDictCursor

# Add shared libraries to path (in Docker, shared is at /app/shared)
sys.path.insert(0, '/app/shared')

from database.pool import get_connection_pool, get_db_connection
from middleware.logging import setup_logging, request_logger
from validation.input_validators import validate_shipping_payload

app = Flask(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL environment variable is required')
INVENTORY_SERVICE_URL = os.environ.get('INVENTORY_SERVICE_URL', 'http://inventory-service:5005')

# Setup logging
setup_logging('order-service')
request_logger.init_app(app)

# Initialize database pool
db_pool = get_connection_pool(DATABASE_URL)


def get_request_user():
    """Extract user info from request headers (set by API Gateway)"""
    user_id = request.headers.get('X-User-ID')
    if user_id:
        return int(user_id)
    return None


def is_admin_request():
    """Return whether the current request was authenticated as an admin."""
    return request.headers.get('X-User-Is-Admin', '').lower() == 'true'


def calculate_coupon_discount(cursor, coupon_code, subtotal):
    """Validate a coupon and return (coupon_row_or_error, discount_amount)."""
    if not coupon_code:
        return None, 0

    cursor.execute('''
        SELECT code, description, discount_type, discount_value, min_order_amount,
               usage_limit, used_count, active, expires_at
        FROM coupon_codes
        WHERE UPPER(code) = UPPER(%s)
    ''', (coupon_code,))
    coupon = cursor.fetchone()

    if not coupon or not coupon['active']:
        return {'error': 'Coupon code is invalid or inactive'}, 0
    if coupon['expires_at'] and coupon['expires_at'] <= datetime.now():
        return {'error': 'Coupon code has expired'}, 0
    if coupon['usage_limit'] is not None and coupon['used_count'] >= coupon['usage_limit']:
        return {'error': 'Coupon usage limit reached'}, 0

    min_order_amount = float(coupon['min_order_amount'] or 0)
    if subtotal < min_order_amount:
        return {'error': f'Coupon requires a minimum order of ${min_order_amount:.2f}'}, 0

    discount_value = float(coupon['discount_value'])
    if coupon['discount_type'] == 'FIXED':
        discount = min(subtotal, discount_value)
    else:
        discount = round(subtotal * (discount_value / 100), 2)

    coupon['discount_value'] = discount_value
    coupon['min_order_amount'] = min_order_amount
    return coupon, round(discount, 2)


@app.route('/health')
def health():
    """Health check for liveness probe"""
    return jsonify({'status': 'healthy', 'service': 'order-service'})


@app.route('/ready')
def ready():
    """Readiness probe - checks database connection"""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT 1')
        return jsonify({
            'status': 'ready',
            'service': 'order-service',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'service': 'order-service',
            'database': 'disconnected',
            'error': str(e)
        }), 503


@app.route('/live')
def live():
    """Liveness probe"""
    return jsonify({'status': 'alive', 'service': 'order-service'})


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get user's order history"""
    user_id = get_request_user()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    # Pagination
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(50, max(1, int(request.args.get('page_size', 10))))
    offset = (page - 1) * page_size

    try:
        with db_pool.connection() as cursor:
            # Get total count
            cursor.execute('SELECT COUNT(*) as total FROM orders WHERE user_id = %s', (user_id,))
            total = cursor.fetchone()['total']

            # Get orders
            cursor.execute('''
                SELECT id, order_number, total_amount, status, shipping_address, city, state, pincode,
                       payment_method, order_date, delivery_date, coupon_code, discount_amount
                FROM orders
                WHERE user_id = %s
                ORDER BY order_date DESC
                LIMIT %s OFFSET %s
            ''', (user_id, page_size, offset))

            orders = cursor.fetchall()

            # Get order items for each order
            for order in orders:
                order['total_amount'] = float(order['total_amount'])
                order['discount_amount'] = float(order.get('discount_amount') or 0)
                cursor.execute('''
                    SELECT oi.quantity, oi.price, p.name, p.image_url, p.id as product_id
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                ''', (order['id'],))
                order['items'] = cursor.fetchall()

            total_pages = (total + page_size - 1) // page_size

            return jsonify({
                'orders': orders,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages
                }
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch orders',
            'message': str(e)
        }), 500


@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order with transaction management"""
    user_id = get_request_user()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    cart_id = data.get('cart_id')
    coupon_code = str(data.get('coupon_code', '') or '').strip().upper()

    if not cart_id:
        return jsonify({'error': 'Cart ID required'}), 400

    is_valid, error, sanitized = validate_shipping_payload(data)
    if not is_valid:
        return jsonify({'error': error}), 400

    shipping_address = sanitized['address']
    city = sanitized['city']
    state = sanitized['state']
    pincode = sanitized['pincode']
    phone = sanitized['phone']
    payment_method = sanitized['payment_method']

    try:
        # Start transaction
        conn = db_pool.get_connection()
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Get cart items
            cursor.execute('''
                SELECT ci.product_id, ci.quantity, p.price, p.stock, p.name
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                WHERE ci.cart_id = %s
            ''', (cart_id,))

            cart_items = cursor.fetchall()

            if not cart_items:
                conn.rollback()
                return jsonify({'error': 'Cart is empty'}), 400

            product_ids = [item['product_id'] for item in cart_items]
            cursor.execute('''
                SELECT id, stock
                FROM products
                WHERE id = ANY(%s)
                FOR UPDATE
            ''', (product_ids,))
            locked_products = {
                row['id']: int(row['stock']) if row['stock'] is not None else 0
                for row in cursor.fetchall()
            }

            for item in cart_items:
                available_stock = locked_products.get(item['product_id'], 0)
                if available_stock < item['quantity']:
                    conn.rollback()
                    return jsonify({
                        'error': 'Insufficient stock',
                        'product_id': item['product_id'],
                        'product_name': item['name'],
                        'available': available_stock,
                        'requested': item['quantity']
                    }), 400

            # Calculate totals
            subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)
            coupon, discount = calculate_coupon_discount(cursor, coupon_code, subtotal)
            if coupon and coupon.get('error'):
                conn.rollback()
                return jsonify({'error': coupon['error']}), 400
            total = round(subtotal - discount, 2)

            # Set delivery date (7 days from now)
            delivery_date = datetime.now() + timedelta(days=7)

            # Create order with generated order number
            cursor.execute('''
                INSERT INTO orders (user_id, total_amount, status, shipping_address, city, state, pincode, phone, payment_method, delivery_date, coupon_code, discount_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, order_number
            ''', (user_id, total, 'Processing', shipping_address, city, state, pincode, phone, payment_method, delivery_date, coupon_code or None, discount))

            order = cursor.fetchone()
            order_id = order['id']
            order_number = order['order_number']

            # Create order items
            for item in cart_items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                ''', (order_id, item['product_id'], item['quantity'], item['price']))

                cursor.execute('''
                    UPDATE products
                    SET stock = stock - %s
                    WHERE id = %s
                ''', (item['quantity'], item['product_id']))

                cursor.execute('''
                    UPDATE inventory
                    SET quantity = quantity - %s
                    WHERE product_id = %s
                ''', (item['quantity'], item['product_id']))

            # Clear cart
            cursor.execute('DELETE FROM cart_items WHERE cart_id = %s', (cart_id,))
            cursor.execute('DELETE FROM carts WHERE id = %s', (cart_id,))

            if coupon_code:
                cursor.execute('''
                    UPDATE coupon_codes
                    SET used_count = used_count + 1
                    WHERE UPPER(code) = UPPER(%s)
                ''', (coupon_code,))

            # Commit transaction
            conn.commit()

            return jsonify({
                'success': True,
                'order_id': order_id,
                'order_number': order_number,
                'total': total,
                'subtotal': subtotal,
                'discount': discount,
                'coupon_code': coupon_code or None
            })

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'error': 'Failed to create order',
            'message': str(e)
        }), 500


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    user_id = get_request_user()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        with db_pool.connection() as cursor:
            # Get order
            cursor.execute('''
                SELECT id, order_number, total_amount, status, shipping_address, city, state, pincode,
                       phone, payment_method, order_date, delivery_date, coupon_code, discount_amount
                FROM orders
                WHERE id = %s AND user_id = %s
            ''', (order_id, user_id))

            order = cursor.fetchone()

            if not order:
                return jsonify({'error': 'Order not found'}), 404

            order['total_amount'] = float(order['total_amount'])
            order['discount_amount'] = float(order.get('discount_amount') or 0)

            # Get order items
            cursor.execute('''
                SELECT oi.quantity, oi.price, oi.product_id, p.name, p.image_url
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            ''', (order_id,))

            order['items'] = cursor.fetchall()

            # Generate tracking steps based on status
            status_steps = {
                'Processing': ['Order Placed', 'Processing', 'Preparing for Shipment'],
                'Shipped': ['Order Placed', 'Processing', 'Preparing for Shipment', 'Shipped', 'In Transit'],
                'Delivered': ['Order Placed', 'Processing', 'Preparing for Shipment', 'Shipped', 'In Transit', 'Delivered']
            }
            order['tracking_steps'] = status_steps.get(order['status'], status_steps['Processing'])

            return jsonify(order)

    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch order',
            'message': str(e)
        }), 500


@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status (for admin or system use)"""
    user_id = get_request_user()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    new_status = data.get('status')
    is_admin = is_admin_request()

    valid_statuses = ['Processing', 'Shipped', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Valid: {valid_statuses}'}), 400

    try:
        with db_pool.connection() as cursor:
            if is_admin:
                cursor.execute('''
                    UPDATE orders SET status = %s
                    WHERE id = %s
                    RETURNING id, status
                ''', (new_status, order_id))
            else:
                cursor.execute('''
                    UPDATE orders SET status = %s
                    WHERE id = %s AND user_id = %s
                    RETURNING id, status
                ''', (new_status, order_id, user_id))

            order = cursor.fetchone()
            if not order:
                return jsonify({'error': 'Order not found'}), 404

            return jsonify({
                'success': True,
                'order_id': order['id'],
                'status': order['status']
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to update order status',
            'message': str(e)
        }), 500


@app.route('/api/coupons/validate', methods=['GET'])
def validate_coupon():
    """Validate a coupon code against a subtotal."""
    coupon_code = str(request.args.get('code', '') or '').strip().upper()
    subtotal = float(request.args.get('subtotal', 0) or 0)
    if not coupon_code:
        return jsonify({'error': 'Coupon code required'}), 400

    try:
        with db_pool.connection() as cursor:
            coupon, discount = calculate_coupon_discount(cursor, coupon_code, subtotal)
            if coupon and coupon.get('error'):
                return jsonify({'error': coupon['error']}), 400
            return jsonify({
                'valid': True,
                'code': coupon['code'],
                'description': coupon['description'],
                'discount': discount,
                'discount_type': coupon['discount_type'],
                'discount_value': coupon['discount_value'],
                'min_order_amount': coupon['min_order_amount']
            })
    except Exception as e:
        return jsonify({'error': 'Failed to validate coupon', 'message': str(e)}), 500


@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel an order and restore stock."""
    user_id = get_request_user()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    is_admin = is_admin_request()

    try:
        conn = db_pool.get_connection()
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            if is_admin:
                cursor.execute('SELECT id, status, coupon_code FROM orders WHERE id = %s FOR UPDATE', (order_id,))
            else:
                cursor.execute('SELECT id, status, coupon_code FROM orders WHERE id = %s AND user_id = %s FOR UPDATE', (order_id, user_id))
            order = cursor.fetchone()
            if not order:
                conn.rollback()
                return jsonify({'error': 'Order not found'}), 404
            if order['status'] == 'Cancelled':
                conn.rollback()
                return jsonify({'error': 'Order is already cancelled'}), 400
            if order['status'] == 'Delivered':
                conn.rollback()
                return jsonify({'error': 'Delivered orders cannot be cancelled'}), 400

            cursor.execute('SELECT product_id, quantity FROM order_items WHERE order_id = %s', (order_id,))
            for item in cursor.fetchall():
                cursor.execute('UPDATE products SET stock = stock + %s WHERE id = %s', (item['quantity'], item['product_id']))
                cursor.execute('''
                    INSERT INTO inventory (product_id, quantity, reserved_quantity)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (product_id)
                    DO UPDATE SET quantity = inventory.quantity + EXCLUDED.quantity
                ''', (item['product_id'], item['quantity']))

            if order.get('coupon_code'):
                cursor.execute('''
                    UPDATE coupon_codes
                    SET used_count = GREATEST(used_count - 1, 0)
                    WHERE UPPER(code) = UPPER(%s)
                ''', (order['coupon_code'],))

            cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE id = %s", (order_id,))
            conn.commit()
            return jsonify({'success': True, 'order_id': order_id, 'status': 'Cancelled'})
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({'error': 'Failed to cancel order', 'message': str(e)}), 500


@app.route('/api/admin/orders', methods=['GET'])
def admin_get_orders():
    """Get all orders for the admin panel."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    page = max(1, int(request.args.get('page', 1)))
    page_size = min(50, max(1, int(request.args.get('page_size', 20))))
    offset = (page - 1) * page_size

    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT COUNT(*) AS total FROM orders')
            total = cursor.fetchone()['total']
            cursor.execute('''
                SELECT id, user_id, order_number, total_amount, status, shipping_address, city, state, pincode,
                       payment_method, order_date, delivery_date, coupon_code, discount_amount
                FROM orders
                ORDER BY order_date DESC
                LIMIT %s OFFSET %s
            ''', (page_size, offset))
            orders = cursor.fetchall()
            for order in orders:
                order['total_amount'] = float(order['total_amount'])
                order['discount_amount'] = float(order.get('discount_amount') or 0)
            total_pages = (total + page_size - 1) // page_size
            return jsonify({
                'orders': orders,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages
                }
            })
    except Exception as e:
        return jsonify({'error': 'Failed to fetch admin orders', 'message': str(e)}), 500


@app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
def admin_update_order_status(order_id):
    """Update an order status from the admin panel."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403
    return update_order_status(order_id)


@app.route('/api/admin/coupons', methods=['GET', 'POST'])
def admin_coupons():
    """List or create coupons for the admin portal."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'GET':
        try:
            with db_pool.connection() as cursor:
                cursor.execute('''
                    SELECT id, code, description, discount_type, discount_value, min_order_amount,
                           usage_limit, used_count, active, expires_at, created_at
                    FROM coupon_codes
                    ORDER BY created_at DESC, id DESC
                ''')
                coupons = cursor.fetchall()
                for coupon in coupons:
                    coupon['discount_value'] = float(coupon['discount_value'])
                    coupon['min_order_amount'] = float(coupon['min_order_amount'] or 0)
                return jsonify({'coupons': coupons})
        except Exception as e:
            return jsonify({'error': 'Failed to fetch coupons', 'message': str(e)}), 500

    data = request.get_json() or {}
    code = str(data.get('code', '')).strip().upper()
    description = str(data.get('description', '')).strip()
    discount_type = str(data.get('discount_type', 'PERCENT')).strip().upper()
    expires_at = str(data.get('expires_at', '')).strip() or None

    try:
        discount_value = float(data.get('discount_value', 0))
        min_order_amount = float(data.get('min_order_amount', 0) or 0)
        usage_limit = data.get('usage_limit')
        usage_limit = int(usage_limit) if usage_limit not in (None, '', 'null') else None
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coupon numeric values'}), 400

    if not code or discount_type not in ('PERCENT', 'FIXED') or discount_value <= 0:
        return jsonify({'error': 'Valid code, discount type, and discount value are required'}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                INSERT INTO coupon_codes
                    (code, description, discount_type, discount_value, min_order_amount, usage_limit, active, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NULLIF(%s, '')::timestamp)
                RETURNING id, code, description, discount_type, discount_value, min_order_amount,
                          usage_limit, used_count, active, expires_at
            ''', (
                code, description, discount_type, discount_value, min_order_amount,
                usage_limit, bool(data.get('active', True)), expires_at or ''
            ))
            coupon = cursor.fetchone()
            coupon['discount_value'] = float(coupon['discount_value'])
            coupon['min_order_amount'] = float(coupon['min_order_amount'] or 0)
            return jsonify({'success': True, 'coupon': coupon}), 201
    except Exception as e:
        if 'duplicate' in str(e).lower():
            return jsonify({'error': 'Coupon code already exists'}), 400
        return jsonify({'error': 'Failed to create coupon', 'message': str(e)}), 500


@app.route('/api/admin/coupons/<int:coupon_id>', methods=['PUT', 'DELETE'])
def admin_coupon_detail(coupon_id):
    """Update or delete a coupon."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'DELETE':
        try:
            with db_pool.connection() as cursor:
                cursor.execute('DELETE FROM coupon_codes WHERE id = %s RETURNING id', (coupon_id,))
                deleted = cursor.fetchone()
                if not deleted:
                    return jsonify({'error': 'Coupon not found'}), 404
                return jsonify({'success': True, 'coupon_id': coupon_id})
        except Exception as e:
            return jsonify({'error': 'Failed to delete coupon', 'message': str(e)}), 500

    data = request.get_json() or {}
    code = str(data.get('code', '')).strip().upper()
    description = str(data.get('description', '')).strip()
    discount_type = str(data.get('discount_type', 'PERCENT')).strip().upper()
    expires_at = str(data.get('expires_at', '')).strip() or None

    try:
        discount_value = float(data.get('discount_value', 0))
        min_order_amount = float(data.get('min_order_amount', 0) or 0)
        usage_limit = data.get('usage_limit')
        usage_limit = int(usage_limit) if usage_limit not in (None, '', 'null') else None
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coupon numeric values'}), 400

    if not code or discount_type not in ('PERCENT', 'FIXED') or discount_value <= 0:
        return jsonify({'error': 'Valid code, discount type, and discount value are required'}), 400

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                UPDATE coupon_codes
                SET code = %s, description = %s, discount_type = %s, discount_value = %s,
                    min_order_amount = %s, usage_limit = %s, active = %s, expires_at = NULLIF(%s, '')::timestamp
                WHERE id = %s
                RETURNING id, code, description, discount_type, discount_value, min_order_amount,
                          usage_limit, used_count, active, expires_at
            ''', (
                code, description, discount_type, discount_value, min_order_amount,
                usage_limit, bool(data.get('active', True)), expires_at or '', coupon_id
            ))
            coupon = cursor.fetchone()
            if not coupon:
                return jsonify({'error': 'Coupon not found'}), 404
            coupon['discount_value'] = float(coupon['discount_value'])
            coupon['min_order_amount'] = float(coupon['min_order_amount'] or 0)
            return jsonify({'success': True, 'coupon': coupon})
    except Exception as e:
        if 'duplicate' in str(e).lower():
            return jsonify({'error': 'Coupon code already exists'}), 400
        return jsonify({'error': 'Failed to update coupon', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)
