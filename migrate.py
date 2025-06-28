#!/usr/bin/env python3
"""
Database Migration Script for Keeper Member Management System
"""

from app import app, db, Admin, Member
from werkzeug.security import generate_password_hash
from datetime import date, timedelta

def create_tables():
    """Create all database tables"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")

def create_default_admin():
    """Create default admin user"""
    with app.app_context():
        # Check if admin already exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created: admin/admin123")
        else:
            print("ℹ️  Admin user already exists")

def create_sample_members():
    """Create sample member data for testing"""
    with app.app_context():
        # Check if sample data already exists
        if Member.query.count() > 0:
            print("ℹ️  Sample data already exists, skipping...")
            return
        
        sample_members = [
            {
                'name': '김철수',
                'phone': '010-1234-5678',
                'cid': 'testuser001',
                'expire_date': date.today() + timedelta(days=30),
                'amount': 50000,
                'recommender': '홍길동'
            },
            {
                'name': '이영희',
                'phone': '010-2345-6789',
                'cid': 'testuser002',
                'expire_date': date.today() + timedelta(days=3),
                'amount': 0,
                'recommender': '김철수'
            },
            {
                'name': '박민수',
                'phone': '010-3456-7890',
                'cid': 'testuser003',
                'expire_date': date.today() - timedelta(days=5),
                'amount': 50000,
                'recommender': '이영희'
            }
        ]
        
        for member_data in sample_members:
            member = Member(**member_data)
            db.session.add(member)
        
        db.session.commit()
        print("✅ Sample members created successfully!")

def reset_database():
    """Reset database (drop all tables and recreate)"""
    with app.app_context():
        print("⚠️  Dropping all tables...")
        db.drop_all()
        print("✅ All tables dropped!")
        create_tables()
        create_default_admin()
        create_sample_members()

def show_database_info():
    """Show current database information"""
    with app.app_context():
        admin_count = Admin.query.count()
        member_count = Member.query.count()
        
        print("\n📊 Database Information:")
        print(f"• Admin users: {admin_count}")
        print(f"• Members: {member_count}")
        
        if member_count > 0:
            active_count = Member.query.filter(Member.expire_date >= date.today()).count()
            expired_count = Member.query.filter(Member.expire_date < date.today()).count()
            total_amount = db.session.query(db.func.sum(Member.amount)).scalar() or 0
            
            print(f"• Active members: {active_count}")
            print(f"• Expired members: {expired_count}")
            print(f"• Total amount: {total_amount:,}원")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'create':
            create_tables()
            create_default_admin()
        elif command == 'sample':
            create_sample_members()
        elif command == 'reset':
            reset_database()
        elif command == 'info':
            show_database_info()
        else:
            print("❌ Unknown command. Available commands:")
            print("  python migrate.py create  - Create tables and default admin")
            print("  python migrate.py sample  - Create sample member data")
            print("  python migrate.py reset   - Reset entire database")
            print("  python migrate.py info    - Show database information")
    else:
        print("🚀 Keeper Database Migration Tool")
        print("=" * 40)
        print("Available commands:")
        print("  python migrate.py create  - Create tables and default admin")
        print("  python migrate.py sample  - Create sample member data")
        print("  python migrate.py reset   - Reset entire database")
        print("  python migrate.py info    - Show database information")
        print("\nExample: python migrate.py create") 