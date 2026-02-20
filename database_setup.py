import sqlite3
import hashlib
from datetime import datetime, timedelta
import json
import os

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Initialize the database with all tables and sample data."""
    
    conn = sqlite3.connect('bloodbank.db')
    cursor = conn.cursor()
    
    print("Creating tables...")
    
    # Define SQL schema directly in code
    sql_script = '''
    -- Users table for authentication
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'staff' CHECK(role IN ('admin', 'staff', 'viewer')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    );

    -- Donors table
    CREATE TABLE IF NOT EXISTS donors (
        donor_id VARCHAR(10) PRIMARY KEY,
        name TEXT NOT NULL,
        date_of_birth DATE NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL CHECK(gender IN ('Male', 'Female', 'Other')),
        blood_group TEXT NOT NULL CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-')),
        city TEXT NOT NULL,
        phone VARCHAR(15) NOT NULL UNIQUE,
        email TEXT UNIQUE,
        medical_details TEXT,
        weight DECIMAL(5,2),
        height DECIMAL(5,2),
        last_donation_date DATE,
        eligible BOOLEAN DEFAULT 1,
        status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Temporarily Deferred')),
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    );

    -- Blood inventory table
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blood_group TEXT NOT NULL CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-')),
        units_available INTEGER DEFAULT 0 CHECK(units_available >= 0),
        units_used INTEGER DEFAULT 0,
        units_expired INTEGER DEFAULT 0,
        minimum_threshold INTEGER DEFAULT 10,
        maximum_capacity INTEGER DEFAULT 50,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Normal' CHECK(status IN ('Critical', 'Low Stock', 'Normal', 'Adequate', 'Full')),
        location TEXT DEFAULT 'Main Storage',
        expiry_date DATE,
        notes TEXT
    );

    -- Donation history table
    CREATE TABLE IF NOT EXISTS donation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donation_id VARCHAR(15) UNIQUE NOT NULL,
        donor_id VARCHAR(10) NOT NULL,
        donor_name TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        units_donated INTEGER NOT NULL CHECK(units_donated BETWEEN 1 AND 2),
        hemoglobin_level DECIMAL(4,2),
        blood_pressure VARCHAR(10),
        donation_type TEXT DEFAULT 'Whole Blood' CHECK(donation_type IN ('Whole Blood', 'Plasma', 'Platelets', 'Double Red Cells')),
        donation_date DATE NOT NULL,
        expiry_date DATE NOT NULL,
        received_by INTEGER NOT NULL,
        tested_by INTEGER,
        test_result TEXT DEFAULT 'Pending' CHECK(test_result IN ('Pending', 'Passed', 'Failed')),
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE,
        FOREIGN KEY (received_by) REFERENCES users(id),
        FOREIGN KEY (tested_by) REFERENCES users(id)
    );

    -- Blood requests table
    CREATE TABLE IF NOT EXISTS blood_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id VARCHAR(15) UNIQUE NOT NULL,
        patient_name TEXT NOT NULL,
        hospital_name TEXT NOT NULL,
        hospital_address TEXT,
        doctor_name TEXT,
        blood_group TEXT NOT NULL,
        units_required INTEGER NOT NULL CHECK(units_required > 0),
        urgency TEXT DEFAULT 'Normal' CHECK(urgency IN ('Emergency', 'Urgent', 'Normal')),
        request_date DATE NOT NULL,
        required_date DATE NOT NULL,
        request_status TEXT DEFAULT 'Pending' CHECK(request_status IN ('Pending', 'Approved', 'Rejected', 'Fulfilled', 'Cancelled')),
        fulfilled_units INTEGER DEFAULT 0,
        fulfilled_date DATE,
        requested_by INTEGER,
        approved_by INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (requested_by) REFERENCES users(id),
        FOREIGN KEY (approved_by) REFERENCES users(id)
    );

    -- Blood transfusion table
    CREATE TABLE IF NOT EXISTS blood_transfusion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transfusion_id VARCHAR(15) UNIQUE NOT NULL,
        request_id VARCHAR(15) NOT NULL,
        donation_id VARCHAR(15) NOT NULL,
        units_used INTEGER NOT NULL,
        transfused_date DATE NOT NULL,
        transfused_by INTEGER NOT NULL,
        patient_outcome TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES blood_requests(request_id),
        FOREIGN KEY (donation_id) REFERENCES donation_history(donation_id),
        FOREIGN KEY (transfused_by) REFERENCES users(id)
    );

    -- Donor eligibility log
    CREATE TABLE IF NOT EXISTS donor_eligibility_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donor_id VARCHAR(10) NOT NULL,
        eligibility_status BOOLEAN NOT NULL,
        reason TEXT,
        checked_by INTEGER,
        checked_date DATE DEFAULT CURRENT_DATE,
        next_eligible_date DATE,
        FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE,
        FOREIGN KEY (checked_by) REFERENCES users(id)
    );

    -- Audit log table
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        record_id TEXT NOT NULL,
        action TEXT NOT NULL CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')),
        old_values TEXT,
        new_values TEXT,
        changed_by INTEGER,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT,
        FOREIGN KEY (changed_by) REFERENCES users(id)
    );

    -- Indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_donors_blood_group ON donors(blood_group);
    CREATE INDEX IF NOT EXISTS idx_donors_city ON donors(city);
    CREATE INDEX IF NOT EXISTS idx_donors_eligible ON donors(eligible);
    CREATE INDEX IF NOT EXISTS idx_inventory_blood_group ON inventory(blood_group);
    CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status);
    CREATE INDEX IF NOT EXISTS idx_donation_history_donor_id ON donation_history(donor_id);
    CREATE INDEX IF NOT EXISTS idx_donation_history_donation_date ON donation_history(donation_date);
    CREATE INDEX IF NOT EXISTS idx_blood_requests_status ON blood_requests(request_status);
    CREATE INDEX IF NOT EXISTS idx_blood_requests_blood_group ON blood_requests(blood_group);

    -- View for donor statistics
    CREATE VIEW IF NOT EXISTS donor_statistics AS
    SELECT 
        d.blood_group,
        COUNT(*) as total_donors,
        SUM(CASE WHEN d.eligible = 1 THEN 1 ELSE 0 END) as eligible_donors,
        SUM(CASE WHEN d.gender = 'Male' THEN 1 ELSE 0 END) as male_donors,
        SUM(CASE WHEN d.gender = 'Female' THEN 1 ELSE 0 END) as female_donors,
        AVG(d.age) as avg_age,
        MIN(d.age) as min_age,
        MAX(d.age) as max_age
    FROM donors d
    GROUP BY d.blood_group;

    -- View for monthly donation summary
    CREATE VIEW IF NOT EXISTS monthly_donation_summary AS
    SELECT 
        strftime('%Y-%m', donation_date) as month,
        blood_group,
        COUNT(*) as total_donations,
        SUM(units_donated) as total_units,
        AVG(units_donated) as avg_units_per_donation
    FROM donation_history
    WHERE test_result = 'Passed'
    GROUP BY strftime('%Y-%m', donation_date), blood_group;

    -- View for critical inventory
    CREATE VIEW IF NOT EXISTS critical_inventory AS
    SELECT 
        blood_group,
        units_available,
        minimum_threshold,
        status,
        last_updated
    FROM inventory
    WHERE status IN ('Critical', 'Low Stock')
    ORDER BY units_available ASC;
    '''
    
    # Split the script into individual statements
    statements = sql_script.split(';')
    
    for statement in statements:
        statement = statement.strip()
        if statement:
            try:
                cursor.execute(statement)
            except sqlite3.Error as e:
                print(f"Error executing statement: {e}")
                print(f"Statement: {statement[:100]}...")
    
    print("Inserting default data...")
    
    # Insert default users
    users = [
        ('admin@bloodbank.com', hash_password('admin123'), 'System Administrator', 'admin'),
        ('staff1@bloodbank.com', hash_password('staff123'), 'John Smith', 'staff'),
        ('staff2@bloodbank.com', hash_password('staff123'), 'Emma Wilson', 'staff'),
        ('doctor1@hospital.com', hash_password('doctor123'), 'Dr. Robert Chen', 'viewer'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO users (email, password, name, role)
        VALUES (?, ?, ?, ?)
    ''', users)
    
    # Insert default blood groups into inventory
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
    for bg in blood_groups:
        # Set different starting values for demo
        import random
        units = random.randint(5, 25)
        status = 'Critical' if units < 5 else 'Low Stock' if units < 10 else 'Normal' if units < 20 else 'Adequate'
        
        cursor.execute('''
            INSERT OR IGNORE INTO inventory 
            (blood_group, units_available, minimum_threshold, maximum_capacity, status, expiry_date)
            VALUES (?, ?, 10, 50, ?, ?)
        ''', (bg, units, status, (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')))
    
    # Insert sample donors
    sample_donors = [
        ('DON10001', 'Michael Johnson', '1990-05-15', 33, 'Male', 'O+', 'Chennai', '9976151423', 'michael@email.com', 'No medical issues', 75.5, 180.0, '2023-10-15', 1, 'Active'),
        ('DON10002', 'Sarah Williams', '1985-08-22', 38, 'Female', 'A-', 'Thanjavur', '9555245870', 'sarah@email.com', 'Allergic to penicillin', 62.0, 165.0, '2023-09-20', 1, 'Active'),
        ('DON10003', 'David Brown', '1995-02-10', 28, 'Male', 'B+', 'Kanyakumari', '7801552103', 'david@email.com', 'Asthma controlled', 80.0, 175.0, '2023-11-05', 1, 'Active'),
        ('DON10004', 'Lisa Taylor', '1988-11-30', 35, 'Female', 'AB-', 'Coimbatore', '8246745104', 'lisa@email.com', 'No issues', 58.0, 160.0, '2023-08-10', 0, 'Temporarily Deferred'),
        ('DON10005', 'James Wilson', '1992-07-18', 31, 'Male', 'O-', 'Kanchipuram', '8075010577', 'james@email.com', 'Universal donor', 85.0, 182.0, '2023-12-01', 1, 'Active'),
        ('DON10006', 'Maria Garcia', '1998-04-25', 25, 'Female', 'A+', 'Trichy', '9234062415', 'maria@email.com', 'No medical issues', 61.0, 162.0, None, 1, 'Active'),
        ('DON10007', 'Robert Miller', '1975-12-05', 48, 'Male', 'B-', 'Villupuram', '7820552207', 'robert@email.com', 'High blood pressure controlled', 90.0, 178.0, '2023-07-22', 1, 'Active'),
        ('DON10008', 'Jennifer Davis', '1982-09-14', 41, 'Female', 'AB+', 'Pudukkottai', '8662559808', 'jennifer@email.com', 'No issues', 59.0, 158.0, '2023-11-15', 1, 'Active'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO donors 
        (donor_id, name, date_of_birth, age, gender, blood_group, city, phone, email, 
         medical_details, weight, height, last_donation_date, eligible, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_donors)
    
    # Insert sample donation history
    import random
    
    donations = []
    for i in range(20):
        donor_idx = random.randint(0, len(sample_donors)-1)
        donor = sample_donors[donor_idx]
        donation_date = datetime.now() - timedelta(days=random.randint(1, 180))
        expiry_date = donation_date + timedelta(days=42)  # Blood expires in 42 days
        
        donations.append((
            f'DONATION{1000 + i}',
            donor[0],  # donor_id
            donor[1],  # donor_name
            donor[5],  # blood_group
            random.choice([1, 2]),  # units_donated
            round(random.uniform(12.5, 16.5), 1),  # hemoglobin_level
            f'{random.randint(110, 130)}/{random.randint(70, 85)}',  # blood_pressure
            'Whole Blood',
            donation_date.strftime('%Y-%m-%d'),
            expiry_date.strftime('%Y-%m-%d'),
            random.randint(1, 3),  # received_by (user_id)
            random.choice([None, 1, 2]),  # tested_by
            random.choice(['Passed', 'Passed', 'Passed', 'Failed']),  # test_result
            'Routine donation' if random.random() > 0.2 else 'Emergency drive donation'
        ))
    
    cursor.executemany('''
        INSERT OR IGNORE INTO donation_history 
        (donation_id, donor_id, donor_name, blood_group, units_donated, 
         hemoglobin_level, blood_pressure, donation_type, donation_date, expiry_date,
         received_by, tested_by, test_result, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', donations)
    
    # Insert sample blood requests
    hospitals = [
        ('City General Hospital', '123 Medical Center Dr, New York'),
        ('Memorial Hospital', '456 Health Ave, Los Angeles'),
        ('Unity Medical Center', '789 Care Street, Chicago'),
        ('Regional Hospital', '321 Wellness Blvd, Houston')
    ]
    
    requests = []
    for i in range(10):
        hospital = random.choice(hospitals)
        request_date = datetime.now() - timedelta(days=random.randint(1, 30))
        required_date = request_date + timedelta(days=random.randint(1, 7))
        
        requests.append((
            f'REQ{2000 + i}',
            f'Patient {i+1}',
            hospital[0],
            hospital[1],
            f'Dr. {random.choice(["Smith", "Johnson", "Williams", "Brown"])}',
            random.choice(blood_groups),
            random.randint(1, 4),
            random.choice(['Emergency', 'Urgent', 'Normal']),
            request_date.strftime('%Y-%m-%d'),
            required_date.strftime('%Y-%m-%d'),
            random.choice(['Pending', 'Approved', 'Fulfilled']),
            random.randint(0, 4),
            None if random.random() > 0.5 else required_date.strftime('%Y-%m-%d'),
            random.randint(1, 3),
            random.randint(1, 2) if random.random() > 0.3 else None,
            f'Request for surgery' if random.random() > 0.5 else 'Emergency transfusion needed'
        ))
    
    cursor.executemany('''
        INSERT OR IGNORE INTO blood_requests 
        (request_id, patient_name, hospital_name, hospital_address, doctor_name,
         blood_group, units_required, urgency, request_date, required_date,
         request_status, fulfilled_units, fulfilled_date, requested_by, approved_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', requests)
    
    conn.commit()
    
    # Verify data insertion
    print("\nDatabase Summary:")
    
    tables = ['users', 'donors', 'inventory', 'donation_history', 'blood_requests']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"{table}: {count} records")
    
    print("\nBlood Inventory Status:")
    cursor.execute('''
        SELECT blood_group, units_available, status 
        FROM inventory 
        ORDER BY blood_group
    ''')
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} units ({row[2]})")
    
    conn.close()
    print("\nDatabase initialization completed successfully!")
    print("\nDefault Login Credentials:")
    print("Admin: admin@bloodbank.com / admin123")
    print("Staff: staff1@bloodbank.com / staff123")

class DatabaseManager:
    """Database management class for blood bank system."""
    
    def __init__(self, db_path='bloodbank.db'):
        self.db_path = db_path
    
    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query, params=()):
        """Execute a query and return results."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                conn.close()
                return results
            else:
                conn.commit()
                last_id = cursor.lastrowid
                conn.close()
                return last_id
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.close()
            return None
    
    def add_donor(self, donor_data):
        """Add a new donor to the database."""
        query = '''
        INSERT INTO donors 
        (donor_id, name, date_of_birth, age, gender, blood_group, city, 
         phone, email, medical_details, weight, height, eligible, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        return self.execute_query(query, donor_data)
    
    def search_donors(self, blood_group=None, city=None, eligible=True):
        """Search donors by criteria."""
        query = 'SELECT * FROM donors WHERE 1=1'
        params = []
        
        if blood_group:
            query += ' AND blood_group = ?'
            params.append(blood_group)
        
        if city:
            query += ' AND city LIKE ?'
            params.append(f'%{city}%')
        
        if eligible is not None:
            query += ' AND eligible = ?'
            params.append(1 if eligible else 0)
        
        query += ' ORDER BY name'
        return self.execute_query(query, params)
    
    def get_inventory_status(self):
        """Get current inventory status."""
        query = '''
        SELECT blood_group, units_available, units_used, minimum_threshold, 
               maximum_capacity, status, last_updated
        FROM inventory
        ORDER BY 
            CASE blood_group
                WHEN 'A+' THEN 1
                WHEN 'A-' THEN 2
                WHEN 'B+' THEN 3
                WHEN 'B-' THEN 4
                WHEN 'O+' THEN 5
                WHEN 'O-' THEN 6
                WHEN 'AB+' THEN 7
                WHEN 'AB-' THEN 8
            END
        '''
        return self.execute_query(query)
    
    def get_donation_history(self, donor_id=None, start_date=None, end_date=None):
        """Get donation history with filters."""
        query = '''
        SELECT dh.*, u.name as received_by_name
        FROM donation_history dh
        LEFT JOIN users u ON dh.received_by = u.id
        WHERE 1=1
        '''
        params = []
        
        if donor_id:
            query += ' AND dh.donor_id = ?'
            params.append(donor_id)
        
        if start_date:
            query += ' AND dh.donation_date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND dh.donation_date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY dh.donation_date DESC'
        return self.execute_query(query, params)
    
    def update_inventory(self, blood_group, units_change, action='add'):
        """Update inventory units."""
        if action == 'add':
            query = '''
            UPDATE inventory 
            SET units_available = units_available + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE blood_group = ?
            '''
            params = (units_change, blood_group)
        else:  # remove
            query = '''
            UPDATE inventory 
            SET units_available = units_available - ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE blood_group = ? AND units_available >= ?
            '''
            params = (units_change, blood_group, units_change)
        
        result = self.execute_query(query, params)
        
        if result is not None:
            # Update status after change
            self._update_inventory_status(blood_group)
        return result
    
    def _update_inventory_status(self, blood_group):
        """Update inventory status based on current units."""
        query = '''
        UPDATE inventory 
        SET status = CASE 
            WHEN units_available < 5 THEN 'Critical'
            WHEN units_available < minimum_threshold THEN 'Low Stock'
            WHEN units_available > maximum_capacity * 0.8 THEN 'Full'
            WHEN units_available > maximum_capacity * 0.5 THEN 'Adequate'
            ELSE 'Normal'
        END
        WHERE blood_group = ?
        '''
        return self.execute_query(query, (blood_group,))
    
    def get_statistics(self):
        """Get system statistics."""
        stats = {}
        
        # Total donors
        query = 'SELECT COUNT(*) FROM donors'
        result = self.execute_query(query)
        stats['total_donors'] = result[0][0] if result else 0
        
        # Eligible donors
        query = 'SELECT COUNT(*) FROM donors WHERE eligible = 1'
        result = self.execute_query(query)
        stats['eligible_donors'] = result[0][0] if result else 0
        
        # Total donations
        query = 'SELECT SUM(units_donated) FROM donation_history WHERE test_result = "Passed"'
        result = self.execute_query(query)
        stats['total_donations'] = result[0][0] if result and result[0][0] else 0
        
        # Critical inventory items
        query = 'SELECT COUNT(*) FROM inventory WHERE status IN ("Critical", "Low Stock")'
        result = self.execute_query(query)
        stats['critical_inventory'] = result[0][0] if result else 0
        
        # Monthly donations
        query = '''
        SELECT strftime('%Y-%m', donation_date) as month, 
               SUM(units_donated) as total_units
        FROM donation_history 
        WHERE test_result = 'Passed'
        GROUP BY strftime('%Y-%m', donation_date)
        ORDER BY month DESC
        LIMIT 6
        '''
        stats['monthly_donations'] = self.execute_query(query)
        
        # Blood group distribution
        query = '''
        SELECT blood_group, COUNT(*) as count
        FROM donors
        GROUP BY blood_group
        ORDER BY count DESC
        '''
        stats['blood_group_dist'] = self.execute_query(query)
        
        return stats

def export_database_backup():
    """Export database to backup file."""
    import shutil
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'bloodbank_backup_{timestamp}.db'
    
    if os.path.exists('bloodbank.db'):
        shutil.copy2('bloodbank.db', backup_file)
        print(f"Database backup created: {backup_file}")
        return backup_file
    else:
        print("Database file not found!")
        return None

def check_database_health():
    """Check database health and integrity."""
    if not os.path.exists('bloodbank.db'):
        print("Database file not found!")
        return
    
    conn = sqlite3.connect('bloodbank.db')
    cursor = conn.cursor()
    
    print("Database Health Check:")
    print("=" * 50)
    
    # Check for orphaned records
    queries = [
        ("Orphaned donation records", 
         "SELECT COUNT(*) FROM donation_history WHERE donor_id NOT IN (SELECT donor_id FROM donors)"),
        ("Donations with invalid blood groups",
         "SELECT COUNT(*) FROM donation_history WHERE blood_group NOT IN ('A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-')"),
        ("Expired blood in inventory",
         "SELECT COUNT(*) FROM inventory WHERE expiry_date < DATE('now') AND units_available > 0"),
        ("Eligible donors with recent donation",
         "SELECT COUNT(*) FROM donors d JOIN donation_history dh ON d.donor_id = dh.donor_id WHERE dh.donation_date > DATE('now', '-56 days') AND d.eligible = 1")
    ]
    
    for check_name, query in queries:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        status = "⚠️ WARNING" if count > 0 else "✅ OK"
        print(f"{check_name}: {status} ({count} issues)")
    
    # Check table sizes
    print("\nTable Sizes:")
    tables = ['users', 'donors', 'inventory', 'donation_history', 'blood_requests', 'audit_log']
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} records")
        except:
            print(f"  {table}: Table not found")
    
    conn.close()

def main():
    """Main function to run database setup."""
    print("="*50)
    print("Hemo Care Database Setup")
    print("="*50)
    
    # Initialize database
    init_database()
    
    # Test the database
    print("\n" + "="*50)
    print("Testing Database Operations")
    print("="*50)
    
    db = DatabaseManager()
    
    # Test search
    print("\n1. Searching O+ donors:")
    results = db.search_donors(blood_group='O+')
    if results:
        for row in results:
            print(f"  - {row['name']} (ID: {row['donor_id']}, City: {row['city']})")
    else:
        print("  No results found")
    
    # Test inventory
    print("\n2. Current Inventory Status:")
    inventory = db.get_inventory_status()
    if inventory:
        for row in inventory:
            print(f"  {row['blood_group']}: {row['units_available']} units ({row['status']})")
    else:
        print("  Could not retrieve inventory")
    
    # Test statistics
    print("\n3. System Statistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        if key not in ['monthly_donations', 'blood_group_dist']:
            print(f"  {key}: {value}")
    
    # Create backup
    print("\n4. Creating database backup...")
    backup_file = export_database_backup()
    if backup_file:
        print(f"  Backup created: {backup_file}")


    
    # Check database health
    print("\n5. Database Health Check:")
    check_database_health()

    # Add this at the very end of database_setup.py, before if __name__ == '__main__':

def add_updated_at_column():
    """Add updated_at column to donors table if it doesn't exist"""
    conn = sqlite3.connect('bloodbank.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE donors ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ Column 'updated_at' added successfully!")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Column 'updated_at' already exists")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()

# Call this function in your main()
if __name__ == '__main__':
    add_updated_at_column()  # Add this line
    main()
