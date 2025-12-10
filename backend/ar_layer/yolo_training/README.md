# YOLO Training Pipeline for Laptop Component Detection

This directory contains the complete pipeline for training a YOLOv8 model to detect laptop components for AR-guided repairs.

## 📋 Training Strategy

### 1. **Data Collection** (Target: 5000+ images)

**Sources:**
- ✅ iFixit API (high-quality repair images)
- ✅ YouTube videos (extract frames from repair tutorials)
- ✅ Manual uploads (your own laptop photos)
- ⏳ OEM manuals (PDF image extraction - coming soon)

**Component Classes (15 total):**
- **Critical**: Screws (Phillips, Torx, Flathead), Battery, Power connector, Bottom panel
- **High**: SSD, HDD, Cooling fan, Heat sink, Display connector
- **Medium**: RAM slot/module, Keyboard, Touchpad

### 2. **Annotation Pipeline**

**Tools:**
- **SAM (Segment Anything Model)** - Auto-segmentation for initial annotations
- **Label Studio** - Web-based manual annotation/refinement
- **YOLO format export** - Automatic conversion

**Workflow:**
1. Auto-annotate with SAM → Get initial bounding boxes
2. Refine in Label Studio → Correct class labels
3. Export to YOLO format → Ready for training

### 3. **Training Configuration**

**Model:** YOLOv8n (Nano - fastest, good accuracy)
- Can upgrade to YOLOv8s/m/l/x for better accuracy

**Hyperparameters:**
- Epochs: 100 (with early stopping patience=20)
- Batch size: 16 (adjust based on GPU memory)
- Image size: 640x640
- Optimizer: AdamW
- Learning rate: 0.001 → 0.00001 (cosine decay)

**Augmentation:**
- HSV: Hue ±1.5%, Saturation ±70%, Value ±40%
- Geometric: Rotation ±10°, Translation ±10%, Scale ±50%
- Mosaic: 100% probability
- Mixup: 10% probability
- Copy-paste: 10% probability
- Flip left-right: 50%

### 4. **Evaluation Metrics**

**Target Performance:**
- mAP50: > 0.85 (mean Average Precision at IoU 0.5)
- mAP50-95: > 0.70 (mean across IoU 0.5 to 0.95)
- Precision: > 0.80
- Recall: > 0.75

**Per-Class Requirements:**
- Critical components (screws, battery): > 0.90 precision
- High priority (SSD, fan): > 0.85 precision
- Medium priority (RAM, keyboard): > 0.75 precision

## 🚀 Quick Start Guide

### Step 1: Setup Environment

```bash
# Install dependencies
cd backend
pip install ultralytics opencv-python pillow requests

# Optional: Install SAM for auto-annotation
pip install segment-anything
pip install label-studio

# Setup directories
cd ar_layer/yolo_training
python train_laptop_yolo.py --setup-only
```

### Step 2: Collect Training Data

```bash
# Collect from iFixit (1000 images)
python collect_laptop_data.py --source ifixit --limit 1000

# Extract from YouTube videos (500 frames)
python collect_laptop_data.py --source youtube --limit 500

# Add your own photos
python collect_laptop_data.py --source manual --input /path/to/your/photos

# Or collect from all sources
python collect_laptop_data.py --source all --limit 5000
```

### Step 3: Annotate Data

**Option A: Quick annotation with SAM (recommended)**
```bash
# Auto-annotate with SAM
python annotate_laptop_data.py --mode auto \
  --input datasets/laptop_components/images/raw \
  --output datasets/laptop_components/labels/raw

# Then refine in Label Studio
python annotate_laptop_data.py --mode label-studio --port 8080
# Open http://localhost:8080 in browser
```

**Option B: Manual annotation only**
```bash
# Launch Label Studio
python annotate_laptop_data.py --mode label-studio --port 8080

# Annotate all images manually
# Export as JSON when done

# Convert Label Studio export to YOLO format
python annotate_laptop_data.py --mode export \
  --export-file label_studio_export.json \
  --output datasets/laptop_components
```

### Step 4: Split Dataset

```bash
# Split into train/val/test (80%/15%/5%)
python split_dataset.py \
  --input datasets/laptop_components/labels/raw \
  --output datasets/laptop_components \
  --train 0.8 --val 0.15 --test 0.05
```

### Step 5: Train Model

```bash
# Start training (100 epochs, batch size 16)
python train_laptop_yolo.py \
  --data laptop_classes.yaml \
  --epochs 100 \
  --batch 16 \
  --weights yolov8n.pt \
  --device auto

# Training will automatically:
# - Use GPU if available (CUDA)
# - Save checkpoints every 10 epochs
# - Early stop if no improvement for 20 epochs
# - Generate training plots and metrics
```

**Training on CPU?** (SLOW - not recommended)
Use Google Colab for free GPU:
```bash
# Upload dataset to Google Drive
# Run training in Colab notebook
# Download trained model
```

### Step 6: Evaluate Model

```bash
# Validate on test set
python test_laptop_yolo.py \
  --weights runs/detect/laptop_v1/weights/best.pt \
  --data laptop_classes.yaml \
  --split test

# Test on sample images
python test_laptop_yolo.py \
  --weights runs/detect/laptop_v1/weights/best.pt \
  --source datasets/laptop_components/images/test

# Generate confusion matrix and per-class metrics
python test_laptop_yolo.py \
  --weights runs/detect/laptop_v1/weights/best.pt \
  --task confusion_matrix
```

### Step 7: Deploy to AR System

```bash
# Copy best model to AR detector
cp runs/detect/laptop_v1/weights/best.pt ../../models/laptop_yolo_v8.pt

# Update component_detector.py to use new model
# Restart backend server
```

## 📊 Expected Training Time

| Hardware | Batch Size | Time per Epoch | Total (100 epochs) |
|----------|------------|----------------|-------------------|
| RTX 3090 | 16 | ~2 min | ~3-4 hours |
| RTX 3060 | 16 | ~4 min | ~6-7 hours |
| GTX 1080 | 8 | ~6 min | ~10 hours |
| CPU | 4 | ~45 min | ~75 hours ❌ |

**Recommendation:** Use GPU. Google Colab offers free T4 GPU (~5 hours total).

## 📈 Monitoring Training

**TensorBoard:**
```bash
tensorboard --logdir runs/detect/laptop_v1
# Open http://localhost:6006
```

**Key metrics to watch:**
- `train/box_loss` - should decrease steadily
- `val/mAP50` - should increase and plateau
- `metrics/precision` - target > 0.80
- `metrics/recall` - target > 0.75

## 🔧 Troubleshooting

### Low mAP (<0.70)
- **Solution**: Collect more diverse data (different brands, lighting, angles)
- Increase epochs to 150-200
- Use larger model (yolov8s.pt or yolov8m.pt)

### High precision, low recall
- **Solution**: Lower confidence threshold in inference
- Add more augmentation (mosaic, mixup)
- Balance dataset (some classes may be underrepresented)

### Out of memory error
- **Solution**: Reduce batch size (16 → 8 → 4)
- Reduce image size (640 → 416)
- Use smaller model (yolov8n.pt)

### Model not detecting small screws
- **Solution**: Use higher resolution (640 → 1280)
- Add more screw examples in training data
- Increase box loss weight

## 🎯 Next Categories

After laptop training is successful:

1. **Phone** (next priority)
   - Classes: Screws, battery, camera, screen, charging port, SIM tray
   - Data sources: iFixit, JerryRigEverything videos

2. **Tablet**
   - Classes: Battery, screen, charging port, buttons
   - Similar to phone but larger components

3. **Router**
   - Classes: Antennas, power port, ethernet ports, case screws

4. **Printer**
   - Classes: Paper tray, ink cartridges, power cable, USB port

## 📚 Resources

- **YOLOv8 Docs**: https://docs.ultralytics.com
- **iFixit API**: https://www.ifixit.com/api/2.0/doc
- **SAM GitHub**: https://github.com/facebookresearch/segment-anything
- **Label Studio**: https://labelstud.io
- **YOLO Format**: https://roboflow.com/formats/yolov8-pytorch-txt

## ⚠️ Important Notes

1. **Class imbalance**: Ensure each class has at least 200+ examples
2. **Lighting variations**: Collect images in different lighting conditions
3. **Background diversity**: Include various backgrounds (desk, carpet, etc.)
4. **Occlusion**: Include partially visible components
5. **Multiple instances**: Include images with multiple screws/components
6. **Brand diversity**: Cover Dell, HP, Lenovo, Asus, Acer, etc.

## 📞 Support

If you encounter issues:
1. Check training logs in `runs/detect/laptop_v1/`
2. Review dataset statistics with `collect_laptop_data.py --stats`
3. Validate annotations with visualization tools
4. Post issues on GitHub with training metrics

---

**Status**: Ready for data collection  
**Next step**: Run `collect_laptop_data.py --source ifixit --limit 1000`
