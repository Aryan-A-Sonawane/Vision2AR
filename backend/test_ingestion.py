"""
Test data ingestion with your OEM manuals
"""

import os
from pathlib import Path
from data_sources.ingestion_pipeline import DataIngestionPipeline

# Initialize pipeline
pipeline = DataIngestionPipeline(output_dir="./ingested_data")

print("\n" + "="*60)
print("TESTING DATA INGESTION PIPELINE")
print("="*60)

# List available manuals
manuals_path = Path("../manuals")
print(f"\n📁 Checking manuals directory: {manuals_path.absolute()}")

if manuals_path.exists():
    for brand_dir in manuals_path.iterdir():
        if brand_dir.is_dir():
            pdfs = list(brand_dir.glob("*.pdf"))
            print(f"\n  {brand_dir.name.upper()}:")
            print(f"    Found {len(pdfs)} PDF(s)")
            for pdf in pdfs:
                print(f"    - {pdf.name} ({pdf.stat().st_size / 1024 / 1024:.1f} MB)")
else:
    print("  ⚠️ Manuals directory not found!")
    print(f"  Create: {manuals_path.absolute()}")
    print("  Structure: manuals/lenovo/*.pdf, manuals/dell/*.pdf, etc.")

print("\n" + "-"*60)
print("EXAMPLE: Ingest Lenovo IdeaPad 5 battery replacement")
print("-"*60)

# Example ingestion (uncomment when you have PDFs)
try:
    result = pipeline.ingest_device(
        device_model="IdeaPad 5",
        brand="lenovo",
        component="battery",
        youtube_urls=[]  # Add YouTube URLs if you have any
    )
    
    print("\n✅ INGESTION SUCCESSFUL!")
    print(f"   Device: {result['brand']} {result['device_model']}")
    print(f"   Component: {result['component']}")
    print(f"   Total steps: {result['total_steps']}")
    print(f"   Sources used: {', '.join(result['sources_used'])}")
    print(f"   Output file: ingested_data/{result['brand']}_{result['device_model']}_{result['component']}.json")
    
except FileNotFoundError:
    print("\n⚠️ No manuals found for this device/component")
    print("   Add PDF manuals to: manuals/lenovo/")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("1. Add OEM PDF manuals to manuals/{brand}/ folders")
print("2. Run this script to ingest data")
print("3. Generated JSON files will be in: ./ingested_data/")
print("4. Import JSON data into PostgreSQL database")
print("5. Connect frontend to backend APIs")
print("\n")
