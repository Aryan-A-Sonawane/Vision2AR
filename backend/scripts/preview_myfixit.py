"""
Preview MyFixit data before ingestion
Shows sample tutorials and statistics
"""
import json
from pathlib import Path

MYFIXIT_PATH = Path(__file__).parent.parent / "data" / "myfixit" / "jsons"

def preview_category(category_file: str, max_samples: int = 3):
    """Preview tutorials from a category file"""
    filepath = MYFIXIT_PATH / category_file
    if not filepath.exists():
        print(f"[WARN] File not found: {filepath}")
        return
    
    print(f"\n{'='*70}")
    print(f"CATEGORY: {category_file}")
    print(f"{'='*70}")
    
    guides = []
    total_steps = 0
    total_tools = 0
    with_images = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                guide = json.loads(line)
                guides.append(guide)
                
                # Use capital-first keys (MyFixit format)
                steps = guide.get("Steps", [])
                total_steps += len(steps)
                total_tools += len(guide.get("Toolbox", []))
                
                # Check for images in steps
                if any("Images" in step and step.get("Images") for step in steps):
                    with_images += 1
                    
            except json.JSONDecodeError:
                continue
    
    print(f"Total guides: {len(guides)}")
    print(f"Total steps: {total_steps} (avg {total_steps/len(guides):.1f} per guide)")
    print(f"Total tools: {total_tools} (avg {total_tools/len(guides):.1f} per guide)")
    print(f"Guides with images: {with_images} ({with_images/len(guides)*100:.1f}%)")
    
    print(f"\nSAMPLE TUTORIALS (first {max_samples}):")
    print("-" * 70)
    
    for i, guide in enumerate(guides[:max_samples], 1):
        # Use capital-first keys (MyFixit format)
        print(f"\n[{i}] {guide.get('Title', 'Untitled')}")
        print(f"    Guidid: {guide.get('Guidid', 'N/A')}")
        print(f"    Category: {guide.get('Category', 'N/A')}")
        print(f"    Steps: {len(guide.get('Steps', []))}")
        
        # Show tools
        toolbox = guide.get('Toolbox', [])
        if toolbox:
            tools = ', '.join([t.get('Name', '') for t in toolbox])[:80]
            print(f"    Tools: {tools}")
        
        # Show first step
        steps = guide.get('Steps', [])
        if steps:
            step = steps[0]
            print(f"    First step order: {step.get('Order', 'N/A')}")
            
            # Get instruction text
            lines = step.get('Lines', [])
            if lines:
                first_line = lines[0].get('Text', '')[:80]
                print(f"    Instruction: {first_line}...")
            
            # Check for images
            images = step.get('Images', [])
            if images:
                print(f"    Image: {images[0][:80]}...")

def main():
    """Preview MyFixit dataset"""
    print("\n" + "#"*70)
    print("# MyFixit Dataset Preview")
    print("# What will be ingested into the database")
    print("#"*70)
    
    # Priority categories for laptop repair
    priority_categories = ["PC.json", "Mac.json", "Computer Hardware.json"]
    
    for category in priority_categories:
        preview_category(category, max_samples=3)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("When you run ingest_myfixit.py, this data will be:")
    print("  1. Parsed from JSONL files")
    print("  2. Inserted into PostgreSQL (tutorials, tutorial_steps, tutorial_tools)")
    print("  3. Vectorized and inserted into Weaviate (Tutorial class)")
    print("\nExpected database content after ingestion:")
    print("  - PC: ~3,592 tutorials")
    print("  - Mac: ~2,224 tutorials")
    print("  - Computer Hardware: ~515 tutorials")
    print("  - TOTAL: ~6,331 tutorials (priority categories only)")
    print("\nTo ingest all categories, uncomment the loop in ingest_myfixit.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
