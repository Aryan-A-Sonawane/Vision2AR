"""
Setup Weaviate cloud instance schema
"""
import os
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

def setup_weaviate_schema():
    """Create Weaviate schema for tutorials"""
    
    print("=" * 60)
    print("Weaviate Schema Setup")
    print("=" * 60)
    
    print(f"\nConnecting to: {WEAVIATE_URL}")
    
    # Connect to Weaviate cloud
    client = weaviate.connect_to_wcs(
        cluster_url=WEAVIATE_URL,
        auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY)
    )
    
    try:
        # Check connection
        if client.is_ready():
            print("✓ Connected to Weaviate cloud")
        else:
            print("✗ Weaviate not ready")
            return False
        
        # Check if Tutorial class already exists
        collections = client.collections.list_all()
        collection_names = [name for name in collections.keys()]
        
        if "Tutorial" in collection_names:
            print("\n⚠ Tutorial class already exists. Deleting and recreating...")
            client.collections.delete("Tutorial")
        
        # Create Tutorial collection with properties
        print("\nCreating Tutorial class...")
        
        collection = client.collections.create(
            name="Tutorial",
            description="Laptop repair tutorials with embeddings",
            vectorizer_config=Configure.Vectorizer.none(),  # We'll provide embeddings manually
            properties=[
                Property(
                    name="tutorial_id",
                    data_type=DataType.INT,
                    description="PostgreSQL tutorial ID"
                ),
                Property(
                    name="brand",
                    data_type=DataType.TEXT,
                    description="Laptop brand (dell, lenovo, hp, etc.)"
                ),
                Property(
                    name="model",
                    data_type=DataType.TEXT,
                    description="Laptop model"
                ),
                Property(
                    name="issue_type",
                    data_type=DataType.TEXT,
                    description="Type of issue (display, power, thermal, etc.)"
                ),
                Property(
                    name="title",
                    data_type=DataType.TEXT,
                    description="Tutorial title"
                ),
                Property(
                    name="keywords",
                    data_type=DataType.TEXT_ARRAY,
                    description="Extracted keywords for matching"
                ),
                Property(
                    name="source",
                    data_type=DataType.TEXT,
                    description="Source: oem or ifixit"
                ),
                Property(
                    name="difficulty",
                    data_type=DataType.TEXT,
                    description="Difficulty level: easy, medium, hard"
                ),
                Property(
                    name="category",
                    data_type=DataType.TEXT,
                    description="Device category: PC, Mac, Computer Hardware, Phone, etc."
                )
            ]
        )
        
        print("✓ Tutorial class created successfully")
        
        # Verify schema
        print("\nVerifying schema...")
        schema = client.collections.get("Tutorial")
        print(f"✓ Class 'Tutorial' exists")
        print(f"  Properties: {len(schema.config.get().properties)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error setting up Weaviate schema: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

def test_weaviate_connection():
    """Test connection to Weaviate"""
    try:
        client = weaviate.connect_to_wcs(
            cluster_url=WEAVIATE_URL,
            auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY)
        )
        
        if client.is_ready():
            print("✓ Weaviate connection test successful")
            meta = client.get_meta()
            print(f"  Version: {meta.get('version', 'unknown')}")
            client.close()
            return True
        else:
            print("✗ Weaviate not ready")
            return False
            
    except Exception as e:
        print(f"✗ Weaviate connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("\n[Step 1] Testing Weaviate connection...")
    if not test_weaviate_connection():
        print("\n✗ Please check Weaviate credentials in .env")
        return
    
    print("\n[Step 2] Creating schema...")
    success = setup_weaviate_schema()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Weaviate setup complete!")
        print("=" * 60)
        print("\nReady to:")
        print("  - Store tutorial embeddings")
        print("  - Perform semantic search")
        print("  - Match user queries to tutorials")
    else:
        print("\n✗ Weaviate setup failed")

if __name__ == "__main__":
    main()
