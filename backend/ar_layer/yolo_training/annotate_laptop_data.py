"""
Semi-Automatic Annotation Tool using SAM (Segment Anything Model)

This tool helps annotate laptop components faster using:
1. SAM for automatic segmentation
2. Manual refinement via Label Studio
3. Export to YOLO format

Usage:
    # Auto-annotate with SAM
    python annotate_laptop_data.py --mode auto --input datasets/laptop_components/images/raw
    
    # Launch Label Studio for manual refinement
    python annotate_laptop_data.py --mode label-studio --port 8080
    
    # Export to YOLO format
    python annotate_laptop_data.py --mode export --output datasets/laptop_components
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
import json
from typing import List, Tuple
import torch

class LaptopAnnotator:
    """Semi-automatic annotation tool for laptop components"""
    
    def __init__(self):
        self.sam_available = False
        try:
            # Try to import SAM
            from segment_anything import sam_model_registry, SamPredictor
            self.sam_available = True
            print("✓ SAM (Segment Anything Model) available")
        except ImportError:
            print("⚠️  SAM not installed. Auto-annotation will be limited.")
            print("   Install: pip install segment-anything")
    
    def auto_annotate_with_sam(self, image_dir: str, output_dir: str):
        """
        Use SAM to automatically detect and segment components
        
        This provides initial annotations that can be refined manually
        """
        if not self.sam_available:
            print("SAM not available. Skipping auto-annotation.")
            return
        
        print("\n🤖 Auto-annotating with SAM...")
        
        from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
        
        # Load SAM model
        sam_checkpoint = "sam_vit_h_4b8939.pth"
        if not Path(sam_checkpoint).exists():
            print(f"⚠️  SAM checkpoint not found: {sam_checkpoint}")
            print("   Download from: https://github.com/facebookresearch/segment-anything")
            return
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        sam = sam_model_registry["vit_h"](checkpoint=sam_checkpoint)
        sam.to(device=device)
        
        mask_generator = SamAutomaticMaskGenerator(sam)
        
        # Process each image
        image_path = Path(image_dir)
        image_files = list(image_path.glob('*.jpg')) + list(image_path.glob('*.png'))
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Found {len(image_files)} images to annotate")
        
        for i, img_file in enumerate(image_files):
            print(f"  Processing {i+1}/{len(image_files)}: {img_file.name}")
            
            # Load image
            image = cv2.imread(str(img_file))
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Generate masks
            masks = mask_generator.generate(image_rgb)
            
            # Convert masks to YOLO format (bounding boxes)
            annotations = self._masks_to_yolo(masks, image.shape)
            
            # Save annotations
            label_file = output_path / f"{img_file.stem}.txt"
            with open(label_file, 'w') as f:
                for ann in annotations:
                    f.write(' '.join(map(str, ann)) + '\n')
            
            if (i + 1) % 10 == 0:
                print(f"    ✓ Annotated: {i+1}/{len(image_files)}")
        
        print(f"\n✅ Auto-annotation complete!")
        print(f"   Annotations saved to: {output_dir}")
        print(f"\n⚠️  IMPORTANT: Review and correct class labels manually")
    
    def _masks_to_yolo(self, masks: List[dict], image_shape: Tuple[int, int, int]) -> List:
        """Convert SAM masks to YOLO bounding box format"""
        h, w = image_shape[:2]
        annotations = []
        
        for mask in masks:
            # Get bounding box from mask
            segmentation = mask['segmentation']
            y_indices, x_indices = np.where(segmentation)
            
            if len(x_indices) == 0:
                continue
            
            x_min = x_indices.min()
            x_max = x_indices.max()
            y_min = y_indices.min()
            y_max = y_indices.max()
            
            # Convert to YOLO format (normalized)
            x_center = ((x_min + x_max) / 2) / w
            y_center = ((y_min + y_max) / 2) / h
            bbox_w = (x_max - x_min) / w
            bbox_h = (y_max - y_min) / h
            
            # Assign class 0 by default (needs manual correction)
            class_id = 0
            
            # Filter very small or very large boxes
            if bbox_w > 0.01 and bbox_h > 0.01 and bbox_w < 0.95 and bbox_h < 0.95:
                annotations.append([class_id, x_center, y_center, bbox_w, bbox_h])
        
        return annotations
    
    def launch_label_studio(self, port: int = 8080):
        """
        Launch Label Studio for manual annotation/refinement
        
        Label Studio provides a web UI for labeling images
        """
        print("\n🎨 Launching Label Studio...")
        print(f"   URL: http://localhost:{port}")
        print("\n📝 Instructions:")
        print("   1. Create a new project")
        print("   2. Import images from datasets/laptop_components/images/raw")
        print("   3. Configure labels from laptop_classes.yaml")
        print("   4. Start annotating!")
        print("   5. Export as YOLO format when done")
        print("\nPress Ctrl+C to stop Label Studio\n")
        
        import subprocess
        try:
            subprocess.run(['label-studio', 'start', '--port', str(port)])
        except FileNotFoundError:
            print("⚠️  Label Studio not installed")
            print("   Install: pip install label-studio")
        except KeyboardInterrupt:
            print("\n\n✓ Label Studio stopped")
    
    def export_to_yolo(self, label_studio_export: str, output_dir: str):
        """
        Convert Label Studio export to YOLO format
        
        Args:
            label_studio_export: JSON file from Label Studio
            output_dir: Output directory for YOLO dataset
        """
        print("\n📦 Exporting to YOLO format...")
        
        with open(label_studio_export, 'r') as f:
            data = json.load(f)
        
        output_path = Path(output_dir)
        images_dir = output_path / 'images'
        labels_dir = output_path / 'labels'
        
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        for item in data:
            # Extract image and annotations
            image_url = item['data']['image']
            annotations = item['annotations'][0]['result']
            
            # Get image filename
            filename = Path(image_url).stem
            
            # Convert annotations to YOLO format
            yolo_annotations = []
            for ann in annotations:
                if ann['type'] != 'rectanglelabels':
                    continue
                
                # Get class ID from label
                label = ann['value']['rectanglelabels'][0]
                class_id = self._get_class_id(label)
                
                # Get normalized coordinates
                x = ann['value']['x'] / 100
                y = ann['value']['y'] / 100
                w = ann['value']['width'] / 100
                h = ann['value']['height'] / 100
                
                # Convert to YOLO format (center coordinates)
                x_center = x + w / 2
                y_center = y + h / 2
                
                yolo_annotations.append([class_id, x_center, y_center, w, h])
            
            # Save annotations
            label_file = labels_dir / f"{filename}.txt"
            with open(label_file, 'w') as f:
                for ann in yolo_annotations:
                    f.write(' '.join(map(str, ann)) + '\n')
        
        print(f"✅ Export complete!")
        print(f"   Images: {images_dir}")
        print(f"   Labels: {labels_dir}")
    
    def _get_class_id(self, label: str) -> int:
        """Map label name to class ID"""
        class_names = [
            'screw_phillips', 'screw_torx', 'screw_flathead',
            'battery', 'ram_slot', 'ram_module', 'ssd', 'hdd',
            'cooling_fan', 'heat_sink', 'connector_power',
            'connector_display', 'bottom_panel', 'keyboard', 'touchpad'
        ]
        
        try:
            return class_names.index(label)
        except ValueError:
            return 0  # Default to first class

def main():
    parser = argparse.ArgumentParser(description='Annotate laptop component images')
    parser.add_argument('--mode', type=str, required=True,
                        choices=['auto', 'label-studio', 'export'],
                        help='Annotation mode')
    parser.add_argument('--input', type=str,
                        help='Input directory with images (for auto mode)')
    parser.add_argument('--output', type=str,
                        help='Output directory for annotations')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port for Label Studio (default: 8080)')
    parser.add_argument('--export-file', type=str,
                        help='Label Studio export JSON file')
    
    args = parser.parse_args()
    
    annotator = LaptopAnnotator()
    
    if args.mode == 'auto':
        if not args.input or not args.output:
            print("Error: --input and --output required for auto mode")
            return
        annotator.auto_annotate_with_sam(args.input, args.output)
    
    elif args.mode == 'label-studio':
        annotator.launch_label_studio(port=args.port)
    
    elif args.mode == 'export':
        if not args.export_file or not args.output:
            print("Error: --export-file and --output required for export mode")
            return
        annotator.export_to_yolo(args.export_file, args.output)
    
    print("\n✅ Done!")

if __name__ == '__main__':
    main()
