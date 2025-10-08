from flask import Flask, request, jsonify
import sqlite3
import os
import jwt
from functools import wraps
from datetime import datetime
import hashlib

app = Flask(__name__)
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('/data/guardiantix.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            phone TEXT,
            join_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create concerts table (jika diperlukan)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS concerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            artist TEXT NOT NULL,
            date TEXT NOT NULL,
            venue TEXT NOT NULL,
            price INTEGER NOT NULL,
            available_tickets INTEGER NOT NULL
        )
    ''')
    
    # Insert admin user if not exists
    admin_exists = conn.execute(
        'SELECT id FROM users WHERE email = ?', ('admin@guardiantix.com',)
    ).fetchone()
    
    if not admin_exists:
        password_hash = hash_password('admin123')
        conn.execute(
            'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
            ('System Admin', 'admin@guardiantix.com', password_hash, 'admin')
        )
        print("✅ Admin user created in database")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

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
        conn.execute('SELECT 1')
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Check session endpoint - FIXED VERSION
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
        user = conn.execute(
            'SELECT id, username, email, role, phone, join_date FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        conn.close()
        
        if user:
            return jsonify({'valid': True, 'user': dict(user)})
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
    
    # Try by email first
    user = conn.execute(
        'SELECT * FROM users WHERE email = ?', (identifier,)
    ).fetchone()
    
    # If not found by email, try by username
    if not user:
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (identifier,)
        ).fetchone()
    
    conn.close()
    
    if user and user['password_hash'] == hash_password(password):
        user_dict = dict(user)
        # Remove password from response
        user_dict.pop('password_hash', None)
        
        token = jwt.encode(
            {'user_id': user['id'], 'username': user['username']}, 
            SECRET_KEY, 
            algorithm="HS256"
        )
        
        return jsonify({
            'token': token, 
            'user': user_dict,
            'message': 'Login successful'
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# User endpoints
@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, email, role, phone, join_date FROM users').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route('/api/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, email, role, phone, join_date FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    conn.close()
    if user:
        return jsonify(dict(user))
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    conn = get_db_connection()
    try:
        # Check if email already exists
        existing = conn.execute(
            'SELECT id FROM users WHERE email = ?', (data['email'],)
        ).fetchone()
        if existing:
            conn.close()
            return jsonify({'error': 'Email already registered'}), 400

        password_hash = hash_password(data['password'])
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, email, password_hash, role, phone) VALUES (?, ?, ?, ?, ?)',
            (data['username'], data['email'], password_hash, data.get('role', 'user'), 
             data.get('phone'))
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'id': user_id, 
            'message': 'User created successfully',
            'username': data['username'],
            'email': data['email'],
            'role': data.get('role', 'user')
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Concert endpoints
@app.route('/api/concerts', methods=['GET'])
def get_concerts():
    conn = get_db_connection()
    try:
        concerts = conn.execute('SELECT * FROM concerts').fetchall()
        conn.close()
        return jsonify([dict(concert) for concert in concerts])
    except:
        # Return empty array if concerts table doesn't exist yet
        conn.close()
        return jsonify([])

# Add sample concerts if needed
@app.route('/api/init-concerts', methods=['POST'])
def init_concerts():
    conn = get_db_connection()
    try:
        # Insert sample concerts
        concerts = [
            ('Coldplay Tour', 'Coldplay', '2024-12-15', 'GBK Stadium', 750000, 1000),
            ('Blackpink Show', 'Blackpink', '2024-11-20', 'Istora Senayan', 1200000, 500),
            ('Jazz Festival', 'Various Artists', '2024-10-25', 'Plenary Hall', 500000, 300)
        ]
        
        conn.executemany(
            'INSERT INTO concerts (name, artist, date, venue, price, available_tickets) VALUES (?, ?, ?, ?, ?, ?)',
            concerts
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Sample concerts added successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Admin endpoints
@app.route('/api/admin/users', methods=['GET'])
@token_required
def get_all_users():
    """Get all users for admin panel"""
    conn = get_db_connection()
    users = conn.execute(
        'SELECT id, username, email, role, phone, join_date FROM users ORDER BY join_date DESC'
    ).fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route('/api/admin/stats', methods=['GET'])
@token_required
def get_admin_stats():
    """Get admin dashboard statistics"""
    conn = get_db_connection()
    
    # Total users count
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    
    # Total concerts count
    total_concerts = conn.execute('SELECT COUNT(*) FROM concerts').fetchone()[0]
    
    # Recent users (last 7 days)
    recent_users = conn.execute(
        'SELECT COUNT(*) FROM users WHERE join_date >= date("now", "-7 days")'
    ).fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_users': total_users,
        'total_concerts': total_concerts,
        'recent_users': recent_users,
        'total_tickets_sold': 1200,  # Placeholder
        'total_revenue': 850000000,  # Placeholder
        'pending_transactions': 20   # Placeholder
    })

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user_role(user_id):
    """Update user role (admin/user)"""
    data = request.json
    new_role = data.get('role')
    
    if new_role not in ['admin', 'user']:
        return jsonify({'error': 'Invalid role'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE users SET role = ? WHERE id = ?',
            (new_role, user_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': f'User role updated to {new_role}'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    """Delete user (admin only)"""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Database API starting...")
    print("📊 Database: SQLite")
    print("🔐 Secret Key:", SECRET_KEY)
    app.run(debug=True, host='0.0.0.0', port=8000)