"""
Inventory Service

Handles stock management:
- Get stock levels
- Reserve stock for orders
- Confirm reservations
- Release reservations
- Stock movements log
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

app = Flask(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL environment variable is required')
RESERVATION_TIMEOUT_MINUTES = int(os.environ.get('RESERVATION_TIMEOUT_MINUTES', 30))

# Setup logging
setup_logging('inventory-service')
request_logger.init_app(app)

# Initialize database pool
db_pool = get_connection_pool(DATABASE_URL)


def is_admin_request():
    return request.headers.get('X-User-Is-Admin', '').lower() == 'true'


@app.route('/health')
def health():
    """Health check for liveness probe"""
    return jsonify({'status': 'healthy', 'service': 'inventory-service'})


@app.route('/ready')
def ready():
    """Readiness probe - checks database connection"""
    try:
        with db_pool.connection() as cursor:
            cursor.execute('SELECT 1')
        return jsonify({
            'status': 'ready',
            'service': 'inventory-service',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'service': 'inventory-service',
            'database': 'disconnected',
            'error': str(e)
        }), 503


@app.route('/live')
def live():
    """Liveness probe"""
    return jsonify({'status': 'alive', 'service': 'inventory-service'})


@app.route('/api/inventory/<int:product_id>', methods=['GET'])
def get_stock(product_id):
    """Get stock level for a product"""
    try:
        with db_pool.connection() as cursor:
            # Check if inventory record exists
            cursor.execute('''
                SELECT i.product_id, i.quantity, i.reserved_quantity,
                       (i.quantity - i.reserved_quantity) as available_quantity,
                       i.low_stock_threshold
                FROM inventory i
                WHERE i.product_id = %s
            ''', (product_id,))

            inventory = cursor.fetchone()

            if not inventory:
                # Try to get stock from products table if inventory not initialized
                cursor.execute('SELECT id, stock FROM products WHERE id = %s', (product_id,))
                product = cursor.fetchone()

                if not product:
                    return jsonify({'error': 'Product not found'}), 404

                return jsonify({
                    'product_id': product_id,
                    'quantity': product['stock'],
                    'reserved_quantity': 0,
                    'available_quantity': product['stock'],
                    'low_stock_threshold': 10
                })

            return jsonify({
                'product_id': inventory['product_id'],
                'quantity': int(inventory['quantity']),
                'reserved_quantity': int(inventory['reserved_quantity']),
                'available_quantity': int(inventory['available_quantity']),
                'low_stock_threshold': inventory['low_stock_threshold']
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to get stock',
            'message': str(e)
        }), 500


@app.route('/api/inventory', methods=['GET'])
def list_inventory():
    """List inventory rows for admin inventory management."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    limit = min(200, max(1, int(request.args.get('limit', 100))))
    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT p.id AS product_id, p.name, p.category, p.stock,
                       COALESCE(i.quantity, p.stock, 0) AS quantity,
                       COALESCE(i.reserved_quantity, 0) AS reserved_quantity,
                       COALESCE(i.quantity - i.reserved_quantity, p.stock, 0) AS available_quantity,
                       COALESCE(i.low_stock_threshold, 10) AS low_stock_threshold
                FROM products p
                LEFT JOIN inventory i ON i.product_id = p.id
                ORDER BY p.id
                LIMIT %s
            ''', (limit,))
            items = cursor.fetchall()
            for item in items:
                item['stock'] = int(item['stock']) if item['stock'] is not None else 0
                item['quantity'] = int(item['quantity']) if item['quantity'] is not None else 0
                item['reserved_quantity'] = int(item['reserved_quantity']) if item['reserved_quantity'] is not None else 0
                item['available_quantity'] = int(item['available_quantity']) if item['available_quantity'] is not None else 0
            return jsonify({'items': items, 'count': len(items)})
    except Exception as e:
        return jsonify({'error': 'Failed to list inventory', 'message': str(e)}), 500


@app.route('/api/inventory/reserve', methods=['POST'])
def reserve_stock():
    """Reserve stock for an order"""
    data = request.get_json()
    order_id = data.get('order_id')
    items = data.get('items', [])  # List of {product_id, quantity}

    if not order_id or not items:
        return jsonify({'error': 'order_id and items required'}), 400

    try:
        conn = db_pool.get_connection()
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            reservations = []
            expires_at = datetime.now() + timedelta(minutes=RESERVATION_TIMEOUT_MINUTES)

            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']

                # Check available stock
                cursor.execute('''
                    SELECT quantity, reserved_quantity
                    FROM inventory
                    WHERE product_id = %s
                    FOR UPDATE
                ''', (product_id,))

                inv = cursor.fetchone()

                if not inv:
                    # Initialize from products table
                    cursor.execute('SELECT stock FROM products WHERE id = %s', (product_id,))
                    product = cursor.fetchone()
                    if not product:
                        conn.rollback()
                        return jsonify({'error': f'Product {product_id} not found'}), 404

                    cursor.execute('''
                        INSERT INTO inventory (product_id, quantity, reserved_quantity)
                        VALUES (%s, %s, 0)
                    ''', (product_id, product['stock']))
                    available = product['stock']
                else:
                    available = inv['quantity'] - inv['reserved_quantity']

                if available < quantity:
                    conn.rollback()
                    return jsonify({
                        'error': 'Insufficient stock',
                        'product_id': product_id,
                        'available': available,
                        'requested': quantity
                    }), 400

                # Reserve stock
                cursor.execute('''
                    UPDATE inventory
                    SET reserved_quantity = reserved_quantity + %s
                    WHERE product_id = %s
                ''', (quantity, product_id))

                # Create reservation record
                cursor.execute('''
                    INSERT INTO stock_reservations (order_id, product_id, quantity, expires_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                ''', (order_id, product_id, quantity, expires_at))

                reservation_id = cursor.fetchone()['id']

                # Log movement
                cursor.execute('''
                    INSERT INTO stock_movements (product_id, movement_type, quantity, order_id, notes)
                    VALUES (%s, 'RESERVE', %s, %s, %s)
                ''', (product_id, quantity, order_id, f'Reservation {reservation_id}'))

                reservations.append({
                    'reservation_id': reservation_id,
                    'product_id': product_id,
                    'quantity': quantity
                })

            conn.commit()

            return jsonify({
                'success': True,
                'order_id': order_id,
                'reservations': reservations,
                'expires_at': expires_at.isoformat()
            })

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'error': 'Failed to reserve stock',
            'message': str(e)
        }), 500


@app.route('/api/inventory/confirm/<int:order_id>', methods=['POST'])
def confirm_reservation(order_id):
    """Confirm a stock reservation (deduct stock after payment)"""
    try:
        conn = db_pool.get_connection()
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Get all reservations for this order
            cursor.execute('''
                SELECT id, product_id, quantity
                FROM stock_reservations
                WHERE order_id = %s AND status = 'PENDING'
            ''', (order_id,))

            reservations = cursor.fetchall()

            if not reservations:
                return jsonify({'error': 'No pending reservations found'}), 404

            for res in reservations:
                # Deduct stock
                cursor.execute('''
                    UPDATE inventory
                    SET quantity = quantity - %s,
                        reserved_quantity = reserved_quantity - %s
                    WHERE product_id = %s
                ''', (res['quantity'], res['quantity'], res['product_id']))

                # Update reservation status
                cursor.execute('''
                    UPDATE stock_reservations
                    SET status = 'CONFIRMED'
                    WHERE id = %s
                ''', (res['id'],))

                # Log movement
                cursor.execute('''
                    INSERT INTO stock_movements (product_id, movement_type, quantity, order_id, notes)
                    VALUES (%s, 'CONFIRM', %s, %s, %s)
                ''', (res['product_id'], res['quantity'], order_id, f'Confirmed for order {order_id}'))

            conn.commit()

            return jsonify({
                'success': True,
                'order_id': order_id,
                'confirmed_count': len(reservations)
            })

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'error': 'Failed to confirm reservation',
            'message': str(e)
        }), 500


@app.route('/api/inventory/release/<int:order_id>', methods=['POST'])
def release_reservation(order_id):
    """Release a stock reservation (cancel order)"""
    try:
        conn = db_pool.get_connection()
        conn.autocommit = False
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Get all pending reservations for this order
            cursor.execute('''
                SELECT id, product_id, quantity
                FROM stock_reservations
                WHERE order_id = %s AND status = 'PENDING'
            ''', (order_id,))

            reservations = cursor.fetchall()

            if not reservations:
                return jsonify({'success': True, 'message': 'No pending reservations'})

            for res in reservations:
                # Release reserved stock
                cursor.execute('''
                    UPDATE inventory
                    SET reserved_quantity = reserved_quantity - %s
                    WHERE product_id = %s
                ''', (res['quantity'], res['product_id']))

                # Update reservation status
                cursor.execute('''
                    UPDATE stock_reservations
                    SET status = 'RELEASED'
                    WHERE id = %s
                ''', (res['id'],))

                # Log movement
                cursor.execute('''
                    INSERT INTO stock_movements (product_id, movement_type, quantity, order_id, notes)
                    VALUES (%s, 'RELEASE', %s, %s, %s)
                ''', (res['product_id'], res['quantity'], order_id, f'Released for order {order_id}'))

            conn.commit()

            return jsonify({
                'success': True,
                'order_id': order_id,
                'released_count': len(reservations)
            })

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'error': 'Failed to release reservation',
            'message': str(e)
        }), 500


@app.route('/api/inventory/restock', methods=['POST'])
def restock():
    """Add stock to inventory"""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    notes = data.get('notes', '')

    if not product_id or not quantity:
        return jsonify({'error': 'product_id and quantity required'}), 400

    try:
        with db_pool.connection() as cursor:
            # Check if inventory record exists
            cursor.execute('SELECT product_id FROM inventory WHERE product_id = %s', (product_id,))
            exists = cursor.fetchone()

            if exists:
                cursor.execute('''
                    UPDATE inventory
                    SET quantity = quantity + %s
                    WHERE product_id = %s
                ''', (quantity, product_id))
            else:
                cursor.execute('''
                    INSERT INTO inventory (product_id, quantity, reserved_quantity)
                    VALUES (%s, %s, 0)
                ''', (product_id, quantity))

            # Log movement
            cursor.execute('''
                INSERT INTO stock_movements (product_id, movement_type, quantity, notes)
                VALUES (%s, 'RESTOCK', %s, %s)
            ''', (product_id, quantity, notes or f'Restock of {quantity} units'))

            return jsonify({
                'success': True,
                'product_id': product_id,
                'quantity_added': quantity
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to restock',
            'message': str(e)
        }), 500


@app.route('/api/inventory/low-stock', methods=['GET'])
def get_low_stock():
    """Get products with low stock levels"""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    threshold = int(request.args.get('threshold', 10))

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT i.product_id, i.quantity, i.reserved_quantity,
                       (i.quantity - i.reserved_quantity) as available_quantity,
                       i.low_stock_threshold, p.name, p.category
                FROM inventory i
                JOIN products p ON i.product_id = p.id
                WHERE (i.quantity - i.reserved_quantity) <= %s
                   OR i.quantity <= i.low_stock_threshold
                ORDER BY (i.quantity - i.reserved_quantity) ASC
            ''', (threshold,))

            items = cursor.fetchall()

            for item in items:
                item['quantity'] = int(item['quantity'])
                item['reserved_quantity'] = int(item['reserved_quantity'])
                item['available_quantity'] = int(item['available_quantity'])

            return jsonify({
                'low_stock_items': items,
                'count': len(items)
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to get low stock items',
            'message': str(e)
        }), 500


@app.route('/api/inventory/movements/<int:product_id>', methods=['GET'])
def get_movements(product_id):
    """Get stock movement history for a product"""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    limit = min(100, max(1, int(request.args.get('limit', 50))))

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                SELECT id, movement_type, quantity, order_id, notes, created_at
                FROM stock_movements
                WHERE product_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            ''', (product_id, limit))

            movements = cursor.fetchall()

            return jsonify({
                'product_id': product_id,
                'movements': movements,
                'count': len(movements)
            })

    except Exception as e:
        return jsonify({
            'error': 'Failed to get movements',
            'message': str(e)
        }), 500


@app.route('/api/inventory/sync', methods=['POST'])
def sync_inventory():
    """Initialize missing inventory rows from products."""
    if not is_admin_request():
        return jsonify({'error': 'Admin access required'}), 403

    try:
        with db_pool.connection() as cursor:
            cursor.execute('''
                INSERT INTO inventory (product_id, quantity, reserved_quantity)
                SELECT p.id, p.stock, 0
                FROM products p
                WHERE NOT EXISTS (
                    SELECT 1 FROM inventory i WHERE i.product_id = p.id
                )
            ''')
            inserted = cursor.rowcount or 0
            return jsonify({'success': True, 'synced_count': inserted})
    except Exception as e:
        return jsonify({'error': 'Failed to sync inventory', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=False)
