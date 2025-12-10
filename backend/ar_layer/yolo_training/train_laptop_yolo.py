"""
YOLOv8 Training Script for Laptop Component Detection

This script trains a custom YOLOv8 model to detect laptop components
for AR-guided repair tutorials.

Usage:
    python train_laptop_yolo.py --epochs 100 --batch 16 --imgsz 640
"""

from ultralytics import YOLO
import argparse
import yaml
from pathlib import Path
import torch
import os

def setup_directories():
    """Create necessary directories for training"""
    dirs = [
        'datasets/laptop_components/images/train',
        'datasets/laptop_components/images/val',
        'datasets/laptop_components/images/test',
        'datasets/laptop_components/labels/train',
        'datasets/laptop_components/labels/val',
        'datasets/laptop_components/labels/test',
        'runs/detect/laptop_v1',
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")

def check_dataset_stats(data_yaml_path):
    """Check dataset statistics before training"""
    with open(data_yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    train_dir = Path(config['path']) / config['train']
    val_dir = Path(config['path']) / config['val']
    
    train_images = list(train_dir.glob('*.jpg')) + list(train_dir.glob('*.png'))
    val_images = list(val_dir.glob('*.jpg')) + list(val_dir.glob('*.png'))
    
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)
    print(f"Training images:   {len(train_images)}")
    print(f"Validation images: {len(val_images)}")
    print(f"Total images:      {len(train_images) + len(val_images)}")
    print(f"Number of classes: {config['nc']}")
    print(f"Class names:       {', '.join(config['names'].values())}")
    print("="*60 + "\n")
    
    if len(train_images) == 0:
        raise ValueError("No training images found! Please run data collection script first.")
    
    if len(val_images) == 0:
        raise ValueError("No validation images found!")
    
    return len(train_images), len(val_images)

def train_yolo_model(
    data_yaml: str,
    epochs: int = 100,
    batch: int = 16,
    imgsz: int = 640,
    pretrained: str = 'yolov8n.pt',
    device: str = 'auto'
):
    """
    Train YOLOv8 model for laptop component detection
    
    Args:
        data_yaml: Path to dataset YAML config
        epochs: Number of training epochs
        batch: Batch size
        imgsz: Image size for training
        pretrained: Pretrained weights (yolov8n.pt, yolov8s.pt, yolov8m.pt)
        device: Device to use (auto, cpu, 0, 0,1,2,3)
    """
    
    print("\n" + "="*60)
    print("YOLO LAPTOP COMPONENT DETECTOR - TRAINING")
    print("="*60)
    print(f"Pretrained model: {pretrained}")
    print(f"Epochs:          {epochs}")
    print(f"Batch size:      {batch}")
    print(f"Image size:      {imgsz}")
    print(f"Device:          {device}")
    print("="*60 + "\n")
    
    # Check if CUDA is available
    if device == 'auto':
        device = '0' if torch.cuda.is_available() else 'cpu'
        print(f"Auto-detected device: {device}")
        if device == 'cpu':
            print("⚠️  WARNING: Training on CPU will be VERY slow!")
            print("   Consider using Google Colab (free GPU) or cloud GPU")
    
    # Load pretrained model
    model = YOLO(pretrained)
    
    # Check dataset
    train_count, val_count = check_dataset_stats(data_yaml)
    
    # Recommended settings based on dataset size
    if train_count < 500:
        print("⚠️  WARNING: Dataset is small (<500 images)")
        print("   Recommended: Collect more data or use heavy augmentation")
    
    # Train the model
    print("\n🚀 Starting training...\n")
    
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        patience=20,  # Early stopping patience
        save=True,
        save_period=10,  # Save checkpoint every 10 epochs
        cache=False,  # Don't cache images (to save RAM)
        workers=4,
        project='runs/detect',
        name='laptop_v1',
        exist_ok=True,
        pretrained=True,
        optimizer='AdamW',
        lr0=0.001,  # Initial learning rate
        lrf=0.01,   # Final learning rate (lr0 * lrf)
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=7.5,       # Box loss gain
        cls=0.5,       # Class loss gain
        dfl=1.5,       # Distribution focal loss gain
        hsv_h=0.015,   # HSV hue augmentation
        hsv_s=0.7,     # HSV saturation augmentation
        hsv_v=0.4,     # HSV value augmentation
        degrees=10.0,  # Rotation augmentation
        translate=0.1, # Translation augmentation
        scale=0.5,     # Scale augmentation
        shear=0.0,     # Shear augmentation
        perspective=0.0,  # Perspective augmentation
        flipud=0.0,    # Flip up-down probability
        fliplr=0.5,    # Flip left-right probability
        mosaic=1.0,    # Mosaic augmentation probability
        mixup=0.1,     # Mixup augmentation probability
        copy_paste=0.1, # Copy-paste augmentation probability
    )
    
    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE!")
    print("="*60)
    print(f"Best weights:  runs/detect/laptop_v1/weights/best.pt")
    print(f"Last weights:  runs/detect/laptop_v1/weights/last.pt")
    print(f"Metrics:       runs/detect/laptop_v1/results.csv")
    print(f"Plots:         runs/detect/laptop_v1/*.png")
    print("="*60 + "\n")
    
    # Validate the model
    print("🔍 Running validation...\n")
    metrics = model.val()
    
    print("\n" + "="*60)
    print("VALIDATION METRICS")
    print("="*60)
    print(f"mAP50:     {metrics.box.map50:.4f}")
    print(f"mAP50-95:  {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall:    {metrics.box.mr:.4f}")
    print("="*60 + "\n")
    
    return results, metrics

def export_model(weights_path: str, formats: list = ['onnx', 'torchscript']):
    """Export trained model to different formats for deployment"""
    print("\n📦 Exporting model...\n")
    
    model = YOLO(weights_path)
    
    for fmt in formats:
        print(f"Exporting to {fmt}...")
        model.export(format=fmt, imgsz=640)
    
    print("\n✅ Export complete!\n")

def main():
    parser = argparse.ArgumentParser(description='Train YOLOv8 for laptop component detection')
    parser.add_argument('--data', type=str, default='ar_layer/yolo_training/laptop_classes.yaml',
                        help='Path to dataset YAML file')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size (reduce if out of memory)')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='Image size for training')
    parser.add_argument('--weights', type=str, default='yolov8n.pt',
                        help='Pretrained weights (yolov8n.pt, yolov8s.pt, yolov8m.pt)')
    parser.add_argument('--device', type=str, default='auto',
                        help='Device to use (auto, cpu, 0, 0,1,2,3)')
    parser.add_argument('--setup-only', action='store_true',
                        help='Only setup directories without training')
    parser.add_argument('--export', action='store_true',
                        help='Export model after training')
    
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    if args.setup_only:
        print("✅ Setup complete! Ready for data collection.")
        return
    
    # Train model
    results, metrics = train_yolo_model(
        data_yaml=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        pretrained=args.weights,
        device=args.device
    )
    
    # Export if requested
    if args.export:
        export_model('runs/detect/laptop_v1/weights/best.pt')
    
    print("\n🎉 All done! Model ready for AR deployment.")
    print("\n📝 Next steps:")
    print("   1. Test the model: python test_laptop_yolo.py")
    print("   2. Deploy to AR system: Copy best.pt to models/laptop_yolo_v8.pt")
    print("   3. Update component_detector.py to use the new model")

if __name__ == '__main__':
    main()
