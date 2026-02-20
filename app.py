from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
import hashlib
import random
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'bloodbank-secure-key-123456'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect('bloodbank.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_age(dob):
    try:
        birth_date = datetime.strptime(dob, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return 0

def generate_donor_id():
    return f'DON{random.randint(10000, 99999)}'

def generate_donation_id():
    return f'DONATION{random.randint(1000, 9999)}'

def init_db():
    if not os.path.exists('bloodbank.db'):
        conn = sqlite3.connect('bloodbank.db')
        c = conn.cursor()
        
        # Create tables
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'staff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS donors (
                donor_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                date_of_birth DATE NOT NULL,
                age INTEGER,
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
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blood_group TEXT UNIQUE NOT NULL,
                units_available INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Normal',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS donation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donation_id TEXT UNIQUE NOT NULL,
                donor_id TEXT NOT NULL,
                donor_name TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                units_donated INTEGER NOT NULL,
                donation_date DATE NOT NULL,
                expiry_date DATE,
                received_by TEXT,
                test_result TEXT DEFAULT 'Passed',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if tables are empty before inserting
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            # Insert default users
            c.execute("INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
                     ('admin@bloodbank.com', hash_password('admin123'), 'System Administrator', 'admin'))
            c.execute("INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
                     ('staff@bloodbank.com', hash_password('staff123'), 'John Doe', 'staff'))
            print("Default users created")
        
        c.execute("SELECT COUNT(*) FROM inventory")
        if c.fetchone()[0] == 0:
            # Insert inventory
            blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
            for bg in blood_groups:
                units = random.randint(5, 25)
                status = 'Low Stock' if units < 10 else 'Normal' if units < 20 else 'High Stock'
                c.execute("INSERT INTO inventory (blood_group, units_available, status) VALUES (?, ?, ?)",
                         (bg, units, status))
            print("Inventory initialized")
        
        conn.commit()
        conn.close()
        print("Database initialization complete!")

# Initialize database on startup
init_db()

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash('Please fill in all fields', 'danger')
            return render_template('login.html')
        
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? AND password = ?',
            (email, hash_password(password))
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session.permanent = True
            
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not all([name, email, password, confirm_password]):
            flash('Please fill in all fields', 'danger')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('signup.html')
        
        # Email validation
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address', 'danger')
            return render_template('signup.html')
        
        try:
            conn = get_db()
            conn.execute(
                'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                (name, email, hash_password(password))
            )
            conn.commit()
            conn.close()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    
    # Get statistics
    total_donors = conn.execute('SELECT COUNT(*) FROM donors').fetchone()[0] or 0
    
    total_donations_result = conn.execute('SELECT SUM(units_donated) FROM donation_history').fetchone()
    total_donations = total_donations_result[0] if total_donations_result and total_donations_result[0] else 0
    
    low_stock = conn.execute('SELECT COUNT(*) FROM inventory WHERE status = "Low Stock"').fetchone()[0] or 0
    
    # Get recent donations (last 5)
    recent_donations = conn.execute('''
        SELECT donor_name, blood_group, units_donated, donation_date
        FROM donation_history
        ORDER BY donation_date DESC
        LIMIT 5
    ''').fetchall()
    
    # Get upcoming expiries (within 7 days)
    upcoming_expiries = conn.execute('''
        SELECT blood_group, COUNT(*) as expiring_units
        FROM donation_history
        WHERE expiry_date BETWEEN DATE('now') AND DATE('now', '+7 days')
        GROUP BY blood_group
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html',
                         name=session['user_name'],
                         role=session['user_role'],
                         total_donors=total_donors,
                         total_donations=total_donations,
                         low_stock=low_stock,
                         recent_donations=recent_donations,
                         upcoming_expiries=upcoming_expiries)

@app.route('/add_donor', methods=['GET', 'POST'])
@login_required
def add_donor():
    if request.method == 'POST':
        # Generate donor ID
        donor_id = generate_donor_id()
        
        # Get form data
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        blood_group = request.form.get('blood_group', '')
        city = request.form.get('city', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()
        medical_details = request.form.get('medical_details', '').strip()
        
        # Validation
        required_fields = {'name': name, 'dob': dob, 'gender': gender, 
                          'blood_group': blood_group, 'city': city, 'phone': phone}
        for field, value in required_fields.items():
            if not value:
                flash(f'Please fill in {field.replace("_", " ")}', 'danger')
                return render_template('add_donor.html')
        
        # Calculate age
        age = calculate_age(dob)
        
        # Check eligibility (18-65 years)
        eligible = 1 if 18 <= age <= 65 else 0
        
        conn = get_db()
        
        try:
            # Insert donor
            conn.execute('''
                INSERT INTO donors (donor_id, name, date_of_birth, age, gender, 
                                  blood_group, city, phone, email, medical_details, eligible)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (donor_id, name, dob, age, gender, blood_group, city, phone, email, medical_details, eligible))
            
            # Check if donation is made
            if request.form.get('make_donation') == 'yes':
                units_donated = int(request.form.get('units_donated', 1))
                donation_date = request.form.get('donation_date', datetime.today().strftime('%Y-%m-%d'))
                
                # Generate donation ID
                donation_id = generate_donation_id()
                
                # Calculate expiry date (42 days from donation)
                donation_datetime = datetime.strptime(donation_date, '%Y-%m-%d')
                expiry_date = (donation_datetime + timedelta(days=42)).strftime('%Y-%m-%d')
                
                # Add to history
                conn.execute('''
                    INSERT INTO donation_history (donation_id, donor_id, donor_name, 
                                                blood_group, units_donated, donation_date, 
                                                expiry_date, received_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (donation_id, donor_id, name, blood_group, units_donated, 
                      donation_date, expiry_date, session['user_name']))
                
                # Update donor's last donation date
                conn.execute('''
                    UPDATE donors 
                    SET last_donation_date = ?
                    WHERE donor_id = ?
                ''', (donation_date, donor_id))
                
                # Update inventory
                conn.execute('''
                    UPDATE inventory 
                    SET units_available = units_available + ?
                    WHERE blood_group = ?
                ''', (units_donated, blood_group))
                
                # Update inventory status
                conn.execute('''
                    UPDATE inventory 
                    SET status = CASE 
                        WHEN units_available < 10 THEN 'Low Stock'
                        WHEN units_available > 20 THEN 'High Stock'
                        ELSE 'Normal'
                    END,
                    last_updated = CURRENT_TIMESTAMP
                    WHERE blood_group = ?
                ''', (blood_group,))
                
                flash(f'Donor and donation added successfully! Donor ID: {donor_id}, Donation ID: {donation_id}', 'success')
            else:
                flash(f'Donor added successfully! Donor ID: {donor_id}', 'success')
            
            conn.commit()
            
        except sqlite3.IntegrityError as e:
            flash(f'Database error: Donor ID or Donation ID already exists. Try again.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('add_donor'))
    
    return render_template('add_donor.html')

@app.route('/donors')
@login_required
def donors():
    search = request.args.get('search', '').strip()
    blood_group = request.args.get('blood_group', '')
    city = request.args.get('city', '').strip()
    
    conn = get_db()
    
    query = '''
        SELECT donor_id, name, age, gender, blood_group, city, phone, email, 
               eligible, last_donation_date
        FROM donors 
        WHERE 1=1
    '''
    params = []
    
    if search:
        query += ' AND (name LIKE ? OR donor_id LIKE ? OR phone LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if blood_group:
        query += ' AND blood_group = ?'
        params.append(blood_group)
    
    if city:
        query += ' AND city LIKE ?'
        params.append(f'%{city}%')
    
    query += ' ORDER BY name'
    
    donors_list = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('donors.html', donors=donors_list, 
                         search=search, blood_group=blood_group, city=city)

@app.route('/donor/<donor_id>')
@login_required
def donor_detail(donor_id):
    conn = get_db()
    
    donor = conn.execute('''
        SELECT * FROM donors WHERE donor_id = ?
    ''', (donor_id,)).fetchone()
    
    if not donor:
        flash('Donor not found', 'danger')
        return redirect(url_for('donors'))
    
    # Get donation history for this donor
    donations = conn.execute('''
        SELECT donation_id, units_donated, donation_date, expiry_date, 
               received_by, test_result, notes
        FROM donation_history
        WHERE donor_id = ?
        ORDER BY donation_date DESC
    ''', (donor_id,)).fetchall()
    
    conn.close()
    
    return render_template('donor_detail.html', donor=donor, donations=donations)

@app.route('/add_donation', methods=['GET', 'POST'])
@login_required
def add_donation():
    if request.method == 'POST':
        donor_id = request.form.get('donor_id', '').strip()
        units_donated = int(request.form.get('units_donated', 1))
        donation_date = request.form.get('donation_date', datetime.today().strftime('%Y-%m-%d'))
        notes = request.form.get('notes', '').strip()
        
        if not donor_id:
            flash('Please enter a donor ID', 'danger')
            return render_template('add_donation.html')
        
        conn = get_db()
        
        # Check if donor exists
        donor = conn.execute('SELECT * FROM donors WHERE donor_id = ?', (donor_id,)).fetchone()
        if not donor:
            flash('Donor not found. Please add donor first.', 'danger')
            conn.close()
            return redirect(url_for('add_donor'))
        
        # Check if donor is eligible
        if not donor['eligible']:
            flash('Donor is not eligible to donate blood', 'danger')
            conn.close()
            return redirect(url_for('donor_detail', donor_id=donor_id))
        
        try:
            # Generate donation ID
            donation_id = generate_donation_id()
            
            # Calculate expiry date
            donation_datetime = datetime.strptime(donation_date, '%Y-%m-%d')
            expiry_date = (donation_datetime + timedelta(days=42)).strftime('%Y-%m-%d')
            
            # Add to history
            conn.execute('''
                INSERT INTO donation_history (donation_id, donor_id, donor_name, 
                                            blood_group, units_donated, donation_date, 
                                            expiry_date, received_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (donation_id, donor_id, donor['name'], donor['blood_group'], 
                  units_donated, donation_date, expiry_date, session['user_name'], notes))
            
            # Update donor's last donation date
            conn.execute('''
                UPDATE donors 
                SET last_donation_date = ?
                WHERE donor_id = ?
            ''', (donation_date, donor_id))
            
            # Update inventory
            conn.execute('''
                UPDATE inventory 
                SET units_available = units_available + ?
                WHERE blood_group = ?
            ''', (units_donated, donor['blood_group']))
            
            # Update inventory status
            conn.execute('''
                UPDATE inventory 
                SET status = CASE 
                    WHEN units_available < 10 THEN 'Low Stock'
                    WHEN units_available > 20 THEN 'High Stock'
                    ELSE 'Normal'
                END,
                last_updated = CURRENT_TIMESTAMP
                WHERE blood_group = ?
            ''', (donor['blood_group'],))
            
            conn.commit()
            conn.close()
            
            flash(f'Donation recorded successfully! Donation ID: {donation_id}', 'success')
            return redirect(url_for('donor_detail', donor_id=donor_id))
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            conn.close()
    
    return render_template('add_donation.html')

@app.route('/search_blood', methods=['GET', 'POST'])
@login_required
def search_blood():
    donors = []
    blood_group = ''
    
    if request.method == 'POST':
        blood_group = request.form.get('blood_group', '')
        city = request.form.get('city', '').strip()
        
        if not blood_group:
            flash('Please select a blood group', 'danger')
            return render_template('search_blood.html')
        
        conn = get_db()
        
        query = '''
            SELECT donor_id, name, age, gender, blood_group, city, phone, email, eligible,
                   last_donation_date
            FROM donors 
            WHERE blood_group = ? AND eligible = 1
        '''
        params = [blood_group]
        
        if city:
            query += ' AND city LIKE ?'
            params.append(f'%{city}%')
        
        query += ' ORDER BY last_donation_date ASC'
        
        # Get rows and convert to dictionaries - THIS IS THE FIX
        rows = conn.execute(query, params).fetchall()
        donors = [dict(row) for row in rows]  # Simple one-line fix!
        
        conn.close()
        
        if not donors:
            flash(f'No eligible donors found for blood group {blood_group}', 'info')
    
    return render_template('search_blood.html', donors=donors, blood_group=blood_group)

@app.route('/donor_info/<donor_id>')
@login_required
def donor_info(donor_id):
    conn = get_db()
    
    # Get donor details
    donor_row = conn.execute('''
        SELECT * FROM donors WHERE donor_id = ?
    ''', (donor_id,)).fetchone()
    
    if not donor_row:
        flash('Donor not found', 'danger')
        conn.close()
        return redirect(url_for('donors'))
    
    # Convert to dictionary
    donor = dict(donor_row)
    
    # Get donation history
    donation_rows = conn.execute('''
        SELECT donation_id, units_donated, donation_date, expiry_date, 
               received_by, test_result, notes
        FROM donation_history
        WHERE donor_id = ?
        ORDER BY donation_date DESC
    ''', (donor_id,)).fetchall()
    
    # Convert to list of dictionaries
    donations = [dict(row) for row in donation_rows]
    
    conn.close()
    
    return render_template('donor_detail.html', donor=donor, donations=donations)

@app.route('/inventory')
@login_required
def inventory():
    conn = get_db()
    
    # Get all blood groups with inventory
    inventory_data = conn.execute('''
        SELECT blood_group, units_available, status, last_updated
        FROM inventory
        ORDER BY 
            CASE blood_group
                WHEN 'O-' THEN 1
                WHEN 'O+' THEN 2
                WHEN 'A-' THEN 3
                WHEN 'A+' THEN 4
                WHEN 'B-' THEN 5
                WHEN 'B+' THEN 6
                WHEN 'AB-' THEN 7
                WHEN 'AB+' THEN 8
            END
    ''').fetchall()
    
    # Get expiring soon items
    expiring_soon = conn.execute('''
        SELECT blood_group, COUNT(*) as expiring_count,
               MIN(expiry_date) as earliest_expiry
        FROM donation_history
        WHERE expiry_date BETWEEN DATE('now') AND DATE('now', '+7 days')
        GROUP BY blood_group
    ''').fetchall()
    
    conn.close()
    
    return render_template('inventory.html', 
                         inventory=inventory_data,
                         expiring_soon=expiring_soon)

@app.route('/history')
@login_required
def history():
    conn = get_db()
    
    donor_id = request.args.get('donor_id', '').strip()
    blood_group = request.args.get('blood_group', '')
    
    query = '''
        SELECT dh.donation_id, dh.donor_id, 
               COALESCE(d.name, dh.donor_name) as donor_name, 
               COALESCE(d.blood_group, dh.blood_group) as blood_group,
               dh.units_donated, dh.donation_date, dh.expiry_date, 
               dh.received_by, dh.test_result, dh.notes
        FROM donation_history dh
        LEFT JOIN donors d ON dh.donor_id = d.donor_id
        WHERE 1=1
    '''
    params = []
    
    if donor_id:
        query += ' AND dh.donor_id LIKE ?'
        params.append(f'%{donor_id}%')
    
    if blood_group:
        query += ' AND (dh.blood_group = ? OR d.blood_group = ?)'
        params.extend([blood_group, blood_group])
    
    query += ' ORDER BY dh.donation_date DESC'
    
    history_data = conn.execute(query, params).fetchall()
    history_list = [dict(row) for row in history_data]
    conn.close()
    
    return render_template('history.html', history=history_list)

@app.route('/edit_donor/<donor_id>', methods=['GET', 'POST'])
@login_required
def edit_donor(donor_id):
    conn = get_db()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        blood_group = request.form.get('blood_group', '')
        city = request.form.get('city', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()
        medical_details = request.form.get('medical_details', '').strip()
        eligible = 1 if request.form.get('eligible') else 0
        
        # Calculate age
        from datetime import datetime
        try:
            birth_date = datetime.strptime(dob, '%Y-%m-%d')
            today = datetime.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            age = 0
        
        try:
            # Update donor in donors table
            conn.execute('''
                UPDATE donors 
                SET name = ?, date_of_birth = ?, age = ?, gender = ?, 
                    blood_group = ?, city = ?, phone = ?, email = ?,
                    medical_details = ?, eligible = ?
                WHERE donor_id = ?
            ''', (name, dob, age, gender, blood_group, city, phone, email,
                  medical_details, eligible, donor_id))
            
            # IMPORTANT: Update donation_history
            conn.execute('''
                UPDATE donation_history 
                SET donor_name = ?, blood_group = ?
                WHERE donor_id = ?
            ''', (name, blood_group, donor_id))
            
            conn.commit()
            flash('Donor details updated successfully!', 'success')
            conn.close()
            return redirect(url_for('donor_detail', donor_id=donor_id))
            
        except Exception as e:
            flash(f'Error updating donor: {str(e)}', 'danger')
            conn.close()
            return redirect(url_for('edit_donor', donor_id=donor_id))
    
    # GET request - show edit form
    donor = conn.execute('SELECT * FROM donors WHERE donor_id = ?', (donor_id,)).fetchone()
    conn.close()
    
    if not donor:
        flash('Donor not found', 'danger')
        return redirect(url_for('donors'))
    
    # Convert to dictionary
    donor = dict(donor)
    
    return render_template('edit_donor.html', donor=donor)
@app.route('/profile')
@login_required
def profile():
    conn = get_db()

    user = conn.execute('''
        SELECT id, name, email, role, created_at
        FROM users
        WHERE id = ?
    ''', (session['user_id'],)).fetchone()
    conn.close()
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('logout'))
    
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not name or not email:
        flash('Name and email are required', 'danger')
        return redirect(url_for('profile'))
    
    conn = get_db()
    
    try:
        # Check if email is already taken by another user
        existing_user = conn.execute(
            'SELECT id FROM users WHERE email = ? AND id != ?',
            (email, session['user_id'])
        ).fetchone()
        
        if existing_user:
            flash('Email already taken by another user', 'danger')
            conn.close()
            return redirect(url_for('profile'))
        
        # Update user info
        conn.execute('''
            UPDATE users SET name = ?, email = ? WHERE id = ?
        ''', (name, email, session['user_id']))
        
        # Update password if provided
        if current_password and new_password and confirm_password:
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                conn.close()
                return redirect(url_for('profile'))
            
            if len(new_password) < 6:
                flash('New password must be at least 6 characters', 'danger')
                conn.close()
                return redirect(url_for('profile'))
            
            # Verify current password
            user = conn.execute('''
                SELECT password FROM users WHERE id = ?
            ''', (session['user_id'],)).fetchone()
            
            if user['password'] != hash_password(current_password):
                flash('Current password is incorrect', 'danger')
                conn.close()
                return redirect(url_for('profile'))
            
            # Update password
            conn.execute('''
                UPDATE users SET password = ? WHERE id = ?
            ''', (hash_password(new_password), session['user_id']))
        
        conn.commit()
        conn.close()
        
        # Update session
        session['user_name'] = name
        session['user_email'] = email
        
        flash('Profile updated successfully', 'success')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/api/update_stock', methods=['POST'])
@login_required
def update_stock():
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    try:
        data = request.json
        blood_group = data.get('blood_group', '').strip()
        units = int(data.get('units', 0))
        action = data.get('action', '').strip()
        
        if not blood_group or units <= 0 or action not in ['add', 'remove']:
            return jsonify({'error': 'Invalid parameters'}), 400
        
        conn = get_db()
        
        if action == 'remove':
            current = conn.execute('SELECT units_available FROM inventory WHERE blood_group = ?',
                                 (blood_group,)).fetchone()
            if not current or current['units_available'] < units:
                conn.close()
                return jsonify({'error': 'Not enough units available'}), 400
        
        # Update inventory
        if action == 'add':
            conn.execute('UPDATE inventory SET units_available = units_available + ? WHERE blood_group = ?',
                        (units, blood_group))
        else:
            conn.execute('UPDATE inventory SET units_available = units_available - ? WHERE blood_group = ?',
                        (units, blood_group))
        
        # Update status
        conn.execute('''
            UPDATE inventory 
            SET status = CASE 
                WHEN units_available < 10 THEN 'Low Stock'
                WHEN units_available > 20 THEN 'High Stock'
                ELSE 'Normal'
            END,
            last_updated = CURRENT_TIMESTAMP
            WHERE blood_group = ?
        ''', (blood_group,))
        
        updated = conn.execute('SELECT units_available, status FROM inventory WHERE blood_group = ?',
                             (blood_group,)).fetchone()
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'units_available': updated['units_available'],
            'status': updated['status']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Health check endpoint
@app.route('/health')
def health():
    try:
        conn = get_db()
        conn.execute('SELECT 1')
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500

if __name__ == '__main__':
    print("="*60)
    print("Hemo Care Blood Management System")
    print("="*60)
    print("Server: http://localhost:5000")
    print("Admin Login: admin@bloodbank.com / admin123")
    print("Staff Login: staff@bloodbank.com / staff123")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print("="*60)
    
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Created templates directory")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
    import sqlite3
from flask import Flask, g

app = Flask(__name__)
DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, timeout=10)
        db.execute('PRAGMA journal_mode=WAL')
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Helper function for queries
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# Example route
@app.route('/donors')
def donors():
    donors = query_db('SELECT * FROM donors')
    return render_template('donors.html', donors=donors)