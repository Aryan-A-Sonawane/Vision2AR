"""
Verify database setup and connections
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.db_utils import DatabaseConnection, get_stats
from database.weaviate_utils import WeaviateConnection, get_weaviate_stats

async def verify_setup():
    """Verify PostgreSQL and Weaviate setup"""
    
    print("=" * 60)
    print("Database Setup Verification")
    print("=" * 60)
    
    # Test PostgreSQL
    print("\n[1] PostgreSQL Connection")
    try:
        pool = await DatabaseConnection.get_pool()
        print("✓ PostgreSQL connected")
        
        # Get stats
        stats = await get_stats()
        print(f"  Total tutorials: {stats['total_tutorials']}")
        print(f"  Total steps: {stats['total_steps']}")
        print(f"  Total tools: {stats['total_tools']}")
        print(f"  Total sessions: {stats['total_sessions']}")
        
        if stats['by_brand']:
            print("  Tutorials by brand:")
            for item in stats['by_brand']:
                print(f"    - {item['brand']}: {item['count']}")
        
        if stats['by_source']:
            print("  Tutorials by source:")
            for item in stats['by_source']:
                print(f"    - {item['source']}: {item['count']}")
        
        await DatabaseConnection.close_pool()
        
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False
    
    # Test Weaviate
    print("\n[2] Weaviate Connection")
    try:
        client = WeaviateConnection.get_client()
        
        if client.is_ready():
            print("✓ Weaviate connected")
            
            # Get stats
            w_stats = get_weaviate_stats()
            print(f"  Total tutorials: {w_stats['total_tutorials']}")
            print(f"  Status: {w_stats['status']}")
        else:
            print("✗ Weaviate not ready")
            return False
        
        WeaviateConnection.close_client()
        
    except Exception as e:
        print(f"✗ Weaviate connection failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All systems ready!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Run seed_ifixit.py to populate with iFixit tutorials")
    print("  2. Run seed_oem.py to migrate existing OEM manuals")
    print("  3. Start using the tutorial matching system")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(verify_setup())
    sys.exit(0 if result else 1)
