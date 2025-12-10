"""
Data Collection Pipeline for Laptop Component Detection

This script collects and prepares training data from multiple sources:
1. iFixit repair guide images (via API)
2. YouTube video frames (from ingested videos)
3. OEM service manual PDFs (extract images)
4. Manual uploads (user-provided images)

Usage:
    python collect_laptop_data.py --source ifixit --limit 1000
    python collect_laptop_data.py --source youtube --limit 500
    python collect_laptop_data.py --source manual --input ./my_laptop_photos/
"""

import argparse
import requests
import cv2
import numpy as np
from pathlib import Path
import json
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class LaptopDataCollector:
    """Collects and organizes laptop component images for YOLO training"""
    
    def __init__(self, output_dir: str = 'datasets/laptop_components'):
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / 'images' / 'raw'
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.output_dir / 'collection_metadata.json'
        self.metadata = self._load_metadata()
        
        print(f"📁 Output directory: {self.output_dir}")
        print(f"📸 Images will be saved to: {self.images_dir}")
    
    def _load_metadata(self) -> Dict:
        """Load existing metadata or create new"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            'total_images': 0,
            'sources': {},
            'brands': {},
            'collection_log': []
        }
    
    def _save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, indent=2, fp=f)
    
    def collect_from_ifixit(self, limit: int = 1000):
        """
        Collect laptop repair images from iFixit API
        
        iFixit provides high-quality annotated repair images
        """
        print("\n🔧 Collecting from iFixit...")
        
        # Search for laptop guides
        base_url = "https://www.ifixit.com/api/2.0"
        
        # Get laptop categories
        laptops = [
            'Dell', 'HP', 'Lenovo', 'Asus', 'Acer', 'Apple MacBook',
            'MSI', 'Razer', 'ThinkPad', 'Chromebook'
        ]
        
        collected = 0
        
        for brand in laptops:
            if collected >= limit:
                break
            
            print(f"\n  Searching: {brand} laptops...")
            
            try:
                # Search guides
                response = requests.get(
                    f"{base_url}/wikis/CATEGORY/{brand}",
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"  ⚠️  API error for {brand}: {response.status_code}")
                    continue
                
                data = response.json()
                
                # Process each guide
                for guide in data.get('guides', [])[:50]:  # Limit per brand
                    if collected >= limit:
                        break
                    
                    guide_id = guide.get('guideid')
                    title = guide.get('title', 'Unknown')
                    
                    print(f"    Processing: {title[:50]}...")
                    
                    # Get guide details
                    guide_response = requests.get(
                        f"{base_url}/guides/{guide_id}",
                        timeout=10
                    )
                    
                    if guide_response.status_code != 200:
                        continue
                    
                    guide_data = guide_response.json()
                    
                    # Download images from steps
                    for step in guide_data.get('steps', []):
                        for media in step.get('media', {}).get('data', []):
                            if collected >= limit:
                                break
                            
                            image_url = media.get('image', {}).get('standard')
                            if not image_url:
                                continue
                            
                            # Download image
                            self._download_image(
                                image_url,
                                source='ifixit',
                                brand=brand,
                                guide_title=title,
                                step_number=step.get('orderby', 0)
                            )
                            
                            collected += 1
                            
                            if collected % 10 == 0:
                                print(f"    ✓ Collected: {collected}/{limit}")
            
            except Exception as e:
                print(f"  ⚠️  Error processing {brand}: {e}")
                continue
        
        print(f"\n✅ iFixit collection complete: {collected} images")
        self._save_metadata()
    
    def collect_from_youtube_frames(self, limit: int = 500):
        """
        Extract frames from YouTube repair videos already in database
        
        Uses videos from data_sources/youtube/ that were ingested
        """
        print("\n🎥 Collecting from YouTube video frames...")
        
        youtube_dir = Path('data_sources/youtube')
        if not youtube_dir.exists():
            print("  ⚠️  No YouTube videos found in data_sources/youtube/")
            return
        
        video_files = list(youtube_dir.glob('*.mp4'))
        print(f"  Found {len(video_files)} videos")
        
        collected = 0
        frames_per_video = limit // max(len(video_files), 1)
        
        for video_path in video_files:
            if collected >= limit:
                break
            
            print(f"\n  Processing: {video_path.name}...")
            
            cap = cv2.VideoCapture(str(video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Extract frames at regular intervals
            interval = max(total_frames // frames_per_video, 1)
            
            frame_count = 0
            while collected < limit:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % interval == 0:
                    # Save frame
                    filename = f"youtube_{video_path.stem}_frame_{frame_count:06d}.jpg"
                    output_path = self.images_dir / filename
                    cv2.imwrite(str(output_path), frame)
                    
                    collected += 1
                    
                    if collected % 50 == 0:
                        print(f"    ✓ Extracted: {collected}/{limit} frames")
                
                frame_count += 1
            
            cap.release()
        
        print(f"\n✅ YouTube extraction complete: {collected} frames")
        self._save_metadata()
    
    def collect_from_manual_upload(self, input_dir: str):
        """
        Process manually uploaded laptop photos
        
        User provides their own laptop disassembly photos
        """
        print("\n📤 Processing manual uploads...")
        
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"  ⚠️  Input directory not found: {input_dir}")
            return
        
        # Supported image formats
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
            image_files.extend(input_path.glob(ext))
            image_files.extend(input_path.glob(ext.upper()))
        
        print(f"  Found {len(image_files)} images")
        
        collected = 0
        for img_path in image_files:
            # Copy image to dataset
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            
            # Resize if too large
            h, w = img.shape[:2]
            if max(h, w) > 1920:
                scale = 1920 / max(h, w)
                img = cv2.resize(img, (int(w*scale), int(h*scale)))
            
            # Save to dataset
            filename = f"manual_{img_path.stem}.jpg"
            output_path = self.images_dir / filename
            cv2.imwrite(str(output_path), img)
            
            collected += 1
            
            if collected % 10 == 0:
                print(f"    ✓ Processed: {collected}/{len(image_files)}")
        
        print(f"\n✅ Manual upload complete: {collected} images")
        self._save_metadata()
    
    def _download_image(self, url: str, source: str, brand: str, **metadata):
        """Download and save image with metadata"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return
            
            # Convert to numpy array
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                return
            
            # Generate filename
            filename = f"{source}_{brand}_{self.metadata['total_images']:06d}.jpg"
            output_path = self.images_dir / filename
            
            # Save image
            cv2.imwrite(str(output_path), img)
            
            # Update metadata
            self.metadata['total_images'] += 1
            self.metadata['sources'][source] = self.metadata['sources'].get(source, 0) + 1
            self.metadata['brands'][brand] = self.metadata['brands'].get(brand, 0) + 1
            
        except Exception as e:
            print(f"    ⚠️  Download failed: {e}")
    
    def show_statistics(self):
        """Display collection statistics"""
        print("\n" + "="*60)
        print("DATASET STATISTICS")
        print("="*60)
        print(f"Total images: {self.metadata['total_images']}")
        print(f"\nBy source:")
        for source, count in self.metadata['sources'].items():
            print(f"  {source:15s}: {count:5d} images")
        print(f"\nBy brand:")
        for brand, count in sorted(self.metadata['brands'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {brand:15s}: {count:5d} images")
        print("="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(description='Collect laptop images for YOLO training')
    parser.add_argument('--source', type=str, required=True,
                        choices=['ifixit', 'youtube', 'manual', 'all'],
                        help='Data source to collect from')
    parser.add_argument('--limit', type=int, default=1000,
                        help='Maximum number of images to collect')
    parser.add_argument('--input', type=str,
                        help='Input directory for manual uploads')
    parser.add_argument('--output', type=str, default='datasets/laptop_components',
                        help='Output directory for dataset')
    
    args = parser.parse_args()
    
    collector = LaptopDataCollector(output_dir=args.output)
    
    if args.source == 'ifixit' or args.source == 'all':
        collector.collect_from_ifixit(limit=args.limit)
    
    if args.source == 'youtube' or args.source == 'all':
        collector.collect_from_youtube_frames(limit=args.limit)
    
    if args.source == 'manual':
        if not args.input:
            print("Error: --input required for manual uploads")
            return
        collector.collect_from_manual_upload(args.input)
    
    # Show final statistics
    collector.show_statistics()
    
    print("\n📝 Next steps:")
    print("   1. Annotate images: python annotate_laptop_data.py")
    print("   2. Split dataset: python split_dataset.py --train 0.8 --val 0.15 --test 0.05")
    print("   3. Train model: python train_laptop_yolo.py --epochs 100")

if __name__ == '__main__':
    main()
