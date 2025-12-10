"""
Show current diagnostic logs to understand what's being tracked
"""
import asyncio
import asyncpg
import json

async def show_logs():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='ar_laptop_repair',
        user='postgres',
        password='9850044547'
    )
    
    print("\n" + "="*70)
    print("📋 CURRENT DIAGNOSTIC LOGS")
    print("="*70)
    
    logs = await conn.fetch("""
        SELECT session_id, stage, action, data_json, confidence, created_at
        FROM diagnostic_logs
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    if not logs:
        print("\n⚠️  No logs found - system hasn't been tested yet")
    else:
        for i, log in enumerate(logs, 1):
            print(f"\n--- Log Entry #{i} ---")
            print(f"Session: {log['session_id']}")
            print(f"Stage: {log['stage']}")
            print(f"Action: {log['action']}")
            print(f"Confidence: {log['confidence']:.3f}" if log['confidence'] else "Confidence: N/A")
            print(f"Time: {log['created_at']}")
            
            if log['data_json']:
                data = json.loads(log['data_json'])
                print(f"Data:")
                for key, value in data.items():
                    if isinstance(value, dict) and len(str(value)) > 100:
                        print(f"  {key}: {{...}} (large dict)")
                    else:
                        print(f"  {key}: {value}")
    
    await conn.close()
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(show_logs())
