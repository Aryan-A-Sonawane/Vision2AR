"""
Generate placeholder images for tutorial steps
"""
import cv2
import numpy as np
import os
from pathlib import Path

def create_placeholder_image(tutorial_id: int, step_number: int, width=640, height=480):
    """Create a placeholder image with tutorial and step info"""
    
    # Create output directory
    output_dir = Path(f"assets/tutorials/{tutorial_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create image with gradient background
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add gradient background
    for i in range(height):
        color_value = int(40 + (i / height) * 80)
        img[i, :] = [color_value, color_value, color_value]
    
    # Add text
    text_tutorial = f"Tutorial #{tutorial_id}"
    text_step = f"Step {step_number}"
    text_placeholder = "Placeholder Image"
    text_info = "Replace with actual device photo"
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Calculate text positions (centered)
    cv2.putText(img, text_tutorial, (width//2 - 120, height//2 - 60), 
                font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, text_step, (width//2 - 80, height//2 - 20), 
                font, 1.2, (100, 200, 255), 2, cv2.LINE_AA)
    cv2.putText(img, text_placeholder, (width//2 - 140, height//2 + 30), 
                font, 0.8, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(img, text_info, (width//2 - 180, height//2 + 70), 
                font, 0.6, (150, 150, 150), 1, cv2.LINE_AA)
    
    # Add some placeholder "component" boxes
    components = [
        {"name": "Screw", "pos": (150, 150), "size": (80, 80), "color": (0, 255, 0)},
        {"name": "Panel", "pos": (350, 200), "size": (150, 100), "color": (255, 200, 0)},
        {"name": "Connector", "pos": (200, 320), "size": (100, 60), "color": (255, 100, 200)},
    ]
    
    for comp in components:
        x, y = comp["pos"]
        w, h = comp["size"]
        color = comp["color"]
        
        # Draw rectangle
        cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
        
        # Draw label
        cv2.putText(img, comp["name"], (x, y-10), 
                    font, 0.5, color, 1, cv2.LINE_AA)
    
    # Save image
    output_path = output_dir / f"step_{step_number}.jpg"
    cv2.imwrite(str(output_path), img)
    print(f"✓ Created: {output_path}")
    
    return str(output_path)


def generate_tutorial_placeholders():
    """Generate placeholder images for common tutorial IDs"""
    
    # Common tutorial IDs from the system (adjust as needed)
    tutorial_ids = [42, 1, 2, 3, 4, 5]  # Tutorial 42 seems to be active
    
    for tutorial_id in tutorial_ids:
        print(f"\n📁 Generating placeholders for Tutorial {tutorial_id}...")
        
        # Generate 5 steps per tutorial
        for step in range(5):
            create_placeholder_image(tutorial_id, step)
    
    print("\n✅ All placeholder images generated successfully!")
    print(f"📂 Location: backend/assets/tutorials/")
    print("\n💡 To use real images:")
    print("   1. Take photos of actual device repair steps")
    print("   2. Replace placeholder images in assets/tutorials/{id}/")
    print("   3. Ensure images are 640x480 or higher resolution")


if __name__ == "__main__":
    generate_tutorial_placeholders()
