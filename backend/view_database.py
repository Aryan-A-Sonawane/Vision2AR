"""
PostgreSQL Database Viewer
Shows all tables and data in the ar_laptop_repair database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ar_laptop_repair',
    'user': 'postgres',
    'password': '9850044547'
}

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Make sure PostgreSQL is running:")
        print("   - Check services: services.msc → PostgreSQL")
        print("   - Or run: pg_ctl -D \"C:\\Program Files\\PostgreSQL\\16\\data\" start")
        return None

def list_tables(conn):
    """List all tables in the database"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    cursor.close()
    return [t[0] for t in tables]

def view_table(conn, table_name):
    """View contents of a table"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
    rows = cursor.fetchall()
    
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
    total = cursor.fetchone()['count']
    
    cursor.close()
    return rows, total

def main():
    print("=" * 80)
    print("📊 AR Laptop Repair Database Viewer")
    print("=" * 80)
    print(f"\n🔗 Connecting to: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    conn = connect_db()
    if not conn:
        return
    
    print("✅ Connected successfully!\n")
    
    # List all tables
    tables = list_tables(conn)
    
    if not tables:
        print("⚠️  No tables found in database.")
        print("\n💡 You may need to create the schema first:")
        print("   Run: psql -U postgres -d ar_laptop_repair -f schema.sql")
    else:
        print(f"📋 Found {len(tables)} table(s):\n")
        
        for table in tables:
            print(f"\n{'=' * 80}")
            print(f"📁 Table: {table}")
            print('=' * 80)
            
            rows, total = view_table(conn, table)
            
            if rows:
                # Convert to list of dicts for tabulate
                print(f"\nShowing first 10 of {total} total rows:\n")
                print(tabulate(rows, headers="keys", tablefmt="grid"))
            else:
                print(f"\n(empty - {total} rows)")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("🔧 Database Tools:")
    print("=" * 80)
    print("\n1. pgAdmin 4 - GUI Tool:")
    print("   - Open pgAdmin from Start Menu")
    print("   - Right-click 'Servers' → Register → Server")
    print(f"   - Host: {DB_CONFIG['host']}, Port: {DB_CONFIG['port']}")
    print(f"   - Database: {DB_CONFIG['database']}")
    print(f"   - Username: {DB_CONFIG['user']}, Password: {DB_CONFIG['password']}")
    
    print("\n2. psql - Command Line:")
    print(f"   psql -U postgres -d ar_laptop_repair")
    print("   Password: 9850044547")
    
    print("\n3. DBeaver - Universal Tool:")
    print("   - Download: https://dbeaver.io/download/")
    print("   - New Connection → PostgreSQL")
    print(f"   - Same credentials as above")
    
    print("\n4. VS Code Extension:")
    print("   - Install: PostgreSQL by Chris Kolkman")
    print("   - Connect with same credentials")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
