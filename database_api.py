from flask import Flask, request, jsonify
import mysql.connector
import os
import jwt
from functools import wraps
from datetime import datetime
import hashlib
from mysql.connector import Error
import time

app = Flask(__name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# MySQL configuration - DOCKER VERSION
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'mysql'),  # ← PAKAI 'mysql' (service name)
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'password'),
    'database': os.getenv('MYSQL_DATABASE', 'guardiantix'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'auth_plugin': 'mysql_native_password',  # ← TAMBAH INI
    'connect_timeout': 30  # ← TAMBAH INI
}

def get_db_connection(retries=5, delay=5):
    """Create MySQL database connection dengan retry untuk Docker"""
    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            print(f"✅ Connected to MySQL database: {MYSQL_CONFIG['database']}")
            return conn
        except Error as e:
            print(f"❌ Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                print(f"🔄 Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("❌ All connection attempts failed")
                return None

def init_database():
    """Initialize database tables if they don't exist"""
    print("🔄 Initializing database dengan retry...")
    
    for attempt in range(3):
        conn = get_db_connection()
        if conn:
            break
        print(f"🔄 Retry {attempt + 1}/3 in 10 seconds...")
        time.sleep(10)
    else:
        print("❌ Failed to connect to MySQL after 3 attempts")
        return
    
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                phone VARCHAR(20),
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create concerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                artist VARCHAR(255) NOT NULL,
                date VARCHAR(100) NOT NULL,
                venue VARCHAR(255) NOT NULL,
                price INT NOT NULL,
                available_tickets INT NOT NULL
            )
        ''')
        
        # Insert admin user if not exists
        cursor.execute('SELECT id FROM users WHERE email = %s', ('admin@guardiantix.com',))
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            password_hash = hash_password('admin123')
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)',
                ('System Admin', 'admin@guardiantix.com', password_hash, 'admin')
            )
            print("✅ Admin user created in database")
        
        # Insert sample concerts if not exists
        cursor.execute('SELECT COUNT(*) FROM concerts')
        concert_count = cursor.fetchone()[0]
        
        if concert_count == 0:
            concerts = [
                ('Coldplay Tour', 'Coldplay', '2024-12-15', 'GBK Stadium', 750000, 1000),
                ('Blackpink Show', 'Blackpink', '2024-11-20', 'Istora Senayan', 1200000, 500),
                ('Jazz Festival', 'Various Artists', '2024-10-25', 'Plenary Hall', 500000, 300)
            ]
            
            cursor.executemany(
                'INSERT INTO concerts (name, artist, date, venue, price, available_tickets) VALUES (%s, %s, %s, %s, %s, %s)',
                concerts
            )
            print("✅ Sample concerts added to database")
        
        conn.commit()
        print("✅ MySQL database initialized successfully")
        
    except Error as e:
        print(f"❌ Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()

# Initialize database when starting - TAMBAH DELAY
print("⏳ Waiting for MySQL to be ready...")
time.sleep(10)  # Tunggu MySQL container siap
init_database()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize database when starting
init_database()

# Authentication middleware
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            token = token.replace('Bearer ', '')  # Remove Bearer prefix
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data['user_id']
        except Exception as e:
            return jsonify({'error': 'Token is invalid', 'details': str(e)}), 401
        return f(*args, **kwargs)
    return decorated

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'status': 'unhealthy', 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'MySQL connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Check session endpoint
@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Check if user session is valid"""
    token = request.headers.get('Authorization')
    
    if not token or not token.startswith('Bearer '):
        return jsonify({'valid': False, 'error': 'No token provided'}), 401
    
    try:
        token = token.split()[1]  # Remove 'Bearer ' prefix
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = decoded['user_id']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'valid': False, 'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, username, email, role, phone, join_date FROM users WHERE id = %s',
            (user_id,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({'valid': True, 'user': user})
        else:
            return jsonify({'valid': False, 'error': 'User not found'}), 404
            
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500

# Login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    identifier = data.get('identifier', '').strip()
    password = data.get('password', '').strip()
    
    if not identifier or not password:
        return jsonify({'error': 'Email/username and password required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Try by email first
        cursor.execute('SELECT * FROM users WHERE email = %s', (identifier,))
        user = cursor.fetchone()
        
        # If not found by email, try by username
        if not user:
            cursor.execute('SELECT * FROM users WHERE username = %s', (identifier,))
            user = cursor.fetchone()
        
        # DEBUG: Print untuk troubleshooting
        print(f"🔍 Login attempt - User: {identifier}")
        print(f"🔍 Found user: {user['email'] if user else 'None'}")
        
        # VERIFY PASSWORD - PLAINTEXT (NO HASHING)
        if user and user['password_hash'] == password:  # ← LANGSUNG COMPARE PLAINTEXT
            # Remove password from response
            user.pop('password_hash', None)
            
            token = jwt.encode(
                {'user_id': user['id'], 'username': user['username']}, 
                SECRET_KEY, 
                algorithm="HS256"
            )
            
            print(f"✅ Login successful for: {user['email']}")
            return jsonify({
                'token': token, 
                'user': user,
                'message': 'Login successful'
            })
        else:
            print(f"❌ Login failed - Password mismatch")
            print(f"🔍 Stored: {user['password_hash'] if user else 'None'}")
            print(f"🔍 Input: {password}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Error as e:
        print(f"❌ Database error: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()
# User endpoints
@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT id, username, email, role, phone, join_date FROM users')
        users = cursor.fetchall()
        return jsonify(users)
    except Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            'SELECT id, username, email, role, phone, join_date FROM users WHERE id = %s',
            (user_id,)
        )
        user = cursor.fetchone()
        if user:
            return jsonify(user)
        return jsonify({'error': 'User not found'}), 404
    except Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor()
    try:
        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE email = %s', (data['email'],))
        existing = cursor.fetchone()
        if existing:
            return jsonify({'error': 'Email already registered'}), 400

        # PLAINTEXT PASSWORD - NO HASHING
        password_hash = data['password']  # ← LANGSUNG SIMPAN PLAINTEXT
        
        cursor.execute(
            'INSERT INTO users (username, email, password_hash, role, phone) VALUES (%s, %s, %s, %s, %s)',
            (data['username'], data['email'], password_hash, data.get('role', 'user'), 
             data.get('phone'))
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        return jsonify({
            'id': user_id, 
            'message': 'User created successfully',
            'username': data['username'],
            'email': data['email'],
            'role': data.get('role', 'user')
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

# Concert endpoints
@app.route('/api/concerts', methods=['GET'])
def get_concerts():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT * FROM concerts')
        concerts = cursor.fetchall()
        return jsonify(concerts)
    except Error as e:
        # Return empty array if concerts table doesn't exist yet
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

# Add sample concerts if needed
@app.route('/api/init-concerts', methods=['POST'])
def init_concerts():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor()
    try:
        # Insert sample concerts
        concerts = [
            ('Coldplay Tour', 'Coldplay', '2024-12-15', 'GBK Stadium', 750000, 1000),
            ('Blackpink Show', 'Blackpink', '2024-11-20', 'Istora Senayan', 1200000, 500),
            ('Jazz Festival', 'Various Artists', '2024-10-25', 'Plenary Hall', 500000, 300)
        ]
        
        cursor.executemany(
            'INSERT INTO concerts (name, artist, date, venue, price, available_tickets) VALUES (%s, %s, %s, %s, %s, %s)',
            concerts
        )
        conn.commit()
        return jsonify({'message': 'Sample concerts added successfully'})
    except Error as e:
        conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

# Admin endpoints
@app.route('/api/admin/users', methods=['GET'])
@token_required
def get_all_users():
    """Get all users for admin panel"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            'SELECT id, username, email, role, phone, join_date FROM users ORDER BY join_date DESC'
        )
        users = cursor.fetchall()
        return jsonify(users)
    except Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/stats', methods=['GET'])
@token_required
def get_admin_stats():
    """Get admin dashboard statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor()
    try:
        # Total users count
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Total concerts count
        cursor.execute('SELECT COUNT(*) FROM concerts')
        total_concerts = cursor.fetchone()[0]
        
        # Recent users (last 7 days)
        cursor.execute('SELECT COUNT(*) FROM users WHERE join_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)')
        recent_users = cursor.fetchone()[0]
        
        return jsonify({
            'total_users': total_users,
            'total_concerts': total_concerts,
            'recent_users': recent_users,
            'total_tickets_sold': 1200,  # Placeholder
            'total_revenue': 850000000,  # Placeholder
            'pending_transactions': 20   # Placeholder
        })
    except Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user_role(user_id):
    """Update user role (admin/user)"""
    data = request.json
    new_role = data.get('role')
    
    if new_role not in ['admin', 'user']:
        return jsonify({'error': 'Invalid role'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE users SET role = %s WHERE id = %s',
            (new_role, user_id)
        )
        conn.commit()
        return jsonify({'message': f'User role updated to {new_role}'})
    except Error as e:
        conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    """Delete user (admin only)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Error as e:
        conn.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("🚀 Database API starting...")
    print("📊 Database: MySQL")
    print("🔐 Secret Key:", SECRET_KEY)
    print("🏠 MySQL Host:", MYSQL_CONFIG['host'])
    print("📁 MySQL Database:", MYSQL_CONFIG['database'])
    app.run(debug=True, host='0.0.0.0', port=8000)