import sqlite3
from datetime import datetime
import os

def check_database():
    print("🔍 CHECKING DATABASE IN DOCKER CONTAINER")
    print("=" * 60)
    
    # Gunakan path yang sama dengan di Docker container
    db_path = '/data/guardiantix.db'  # Path di dalam container
    # atau jika mau akses dari local, copy dulu dari container
    
    try:
        conn = sqlite3.connect('guardiantix.db')
        cursor = conn.cursor()
        
        # Cek semua tabel
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("📊 TABLES:", [table[0] for table in tables])
        
        # Cek data users
        if 'users' in [table[0] for table in tables]:
            print("\n👥 USERS DATA:")
            print("-" * 60)
            cursor.execute("SELECT * FROM users;")
            users = cursor.fetchall()
            
            print(f"Total users: {len(users)}")
            for user in users:
                print(f"ID: {user[0]} | Username: {user[1]} | Email: {user[2]} | Role: {user[4]} | Join: {user[6]}")
        
        # Cek data concerts
        if 'concerts' in [table[0] for table in tables]:
            print("\n🎵 CONCERTS DATA:")
            print("-" * 60)
            cursor.execute("SELECT * FROM concerts;")
            concerts = cursor.fetchall()
            
            print(f"Total concerts: {len(concerts)}")
            for concert in concerts:
                print(f"ID: {concert[0]} | {concert[1]} by {concert[2]} | Date: {concert[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Solution: Copy database from container first!")
        copy_database_from_container()

def copy_database_from_container():
    print("\n📥 Copying database from container...")
    print("Run this command in PowerShell:")
    print('docker cp pbl-rks-306-backupfinal-database-api-1:/data/guardiantix.db ./guardiantix.db')

if __name__ == "__main__":
    check_database()