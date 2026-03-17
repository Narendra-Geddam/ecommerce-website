"""
Cart Service

Handles shopping cart operations:
- Get cart contents
- Add items to cart
- Remove items from cart
- Clear cart
- Cart count
- Guest cart support
- Cart merge on login
"""
import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, g
from psycopg2.extras import RealDictCursor
import uuid

# Add shared libraries to path (in Docker, shared is at /app/shared)
sys.path.insert(0, '/app/shared')

from database.pool import get_connection_pool, get_db_connection
from middleware.logging import setup_logging, request_logger

app = Flask(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL environment variable is required')

# Setup logging
setup_logging('cart-service')
request_logger.init_app(app)

# Initialize database pool
db_pool = get_connection_pool(DATABASE_URL)


def get_request_user():
    """Extract user info from request headers (set by API Gateway)"""
    user_id = request.headers.get('X-User-ID')
    if user_id:
        return int(user_id)
    return None


def get_or_create_cart(user_id=None):
    """Get existing cart or create a new one"""
    with db_pool.connection() as cursor:
        if user_id:
            # Get user's cart
            cursor.execute('SELECT id FROM carts WHERE user_id = %s', (user_id,))
            cart = cursor.fetchone()
            if cart:
                return str(cart['id'])

            # Create new cart for user
            cursor.execute('''
                INSERT INTO carts (user_id) VALUES (%s)
                RETURNING id
            ''', (user_id,))
        else:
            # Create guest cart
            cursor.execute('''
                INSERT INTO carts (user_id) VALUES (NULL)
                RETURNING id
            ''', ())

        return str(cursor.fetchone()['id'])


def merge_guest_cart_to_user_cart(guest_cart_id, user_id):
    """Merge guest cart items into user's cart after login"""
    with db_pool.connection() as cursor:
        # Get or create user's cart
        cursor.execute('SELECT id FROM carts WHERE user_id = %s', (user_id,))
        user_cart = cursor.fetchone()

        if user_cart:
            user_cart_id = str(user_cart['id'])
        else:
            cursor.execute('''
                INSERT INTO carts (user_id) VALUES (%s)
                RETURNING id
            ''', (user_id,))
            user_cart_id = str(cursor.fetchone()['id'])

        # Get guest cart items
        cursor.execute('''
            SELECT product_id, quantity FROM cart_items
            WHERE cart_id = %s
        ''', (guest_cart_id,))
        guest_items = cursor.fetchall()

        # Merge items into user cart
        for item in guest_items:
            cursor.execute('''
                INSERT INTO cart_items (cart_id, product_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (cart_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + %s
            ''', (user_cart_id, item['product_id'], item['quantity'], item['quantity']))

        # Delete guest cart
        cursor.execute('DELETE FROM carts WHERE id = %s', (guest_cart_id,))

        return user_cart_id


@app.route('/health')
def health():
    """Health check for liveness probe"""
    return jsonify({'status': 'healthy', 'service': 'cart-service'})


@app.route('/ready')
def ready():
    """Readiness probe - checks database connection"""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT 1')
        return jsonify({
            'status': 'ready',
            'service': 'cart-service',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'service': 'cart-service',
            'database': 'disconnected',
            'error': str(e)
        }), 503


@app.route('/live')
def live():
    """Liveness probe"""
    return jsonify({'status': 'alive', 'service': 'cart-service'})


@app.route('/api/cart', methods=['GET'])
def get_cart():
    """Get cart contents"""
    user_id = get_request_user()
    cart_id = request.headers.get('X-Cart-ID')  # For guest carts

    try:
        with db_pool.connection() as cursor:
            cart_to_use = None

            if user_id:
                # Get user's cart
                cursor.execute('SELECT id FROM carts WHERE user_id = %s', (user_id,))
                cart = cursor.fetchone()
                if cart:
                    cart_to_use = str(cart['id'])
            elif cart_id:
                # Get guest cart by ID
                try:
                    cart_uuid = uuid.UUID(cart_id)
                    cursor.execute('SELECT id FROM carts WHERE id = %s', (str(cart_uuid),))
                    cart = cursor.fetchone()
                    if cart:
                        cart_to_use = str(cart['id'])
                except ValueError:
                    pass

            if not cart_to_use:
                return jsonify({'items': [], 'cart_id': None, 'total': 0})

            # Get cart items with product details
            cursor.execute('''
                SELECT ci.quantity, ci.product_id, p.id, p.name, p.description,
                       p.price, p.image_url, p.category, p.stock
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                WHERE ci.cart_id = %s
            ''', (cart_to_use,))

            items = cursor.fetchall()
            total = 0

            result = []
            for item in items:
                price = float(item['price'])
                quantity = item['quantity']
                total += price * quantity

                result.append({
                    'id': item['product_id'],
                    'name': item['name'],
                    'description': item['description'],
                    'price': price,
                    'image_url': item['image_url'],
                    'category': item['category'],
                    'stock': int(item['stock']) if item['stock'] else 0,
                    'quantity': quantity
                })

            return jsonify({
                'items': result,
                'cart_id': cart_to_use,
                'total': round(total, 2)
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to get cart',
            'message': str(e)
        }), 500


@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add a product to cart"""
    user_id = get_request_user()
    cart_id = request.headers.get('X-Cart-ID')
    data = request.get_json() or {}
    quantity = data.get('quantity', 1)

    try:
        with db_pool.connection() as cursor:
            # Check if product exists
            cursor.execute('SELECT id, stock FROM products WHERE id = %s', (product_id,))
            product = cursor.fetchone()

            if not product:
                return jsonify({'error': 'Product not found'}), 404

            # Get or create cart
            if user_id:
                cart_id = get_or_create_cart(user_id=user_id)
            else:
                cart_id = cart_id or get_or_create_cart()

            # Add item to cart (upsert)
            cursor.execute('''
                INSERT INTO cart_items (cart_id, product_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (cart_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + %s
                RETURNING quantity
            ''', (cart_id, product_id, quantity, quantity))

            new_quantity = cursor.fetchone()['quantity']

            # Get total cart count
            cursor.execute('SELECT SUM(quantity) as count FROM cart_items WHERE cart_id = %s', (cart_id,))
            count = cursor.fetchone()['count'] or 0

            return jsonify({
                'success': True,
                'cart_id': cart_id,
                'product_id': product_id,
                'quantity': new_quantity,
                'cart_count': count
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to add to cart',
            'message': str(e)
        }), 500


@app.route('/api/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Remove a product from cart (or reduce quantity)"""
    user_id = get_request_user()
    cart_id = request.headers.get('X-Cart-ID')
    data = request.get_json() or {}
    quantity = data.get('quantity', 1)  # How many to remove, default 1

    try:
        with db_pool.connection() as cursor:
            # Find cart
            if user_id:
                cursor.execute('SELECT id FROM carts WHERE user_id = %s', (user_id,))
            elif cart_id:
                try:
                    cart_uuid = uuid.UUID(cart_id)
                    cursor.execute('SELECT id FROM carts WHERE id = %s', (str(cart_uuid),))
                except ValueError:
                    return jsonify({'error': 'Invalid cart ID'}), 400
            else:
                return jsonify({'error': 'Cart not found'}), 404

            cart = cursor.fetchone()
            if not cart:
                return jsonify({'error': 'Cart not found'}), 404

            cart_id = str(cart['id'])

            # Reduce quantity or remove item
            cursor.execute('''
                UPDATE cart_items
                SET quantity = quantity - %s
                WHERE cart_id = %s AND product_id = %s AND quantity > %s
                RETURNING quantity
            ''', (quantity, cart_id, product_id, quantity))

            result = cursor.fetchone()

            if not result:
                # If not enough quantity, delete the item
                cursor.execute('DELETE FROM cart_items WHERE cart_id = %s AND product_id = %s', (cart_id, product_id))

            # Clean up items with quantity <= 0
            cursor.execute('DELETE FROM cart_items WHERE cart_id = %s AND quantity <= 0', (cart_id,))

            # Get total cart count
            cursor.execute('SELECT SUM(quantity) as count FROM cart_items WHERE cart_id = %s', (cart_id,))
            count = cursor.fetchone()['count'] or 0

            return jsonify({
                'success': True,
                'cart_count': count
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to remove from cart',
            'message': str(e)
        }), 500


@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    """Clear all items from cart"""
    user_id = get_request_user()
    cart_id = request.headers.get('X-Cart-ID')

    try:
        with db_pool.connection() as cursor:
            # Find cart
            if user_id:
                cursor.execute('SELECT id FROM carts WHERE user_id = %s', (user_id,))
            elif cart_id:
                try:
                    cart_uuid = uuid.UUID(cart_id)
                    cursor.execute('SELECT id FROM carts WHERE id = %s', (str(cart_uuid),))
                except ValueError:
                    return jsonify({'error': 'Invalid cart ID'}), 400
            else:
                return jsonify({'success': True, 'message': 'No cart to clear'})

            cart = cursor.fetchone()
            if cart:
                cursor.execute('DELETE FROM cart_items WHERE cart_id = %s', (str(cart['id']),))

            return jsonify({'success': True})

    except Exception as e:
        return jsonify({
            'error': 'Failed to clear cart',
            'message': str(e)
        }), 500


@app.route('/api/cart/count', methods=['GET'])
def cart_count():
    """Get cart item count"""
    user_id = get_request_user()
    cart_id = request.headers.get('X-Cart-ID')

    try:
        with db_pool.connection() as cursor:
            # Find cart
            if user_id:
                cursor.execute('SELECT id FROM carts WHERE user_id = %s', (user_id,))
            elif cart_id:
                try:
                    cart_uuid = uuid.UUID(cart_id)
                    cursor.execute('SELECT id FROM carts WHERE id = %s', (str(cart_uuid),))
                except ValueError:
                    return jsonify({'count': 0})
            else:
                return jsonify({'count': 0})

            cart = cursor.fetchone()
            if not cart:
                return jsonify({'count': 0})

            # Get total count
            cursor.execute('SELECT SUM(quantity) as count FROM cart_items WHERE cart_id = %s', (str(cart['id']),))
            count = cursor.fetchone()['count'] or 0

            return jsonify({'count': count})

    except Exception as e:
        return jsonify({
            'error': 'Failed to get cart count',
            'message': str(e)
        }), 500


@app.route('/api/cart/merge', methods=['POST'])
def merge_cart():
    """Merge guest cart into user cart after login"""
    user_id = get_request_user()
    data = request.get_json()
    guest_cart_id = data.get('guest_cart_id')

    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    if not guest_cart_id:
        return jsonify({'success': True, 'message': 'No guest cart to merge'})

    try:
        merged_cart_id = merge_guest_cart_to_user_cart(guest_cart_id, user_id)

        return jsonify({
            'success': True,
            'cart_id': merged_cart_id,
            'message': 'Cart merged successfully'
        })

    except Exception as e:
        return jsonify({
            'error': 'Failed to merge cart',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)
