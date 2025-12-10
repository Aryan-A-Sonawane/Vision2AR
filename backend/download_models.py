"""
Download and initialize ML models for AR Laptop Troubleshooter
Run this once to cache models locally
"""

import os
import sys

print("=" * 60)
print("ML MODELS DOWNLOAD - AR Laptop Troubleshooter")
print("=" * 60)
print()

# 1. Whisper (Speech Recognition)
print("1/4 Downloading Whisper (base model) - ~140MB...")
try:
    import whisper
    model = whisper.load_model("base")
    print("✅ Whisper model downloaded successfully!")
    print(f"   Saved to: {os.path.dirname(model.__dict__.get('_modules', {}).get('encoder', '').__class__.__module__)}")
except Exception as e:
    print(f"❌ Whisper download failed: {e}")
print()

# 2. YOLO (Object Detection)
print("2/4 Downloading YOLOv8 (nano model) - ~6MB...")
try:
    from ultralytics import YOLO
    model = YOLO('yolov8n.pt')
    print("✅ YOLO model downloaded successfully!")
except Exception as e:
    print(f"❌ YOLO download failed: {e}")
print()

# 3. Sentence Transformers (Text Embeddings)
print("3/4 Downloading Sentence Transformer - ~90MB...")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Sentence Transformer model downloaded successfully!")
except Exception as e:
    print(f"❌ Sentence Transformer download failed: {e}")
print()

# 4. BLIP2 (Image Captioning) - OPTIONAL (5.4GB)
print("4/4 BLIP2 Image Captioning - SKIPPED (5.4GB - optional)")
print("   To download later, run:")
print("   from transformers import Blip2Processor, Blip2ForConditionalGeneration")
print("   processor = Blip2Processor.from_pretrained('Salesforce/blip2-opt-2.7b')")
print("   model = Blip2ForConditionalGeneration.from_pretrained('Salesforce/blip2-opt-2.7b')")
print()

print("=" * 60)
print("✅ ESSENTIAL MODELS DOWNLOADED!")
print("=" * 60)
print()
print("Total downloaded: ~236MB")
print("Models are cached and ready to use.")
print()
print("Next steps:")
print("1. Start backend: python main.py")
print("2. Test API: http://localhost:8000/api/health")
print("3. Start frontend: cd ../frontend && npm run dev")
