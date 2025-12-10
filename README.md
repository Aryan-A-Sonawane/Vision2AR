# AR Laptop Troubleshooter

A web-based diagnostic and repair assistant that uses adaptive questioning and AR-guided overlays to help users fix laptop problems safely.

## Features

- **Adaptive Diagnosis**: Dynamic follow-up questions with belief vector tracking
- **Multi-Source Tutorials**: Merges OEM manuals, iFixit guides, and YouTube tutorials
- **AR Overlays**: WebXR-based visual guidance tied to device components
- **Voice Guidance**: Browser-based TTS for hands-free assistance
- **Safety First**: Risk classification and warnings for all repair steps

## Tech Stack

### Frontend
- Next.js + Tailwind CSS
- WebXR API (browser-based AR)
- Speech Synthesis API (TTS)

### Backend
- Python FastAPI
- PostgreSQL (procedural tutorials)
- Vector DB (symptom embeddings)

### ML Models
- Whisper (speech-to-text)
- YOLOv8 / SAM (object detection)
- BLIP2 / LLaVA (vision + language)
- XGBoost (diagnosis classifier)

## Project Structure

```
arvr/
├── assets/                    # Device images with AR overlay anchors
│   ├── lenovo/
│   │   └── ideapad_5/        # Product-specific images
│   ├── dell/
│   │   └── xps_15/
│   └── hp/
│       └── pavilion/
├── manuals/                   # OEM service manuals (PDFs)
│   ├── lenovo/
│   ├── dell/
│   └── hp/
├── backend/
│   ├── diagnosis/            # Belief vector engine + question generator
│   ├── tutorial/             # Step merger + source resolver
│   └── ar_layer/             # Overlay generator + bounding box logic
├── frontend/
│   ├── components/           # WebXR viewer + step controls
│   └── pages/                # Next.js routes
└── .github/
    └── copilot-instructions.md  # AI agent guidelines
```

## Getting Started

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- PostgreSQL 14+
- Vector DB (Pinecone/Weaviate/Qdrant)

### Setup

1. **Add device assets:**
   ```
   assets/{brand}/{product}/image_name.jpg
   ```
   Example: `assets/lenovo/ideapad_5/bottom_cover_screws.jpg`

2. **Add OEM manuals:**
   ```
   manuals/{brand}/service_manual.pdf
   ```
   Example: `manuals/lenovo/ideapad_5_service_guide.pdf`

3. **Install dependencies:**
   ```bash
   # Frontend
   cd frontend
   npm install

   # Backend
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure database:**
   - Create PostgreSQL database: `ar_laptop_repair`
   - Initialize vector DB for symptom embeddings
   - Load seed data (repair procedures)

5. **Run development servers:**
   ```bash
   # Backend
   cd backend
   uvicorn main:app --reload

   # Frontend
   cd frontend
   npm run dev
   ```

## How It Works

### 1. Diagnosis Phase
- User describes problem (text/image/video)
- System embeds input → queries vector DB
- Presents top 3 probable causes
- Asks binary follow-up questions:
  - "Does CapsLock LED toggle?"
  - "Do you hear fan spin for 2 seconds?"
- Updates belief vector after each answer
- Stops when confidence ≥ 0.6

### 2. Repair Phase
- Loads OEM tutorial as canonical sequence
- Enhances with iFixit details (screw types, tools)
- Adds YouTube visual anchors
- Displays AR overlay:
  - Highlights target component
  - Shows text instruction
  - Plays TTS voice guidance
- User controls: Next | Previous | Repeat | Manual View

### 3. Safety Rules
- **OEM manuals first** (warranty-safe)
- **iFixit when** OEM lacks clarity
- **YouTube when** visuals needed (with validation)
- **Never** show conflicting methods simultaneously
- **Abort** high-risk YouTube-only tutorials

## Contributing

See `.github/copilot-instructions.md` for AI agent guidelines and architectural patterns.

## License

TBD
