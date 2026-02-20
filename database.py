import sqlite3
import hashlib
from datetime import datetime, timedelta
import random
import os

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_expiry_date(donation_date_str):
    """Calculate expiry date (42 days after donation)."""
    try:
        donation_date = datetime.strptime(donation_date_str, '%Y-%m-%d')
        expiry_date = donation_date + timedelta(days=42)
        return expiry_date.strftime('%Y-%m-%d')
    except Exception as e:
        # If there's an error, return a date 42 days from now
        return (datetime.now() + timedelta(days=42)).strftime('%Y-%m-%d')

def init_database():
    """Initialize the database with all tables and sample data."""
    
    # Don't remove existing database on Render
    conn = sqlite3.connect('bloodbank.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("BLOOD BANK DATABASE SETUP")
    print("=" * 60)
    
    print("\n1. Creating tables...")
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'staff',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create donors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS donors (
        donor_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        date_of_birth DATE NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        city TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        medical_details TEXT,
        eligible BOOLEAN DEFAULT 1,
        last_donation_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create blood inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blood_group TEXT NOT NULL UNIQUE,
        units_available INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Normal'
    )
    ''')
    
    # Create donation history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS donation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donation_id TEXT NOT NULL UNIQUE,
        donor_id TEXT NOT NULL,
        donor_name TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        units_donated INTEGER NOT NULL,
        donation_date DATE NOT NULL,
        expiry_date DATE NOT NULL,
        received_by TEXT,
        test_result TEXT DEFAULT 'Passed',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    print("✓ Tables created successfully!")
    
    # Insert default users
    print("\n2. Creating default users...")
    
    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users WHERE email IN ('admin@bloodbank.com', 'staff@bloodbank.com')")
    if cursor.fetchone()[0] == 0:
        users = [
            ('admin@bloodbank.com', hash_password('admin123'), 'System Administrator', 'admin'),
            ('staff@bloodbank.com', hash_password('staff123'), 'John Doe', 'staff'),
        ]
        
        cursor.executemany('''
            INSERT INTO users (email, password, name, role)
            VALUES (?, ?, ?, ?)
        ''', users)
        print("✓ Default users created!")
        print("   Admin: admin@bloodbank.com / admin123")
        print("   Staff: staff@bloodbank.com / staff123")
    else:
        print("✓ Default users already exist!")
    
    # Insert default blood groups into inventory
    print("\n3. Initializing blood inventory...")
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
    
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        for bg in blood_groups:
            units = random.randint(5, 30)
            status = 'Low Stock' if units < 10 else 'Normal' if units < 20 else 'High Stock'
            
            cursor.execute('''
                INSERT INTO inventory (blood_group, units_available, status)
                VALUES (?, ?, ?)
            ''', (bg, units, status))
        print("✓ Blood inventory initialized!")
    else:
        print("✓ Blood inventory already exists!")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ DATABASE INITIALIZATION COMPLETED!")
    print("=" * 60)
    
    return True

def check_database():
    """Check if database exists and is accessible."""
    if not os.path.exists('bloodbank.db'):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect('bloodbank.db')
        cursor = conn.cursor()
        
        # Check if tables exist
        tables = ['users', 'donors', 'inventory', 'donation_history']
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                print(f"❌ Table '{table}' not found in database!")
                conn.close()
                return False
        
        conn.close()
        print("✅ Database check passed!")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("BLOOD BANK DATABASE SETUP")
    print("=" * 60)
    
    # Create database
    init_database()
    
    # Verify database
    check_database()