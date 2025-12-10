"""
Extract knowledge from OEM manuals and build ML knowledge base
Run this first to prepare data for diagnosis engine
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from diagnosis.manual_extractor import ManualExtractor

def main():
    print("="*70)
    print(" OEM Manual Knowledge Extraction")
    print("="*70)
    print()
    print("This script extracts repair procedures from PDF manuals")
    print("and builds a knowledge base for ML-powered diagnosis.")
    print()
    
    # Initialize extractor
    manuals_dir = os.path.join(os.path.dirname(__file__), "../manuals")
    extractor = ManualExtractor(manuals_dir)
    
    # Extract from all PDFs
    print("Starting extraction...")
    print()
    extractor.extract_all_manuals()
    
    # Save knowledge base
    output_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
    extractor.save_knowledge_base(output_path)
    
    print()
    print("="*70)
    print("✓ Knowledge extraction complete!")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Review knowledge_base.json to see extracted procedures")
    print("  2. Start backend: python main.py")
    print("  3. Backend will automatically use knowledge-based diagnosis")
    print()
    print("The ML model now learns from your OEM manuals!")
    print()

if __name__ == "__main__":
    main()
