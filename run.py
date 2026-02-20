#!/usr/bin/env python3
"""
Blood Bank Management System - Startup Script
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = ['flask']
    
    print("🔍 Checking dependencies...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            print(f"   Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")

def setup_database():
    """Initialize the database."""
    print("\n🗄️  Setting up database...")
    try:
        from database import init_database
        init_database()
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def start_server():
    """Start the Flask server."""
    print("\n🚀 Starting Blood Bank System...")
    print("\n" + "="*60)
    print("HEMO CARE SYSTEM")
    print("="*60)
    print("\n📋 System Information:")
    print(f"   Python Version: {sys.version.split()[0]}")
    print("   Server: Flask Development Server")
    print("   Port: 5000")
    print("\n🔐 Login Credentials:")
    print("   Admin: admin@bloodbank.com / admin123")
    print("   Staff: staff@bloodbank.com / staff123")
    print("\n" + "="*60)
    print("\n🌐 Starting server... Press Ctrl+C to stop")
    print("➡️  Open your browser and go to: http://localhost:5000")
    print("\n" + "="*60)
    
    # Start Flask app
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    try:
        subprocess.run([sys.executable, "-m", "flask", "run", "--debug"])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

def main():
    """Main function."""
    print("\n" + "="*60)
    print("🏥 BLOOD BANK MANAGEMENT SYSTEM")
    print("="*60)
    
    # Check if database exists
    if not os.path.exists('bloodbank.db'):
        print("\n⚠️  Database not found!")
        setup = input("Do you want to create the database? (yes/no): ")
        if setup.lower() != 'yes':
            print("Exiting...")
            return
        
        if not setup_database():
            return
    
    # Check dependencies
    check_dependencies()
    
    # Start server
    start_server()

if __name__ == '__main__':
    main()