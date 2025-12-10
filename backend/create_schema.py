"""Create database schema and load sample data"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ar_laptop_repair',
    'user': 'postgres',
    'password': '9850044547'
}

def create_schema():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("📊 Creating database schema...")
    
    # Read and execute schema
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    try:
        cursor.execute(schema_sql)
        conn.commit()
        print("✅ Schema created successfully!")
        
        # Show what was created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"\n📋 Created {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"   - {table[0]}: {count} rows")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_schema()
